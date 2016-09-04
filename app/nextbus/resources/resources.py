from flask_restful import reqparse, Resource
from flask import g, request
from socket import gethostname
import time
from nextbus import app
from nextbus.common.nextbusapi import NextbusApiError

CACHE_TTL = 3600
SLOW_THRESH = 1.0
SLOW_LOG_SIZE = 5


@app.teardown_request
def teardown_request(exception=None):
    request_time = time.time() - g.start
    if request_time > SLOW_THRESH:
        app.logger.info("logging slow request {} time: {}".format(
                                                          request.url_rule,
                                                          request_time))
        app.stats_redis.zadd('slowlog',
                             {'time': request_time,
                              'request': request,
                              'host': str(gethostname())},
                             request_time)
        r = app.stats_redis.zremrangebyrank('slowlog', 0, -(SLOW_LOG_SIZE + 1))
        if r:
            app.logger.info("purging {} slowlog entries", r)


class NextbusApiResource(Resource):
    _display_name = None

    def counter(self):
        g.start = time.time()
        app.stats_redis.incr(self._display_name)


class ApiStats(NextbusApiResource):
    _display_name = "stats"

    def get(self):
        self.counter()
        names = [k._display_name for k in NextbusApiResource.__subclasses__()
                 if k._display_name]
        counts = app.stats_redis.mget(names)
        return {'stats': {k: v if v else 0 for k, v in zip(names, counts)}}


class ApiSlowLog(NextbusApiResource):
    _display_name = "stats/slowlog"

    def get(self):
        self.counter()
        slowlog = []
        for r, t in app.stats_redis.zrevrange('slowlog', 0, 4, withscores=True):
            slowlog.append({'request': r, 'time': t})
        return {'slowlog': slowlog}


class ApiRoot(NextbusApiResource):
    _display_name = None

    def get(self):
        self.counter()
        names = [k._display_name for k in NextbusApiResource.__subclasses__()
                 if k._display_name]
        return {'resources': names}


class Agency(NextbusApiResource):
    _stat_name = "agency"

    def get(self):
        self.counter()
        app.logger.debug("getting agency list")
        agencies = app.nextbus_api.agency_list()
        if agencies:
            return {'agency': agencies}, 200
        else:
            return {'error': 'resource not found'}, 404


class Routes(NextbusApiResource):
    _display_name = "routes"

    def get(self):
        self.counter()
        routes = app.nextbus_api.route_list()
        if routes:
            return {'routes': routes}, 200
        else:
            return {'error': 'resource not found'}, 404


class RouteSchedule(NextbusApiResource):
    _display_name = "routes/schedule"

    def get(self, tag=None):
        self.counter()
        try:
            schedule = app.nextbus_api.route_schedule(tag)
            return {'schedule': schedule}, 200
        except NextbusApiError as e:
            return {'error': e.message}, 404


class StopPredictions(NextbusApiResource):
    _display_name = "stop/predictions"

    def get(self):
        self.counter()
        return {'error': "not implemented"}


class RouteConfig(NextbusApiResource):
    _display_name = "routes/config"

    def get(self, tag=None):
        self.counter()
        parser = reqparse.RequestParser()
        parser.add_argument('verbose', type=bool)
        args = parser.parse_args()
        app.logger.debug("ARGS: {}".format(args))
        try:
            app.logger.info("getting route_config list and memoizing")
            routes = app.nextbus_api.route_config(tag, args.verbose)
            return {'routeconfig': routes}, 200
        except NextbusApiError as e:
            return {'error': e.message}, 404
