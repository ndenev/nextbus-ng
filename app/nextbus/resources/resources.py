from flask_restful import reqparse, Resource
from flask import Flask, g, request, current_app
from socket import gethostname
import json
import time
from nextbus import app
from nextbus.common.nextbusapi import NextbusApiError

CACHE_TTL = 30
SLOW_THRESH = 2.0
SLOW_LOG_SIZE = 50


@app.teardown_request
def teardown_request(exception=None):
    """ We are logging slow queries here. """
    request_time = time.time() - g.start
    if request_time > SLOW_THRESH:
        app.logger.info("logging slow request {} time: {}".format(
                                                          request.url_rule,
                                                          request_time))
        app.stats_redis.zadd('slowlog',
                             json.dumps({'time': time.time(),
                                         'path': request.path,
                                         'method': request.method,
                                         'args': request.args.to_dict(),
                                         'remote_host': request.remote_addr,
                                         'api_host': gethostname()}),
                             request_time)

        r = app.stats_redis.zremrangebyrank('slowlog', 0, -(SLOW_LOG_SIZE + 1))

        if r > 0:
            app.logger.info("trimming off {} slowlog entries".format(r))


class NextbusApiResource(Resource):
    _display_name = None

    def counter(self):
        g.start = time.time()
        app.stats_redis.incr(self._display_name)


class ApiStats(NextbusApiResource):
    _display_name = "stats"

    def get(self):
        self.counter()
        ids = [k._display_name for k in NextbusApiResource.__subclasses__()
               if k._display_name is not None]
        hits = app.stats_redis.mget(ids)
        return {'stats': {k: int(v) if v else 0 for k, v in zip(ids, hits)}}, 200


class ApiSlowLog(NextbusApiResource):
    _display_name = "stats_slowlog"

    def get(self):
        self.counter()
        slowlog = []
        for rj, rt in app.stats_redis.zrevrange('slowlog', 0,
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
        app.logger.debug("getting agency list")
        agencies = app.nextbus_api.agency_list()
        if agencies is None:
            raise ResourceNotFound
        return agencies, 200


class Routes(NextbusApiResource):
    _display_name = "routes_list"

    def get(self):
        self.counter()
        routes = app.nextbus_api.route_list()
        if routes:
            return {'routes': routes}, 200
        else:
            return {'error': 'resource not found'}, 404


class RouteSchedule(NextbusApiResource):
    _display_name = "routes_schedule"

    def get(self, tag=None):
        self.counter()
        try:
            schedule = app.nextbus_api.route_schedule(tag)
            return {'schedule': schedule}, 200
        except NextbusApiError as e:
            return {'error': e.message}, 404


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
        try:
            app.logger.info("getting route_config list and memoizing")
            routes = app.nextbus_api.route_config(tag,
                                                  verbose=args.verbose,
                                                  terse=args.terse)
            return {'routeconfig': routes}, 200
        except NextbusApiError as e:
            return {'error': e.message}, 404
