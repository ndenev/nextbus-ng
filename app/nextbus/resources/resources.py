from flask_restful import reqparse, Resource

from nextbus import app
from nextbus.common.nextbusapi import NextbusApiClient, NextbusApiError


class Agency(Resource):
    def get(self):
        api = NextbusApiClient()
        #agencies = [a.serialize() for a in api.agency_list()]
        agencies = api.agency_list()
        if agencies:
            return {'agency': agencies}, 200
        else:
            return {'error': 'resource not found'}, 404


class Routes(Resource):
    def get(self):
        api = NextbusApiClient()
        #routes = [r.serialize() for r in api.route_list()]
        routes = api.route_list()
        if routes:
            return {'routes': routes}, 200
        else:
            return {'error': 'resource not found'}, 404


class RouteSchedule(Resource):
    def get(self, tag=None):
        api = NextbusApiClient()


class RouteConfig(Resource):
    def get(self, tag=None, verbose=False):
        parser = reqparse.RequestParser()
        parser.add_argument('verbose', type=bool)
        args = parser.parse_args()
        api = NextbusApiClient()
        #routes = _serialize(api.route_config(tag, verbose=args.get('verbose', False)))
        try:
            routes = api.route_config(tag, verbose=args.get('verbose', False))
            return {'routeconfig': routes}
        except NextbusApiError as e:
            return {'error': 'no routes found for tag {}'.format(tag if tag else 'all'),
                    'message': e.message}, 404
