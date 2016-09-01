from flask_restful import Resource

from nextbus.common.nextbusapi import NextbusApiClient


class Agency(Resource):
    def get(self):
        api = NextbusApiClient()
        agencies = [a.serialize() for a in api.agency_list()]
        if agencies:
            return {'agency': agencies}, 200
        else:
            return {'error': 'resource not found'}, 404


class Routes(Resource):
    def get(self):
        api = NextbusApiClient()
        routes = [r.serialize() for r in api.route_list()]
        if routes:
            return {'routes': routes}, 200
        else:
            return {'error': 'resource not found'}, 404


class RouteConfig(Resource):
    def get(self, tag=None):
        api = NextbusApiClient()
        routes = [r.serialize() for r in api.route_config(tag)]
        if routes:
            return {'routeconfig': routes}
        else:
            return {'error': 'no routes found for tag {}'.format(tag if tag else 'all')}, 404
