import xml.etree.ElementTree as ET
import requests
from requests.exceptions import ConnectionError
from json import JSONEncoder
from retry import retry


DEFAULT_AGENCY = 'sf-muni'
DEFAULT_ENDPOINT = 'http://webservices.nextbus.com/service/publicXMLFeed'

#
# XML Api Specification
# http://www.nextbus.com/xmlFeedDocs/NextBusXMLFeed.pdf
#

'''
Errors:

    <body>
    <Error shouldRetry="true">
    Agency server cannot accept client while status is: agency
    name = sf-muni,status = UNINITIALIZED, client count = 0, last
    even t = 0 seconds ago Could not get route list for agency tag "sf-muni".
    Either the route tag is bad or the system is initializing.
    </Error>
    </body>

'''


class NextbusApiError(Exception):
    """ NextbusApi Client base exception class """
    pass


class NextbusApiRetriableError(NextbusApiError):
    """ Exception signifying a retriable error. """
    pass


class NextbusApiFatalError(NextbusApiError):
    """ Fatal exception, no need to retry. """
    pass


class NextbusObject(object):
    """ Base class for all Nextbus API objects/resources.
    """
    _attributes = []

    def __init__(self, **params):
        """ Initialize the object and validate if the provided parameters
        are valid for the specific sub class.
        Also build getters for all attributes.
        """
        self._data = {}
        for k, v in params.items():
            if k not in self._attributes:
                raise ValueError("Unknown attribute {} for {}",
                                 k, self.__class__.__name__)
            self._data[k] = v
            setattr(self.__class__, k,
                    property(lambda self: self._data.get(k, None)))

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__,
                               ", ".join(["{}='{}'".format(k, v) for k, v in self._data.items()]))


class NextbusAgency(NextbusObject):
    """ Agency class """
    _attributes = ['tag', 'title', 'shortTitle', 'regionTitle']

    def __init__(self, **params):
        super(NextbusAgency, self).__init__(**params)
        setattr(NextbusObject, 'shortTitle', property(lambda self: "XXX"))
    '''
    @NextbusObject.shortTitle.getter
    def shortTitle(self):
        """ Override the shortTitle getter.
        The short title might be missing in the API response,
        so in this case according to the documentation we can
        use the "title" attribute.
        """
        return "XXX"
        #return self.shortTitle if self.shortTitle else self.title
    '''

class NextbusRoute(NextbusObject):
    """ Bus route class. """
    _attributes = ['tag', 'title', 'shortTitle']

    def __init__(self, **params):
        super(NextbusRoute, self).__init__(**params)

    '''
    @property
    def shortTitle(self):
        """ Override the shortTitle getter.
        The short title might be missing in the API response,
        so in this case according to the documentation we can
        use the "title" attribute.
        """
        return "XXX"
        #return self.shortTitle if self.shortTitle else self.title
    '''

class NextbusRouteConfig(NextbusObject):
    """ Bus route configuration object. """
    """ useForUI """
    """ verbose """
    _attributes = ['tag', 'title', 'color', 'oppositeColor', 'stop',
                   'direction', 'useForUI', 'latMax', 'latMin',
                   'lonMax', 'lonMin']

    def __init__(self, stops, directions, paths, **params):
        super(NextbusRouteConfig, self).__init__(**params)
        self._data['stop'] = stops
        self._data['directions'] = directions
        self._data['path'] = paths


class NextbusRouteStop(NextbusObject):
    _attributes = ['tag', 'title', 'shortTitle', 'lat', 'lon', 'stopId']

    def __init__(self, **params):
        super(NextbusRouteStop, self).__init__(**params)


class NextbusDirection(NextbusObject):
    _attributes = ['tag', 'title', 'name', 'useForUI']

    def __init__(self, stops, **params):
        super(NextbusDirection, self).__init__(**params)
        self._data['stop'] = stops


class NextbusPath(NextbusObject):
    def __init__(self, points, **params):
        super(NextbusPath, self).__init__(**params)
        self._data['point'] = points


class NextbusPoint(NextbusObject):
    _attributes = ['lat', 'lon']

    def __init__(self, **params):
        super(NextbusPoint, self).__init__(**params)


class NextbusDirectionStop(NextbusObject):
    _attributes = ['tag']

    def __init__(self, **params):
        super(NextbusDirectionStop, self).__init__(**params)


class NextbusApiClient(object):
    def __init__(self, agency=DEFAULT_AGENCY, endpoint=DEFAULT_ENDPOINT):
        self.agency = agency
        self.endpoint = endpoint
        self.headers = {'content-type': 'application/json'}
        self.timeout = 10

    def _check_error(self, etree):
        err = etree.find('Error')
        if err is not None:
            if err.get('shouldRetry', None) == "true":
                raise NextbusApiRetriableError(err.text)
            else:
                raise NextbusApiFatalError(err.text)

    @retry((ConnectionError, NextbusApiRetriableError), tries=3, delay=10)
    def _make_request(self, command, params={}, set_agency=True):
        if set_agency:
            params.update({'a': self.agency})
        params.update({'command': command})
        req = requests.get(self.endpoint, headers=self.headers,
                           timeout=self.timeout, params=params)
        req.raise_for_status()
        etree = ET.fromstring(req.text)
        self._check_error(etree)
        return etree

    def agency_list(self):
        et = self._make_request('agencyList', set_agency=False)
        return [NextbusAgency(**e.attrib) for e in et.findall('agency')]

    def route_list(self):
        et = self._make_request('routeList')
        return [NextbusRoute(**e.attrib) for e in et.findall('route')]

    def route_config(self, route_tag=None, verbose=False):
        params = {}
        if route_tag is not None:
            params.update({'r': route_tag})
        if verbose is not False:
            params.update({'verbose': True})
        et = self._make_request('routeConfig', params=params)

        routes = []
        for rt in et.findall('route'):
            stops = [NextbusRouteStop(**e.attrib) for e in rt.findall('stop')]
            dirs = []
            for direc in rt.findall('direction'):
                dirstp = [NextbusDirectionStop(**e.attrib) for e in direc.findall('stop')]
                dirs.append(NextbusDirection(dirstp, **direc.attrib))
            paths = []
            for path in rt.findall('path'):
                points = [NextbusPoint(**e.attrib) for e in path.findall('point')]
                paths.append(NextbusPath(points, **path.attrib))
            routes.append(NextbusRouteConfig(stops, dirs, paths, **rt.attrib))
        return routes


class NextbusObjectSerializer(JSONEncoder):
    def default(self, o):
        return o._data
