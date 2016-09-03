from flask_restful import reqparse, Resource, marshal

from nextbus import app
from nextbus.common.nextbusapi import NextbusApiClient, NextbusApiError

CACHE_TTL=3600


class NextbusApiResource(Resource):
    _display_name = None

    def counter(self):
        app.stats_redis.incr(self._display_name)


class ApiStats(NextbusApiResource):
    _display_name = "api_stats"

    def get(self):
        self.counter()
        names = [k._display_name for k in NextbusApiResource.__subclasses__()
                 if k._display_name]
        counts = app.stats_redis.mget(names)
        return {'stats': {k: v if v else 0 for k, v in zip(names, counts)}}


class Agency(NextbusApiResource):
    _stat_name = "agency_list"

    def get(self):
        self.counter()
        app.logger.debug("getting agency list")
        agencies = NextbusApiClient().agency_list()
        if agencies:
            return {'agency': agencies}, 200
        else:
            return {'error': 'resource not found'}, 404


class Routes(NextbusApiResource):
    _display_name = "route_list"

    def get(self):
        self.counter()
        routes = NextbusApiClient().route_list()
        if routes:
            return {'routes': routes}, 200
        else:
            return {'error': 'resource not found'}, 404


class RouteSchedule(NextbusApiResource):
    _display_name = "route_schedule"

    def get(self, tag=None):
        self.counter()
        return {'error': "not implemented"}


class StopPredictions(NextbusApiResource):
    _display_name = "stop_predictions"

    def get(self):
        self.counter()
        return {'error': "not implemented"}


class RouteConfig(NextbusApiResource):
    _display_name = "route_config"

    def get(self, tag=None):
        self.counter()
        parser = reqparse.RequestParser()
        parser.add_argument('verbose', type=bool)
        args = parser.parse_args()
        app.logger.debug("ARGS: {}".format(args))
        try:
            app.logger.info("getting route_config list and memoizing")
            routes = NextbusApiClient().route_config(tag, args.verbose)
            return {'routeconfig': routes}, 200
        except NextbusApiError as e:
            return {'error': 'no routes found{}'.format(
                    ' for tag {}'.format(tag) if tag else ''),
                    'message': e.message}, 404
