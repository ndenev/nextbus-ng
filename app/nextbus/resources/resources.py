from flask_restful import reqparse, Resource

from nextbus import app
from nextbus.common.nextbusapi import NextbusApiClient, NextbusApiError

@app.cache.memoize(300)
def nextbus_api(callable, *args, **kwargs):
    """ Wrapping the calls to Nextbus XML Api with this function
    so we can more easily memoize the response, otherwise we have
    to deal with the instance object for the Resource class.
    """
    print "CACHING: {} {} {}".format(callable, args, kwargs)
    nb = NextbusApiClient()
    return getattr(nb, callable)(*args, **kwargs)

class Agency(Resource):
    def get(self):
        agencies = nextbus_api('agency_list')
        if agencies:
            return {'agency': agencies}, 200
        else:
            return {'error': 'resource not found'}, 404


class Routes(Resource):
    def get(self):
        routes = nextbus_api('route_list')
        if routes:
            return {'routes': routes}, 200
        else:
            return {'error': 'resource not found'}, 404


class RouteSchedule(Resource):
    def get(self, tag=None):
        pass


class RouteConfig(Resource):
    def get(self, tag=None, verbose=False):
        print "GOT TAG: XXX {}".format(tag)
        parser = reqparse.RequestParser()
        parser.add_argument('verbose', type=bool)
        args = parser.parse_args()
        try:
            routes = nextbus_api('route_config', tag,
                                 verbose=args.get('verbose', False))
            return {'routeconfig': routes}, 200
        except NextbusApiError as e:
            return {'error': 'no routes found for tag {}'.format(tag if tag else 'all'),
                    'message': e.message}, 404
