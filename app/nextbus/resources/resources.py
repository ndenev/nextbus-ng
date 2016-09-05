from flask_restful import reqparse, Resource
from flask import g, request, current_app
from socket import gethostname
from datetime import datetime
import calendar

import json
import time

from nextbus.common.nextbusapi import NextbusApiError
from nextbus.resources.exceptions import ResourceNotFound

CACHE_TTL = 30
SLOW_THRESH = 2.0
SLOW_LOG_SIZE = 50


def teardown_request(exception=None):
    """ We are logging slow queries here. """
    request_time = time.time() - g.start
    if request_time > SLOW_THRESH:
        current_app.logger.info("logging slow request {} time: {}".format(
                                                          request.url_rule,
                                                          request_time))
        current_app.stats_redis.zadd('slowlog',
                             json.dumps({'time': time.time(),
                                         'path': request.path,
                                         'method': request.method,
                                         'args': request.args.to_dict(),
                                         'remote_host': request.remote_addr,
                                         'api_host': gethostname()}),
                             request_time)

        r = current_app.stats_redis.zremrangebyrank('slowlog', 0, -(SLOW_LOG_SIZE + 1))

        if r > 0:
            current_app.logger.info("trimming off {} slowlog entries".format(r))


class NextbusApiResource(Resource):
    _display_name = None

    def counter(self):
        g.start = time.time()
        current_app.stats_redis.incr(self._display_name)


class ApiStats(NextbusApiResource):
    _display_name = "stats"

    def get(self):
        self.counter()
        ids = [k._display_name for k in NextbusApiResource.__subclasses__()
               if k._display_name is not None]
        hits = current_app.stats_redis.mget(ids)
        return {'stats': {k: int(v) if v else 0 for k, v in zip(ids, hits)}}, 200


class ApiSlowLog(NextbusApiResource):
    _display_name = "stats_slowlog"

    def get(self):
        self.counter()
        slowlog = []
        for rj, rt in current_app.stats_redis.zrevrange('slowlog', 0,
                                                SLOW_LOG_SIZE - 1,
                                                withscores=True):
            rd = json.loads(rj)
            rd.update({'request_time': rt})
            slowlog.append(rd)
        return {'slowlog': slowlog}, 200


class ApiRoot(NextbusApiResource):
    _display_name = "root"

    def get(self):
        self.counter()
        names = [k._display_name for k in NextbusApiResource.__subclasses__()
                 if k._display_name]
        return {'resources': names}


class Agency(NextbusApiResource):
    _stat_name = "agency_list"

    def get(self):
        self.counter()
        current_app.logger.debug("getting agency list")
        agencies = current_app.nextbus_api.agency_list()
        if agencies is None:
            raise ResourceNotFound
        return agencies, 200


class Routes(NextbusApiResource):
    _display_name = "routes_list"

    def get(self):
        self.counter()
        routes = current_app.nextbus_api.route_list()
        if routes is None:
            raise ResourceNotFound
        return routes, 200


class RouteSchedule(NextbusApiResource):
    _display_name = "routes_schedule"

    def get(self, tag=None):
        self.counter()
        try:
            schedule = current_app.nextbus_api.route_schedule(tag)
            return {'schedule': schedule}, 200
        except NextbusApiError as e:
            return {'error': e.message}, 400


class NotInService(NextbusApiResource):
    _display_name = "not_in_service"

    @staticmethod
    def _get_serviceclass(dt):
        weekday = dt.weekday()
        if 0 <= weekday <= 4:
            return "wkd"
        elif weekday == 5:
            return "sat"
        else:
            return "sun"

    @staticmethod
    def _find_first_bus_in_schedule(schedule):
        blocks = schedule.get('block')
        for stop in blocks:
            for stop_pred in stop.get('stop_prediction'):
                stop_pred_time = stop_pred.get('time')
                if stop_pred_time != "--":
                    return datetime.strptime(stop_pred_time, '%H:%M:%S').time()

    @staticmethod
    def _find_last_bus_in_schedule(schedule):
        blocks = schedule.get('block')
        for stop in reversed(blocks):
            for stop_pred in reversed(stop.get('stop_prediction')):
                stop_pred_time = stop_pred.get('time')
                if stop_pred_time != "--":
                    return datetime.strptime(stop_pred_time, '%H:%M:%S').time()

    def get(self, tag=None):
        self.counter()
        parser = reqparse.RequestParser()
        parser.add_argument('time', type=float)
        args = parser.parse_args()

        check_time = datetime.fromtimestamp(args.get('time', time.time()))
        service_class = self._get_serviceclass(check_time)
        check_time = check_time.time()

        current_app.logger.info("THE TIME IS: {}".format(check_time))

        route_availability = {}

        def _time_in_range(start, end, x):
            if start <= end:
                return start <= x <= end
            else:
                return start <= x or x <= end

        tags_to_check = []
        if tag is not None:
            tags_to_check.append(tag)
        else:
            for route in current_app.nextbus_api.route_list().get('routes'):
                tag = route.get('tag')
                tags_to_check.append(tag)

        for tag in tags_to_check:
            route_availability[tag] = False
            #tag = route.get('tag')
            schedules = current_app.nextbus_api.route_schedule(tag)
            service_start_times = []
            service_end_times = []
            for schedule in schedules:
                if schedule.get('serviceClass') != service_class:
                    continue
                first_bus = self._find_first_bus_in_schedule(schedule)
                #current_app.logger.info("first bus {} for schedule".format(first_bus))
                service_start_times.append(first_bus)
                last_bus = self._find_last_bus_in_schedule(schedule)
                #current_app.logger.info("last bus {} for schedule".format(last_bus))
                service_end_times.append(last_bus)
                if _time_in_range(first_bus, last_bus, check_time):
                    current_app.logger.info("There is service for route {} at {}".format(tag, check_time))
                    route_availability[tag] = True

            #current_app.logger.info('Route {} starts at {} and ends at {}'.format(tag, service_start_time, service_end_time))
        return {'notinservice': [k for k,v in route_availability.items() if v is False]}, 200


class StopPredictions(NextbusApiResource):
    _display_name = "stop_predictions"

    def get(self):
        self.counter()
        return {'error': "not implemented"}


class RouteConfig(NextbusApiResource):
    _display_name = "routes_config"

    def get(self, tag=None):
        self.counter()
        parser = reqparse.RequestParser()
        parser.add_argument('verbose', type=bool)
        parser.add_argument('terse', type=bool)
        args = parser.parse_args()

        routes = current_app.nextbus_api.route_config(tag,
                                                      verbose=args.verbose,
                                                      terse=args.terse)

        if routes is None:
            raise ResourceNotFound
        return routes, 200
