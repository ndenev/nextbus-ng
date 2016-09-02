from flask_restful import reqparse, Resource
from nextbus.common.nextbusapi import NextbusObject, NextbusApiClient


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


def _serialize(o):
    if issubclass(o.__class__, NextbusObject):
        ret = o.serialize()
        for k, v in o.nested.items():
            ret.update({k: _serialize(v)})
        return ret
    elif issubclass(o.__class__, dict):
        return o
    elif issubclass(o.__class__, list):
        return [_serialize(i) for i in o]


class RouteSchedule(Resource):
    def get(self, tag=None):
        api = NextbusApiClient()


class RouteConfig(Resource):
    def get(self, tag=None, verbose=False):
        parser = reqparse.RequestParser()
        parser.add_argument('verbose', type=bool)
        args = parser.parse_args()
        api = NextbusApiClient()
        routes = _serialize(api.route_config(tag, verbose=args.get('verbose', False)))
        #routes = [r for r in api.route_config(tag, verbose=args.get('verbose', False))]

        if routes:
            return {'routeconfig': routes}
        else:
            return {'error': 'no routes found for tag {}'.format(tag if tag else 'all')}, 404
