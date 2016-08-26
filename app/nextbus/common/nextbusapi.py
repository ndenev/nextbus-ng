import sys
from nextbus import app
import xml.etree.ElementTree as ET
import requests

DEFAULT_AGENCY='sf-muni'
DEFAULT_ENDPOINT='http://webservices.nextbus.com/service/publicXMLFeed'
#CACHE_TTL=30
CACHE_TTL=300

# http://www.nextbus.com/xmlFeedDocs/NextBusXMLFeed.pdf

'''
Commands
command=agencyList
sf-muni


Command "routeList"
To obtain a list of routes for an agency, use the "routeList" command. The agency is specified by
the "a" parameter in the query string. The tag for the agency as obtained from the agencyList
command should be used.
The format of the command is:
    http://webservices.nextbus.com/service/publicXMLFeed?command=routeList&
    a=<agency_tag>
    The route list data returned has multiple attributes. These are:
     tag  unique alphanumeric identifier for route, such as N.
     title  the name of the route to be displayed in a User Interface, such as N-Judah.
     shortTitle  for some transit agencies shorter titles are provided that can be useful for
    User Interfaces where there is not much screen real estate, such as on smartphones.
    This element is only provided where a short title is actually available. If a short title is
    not available then the regular title element should be used.



'''

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


class NextbuApiFatalError(NextbusApiError):
    """ Fatal exception, no need to retry. """
    pass


class NextbusObject(object):
    _obj_map = {'Error': 'NextbusApiError',
                'agency': 'NextbusAgency',
                'route': 'NextbusRoute',
                'direction': 'NextbusDirection',
                'stop': 'NextbusStop',
                'path': 'NextbusPath',
                'point': 'NextbusPoint',
                'predictions': 'NextbusPredictions',
                'prediction': 'NextbusPrediction',
                'message': 'NextbusMessage'}
    _attributes = []
    def __init__(self, **params):
        self._data = {a: params.get(a, None) for a in self._attributes}

    @classmethod
    def factory(cls, t, d):
        return getattr(sys.modules[__name__],
                       cls._obj_map.get(t, NextbusApiError))(**d)

    def serialize(self):
        return self._data

    def __repr__(self):
        print "{}".format({self.__class__.__name__: self._data})
        return "{}".format({self.__class__.__name__: self._data})



class NextbusAgency(NextbusObject):
    """ Agency class """
    _attributes = ['tag', 'title', 'shortTitle', 'regionTitle']
    def __init__(self, **params):
        super(NextbusAgency, self).__init__(**params)

    @property
    def tag(self):
        """ Get the agency tag. """
        return self._data.get('tag', None)
    
    @property
    def title(self):
        """ Get the agency title. """
        return self._data.get('title', None)

    @property
    def short_title(self):
        """ Get the agency short title.
        The short title might be missing in the API response,
        so in this case according to the documentation we can
        use the "title" attribute.
        """
        return self._data.get('shortTitle', self.title)

    @property
    def region_title(self):
        """ Get the agency region title. """
        return self._data.get('regionTitle', None)


class NextbusRoute(NextbusObject):
    """ Bus route class. """
    _attributes = ['tag', 'title', 'shortTitle']
    def __init__(self, **params):
        super(NextbusRoute, self).__init__(**params)

    @property
    def tag(self):
        """ Get route tag. """
        return self._data.get('tag', None)
    
    @property
    def title(self):
        """ Get route title. """
        return self._data.get('title', None)

    @property
    def short_title(self):
        """ Get short title if it exists.
        if it doesn't fall back to regular title.
        """
        return self._data.get('shortTitle', self.title)


class NextbusRouteConfig(NextbusObject):
    """ Bus route configuration object. """
    """ useForUI """
    """ verbose """
    def __init__(self, tag, title):
        pass

class NextbusRouteStop(NextbusObject):
    def __init__(self):
        pass


#@app.cache.memoize(CACHE_TTL)
def _cached_request(endpoint, headers, timeout, params):
    """ Wrapper function around request get so we can more
    easily memoize it without having to deal with the class
    instance.
    """
    r = requests.get(endpoint, headers=headers, timeout=timeout, params=params)
    r.raise_for_status()
    root = ET.fromstring(r.text)

    if root.tag != 'body':
        raise NextbusApiError

    objects = []
    for child in root:
        #objects.append(NextbusObject.factory(child.tag, child.attrib))
        objects.append({child.tag: child.attrib})
    return objects

class NextbusApiClient(object):
    def __init__(self, agency=DEFAULT_AGENCY, endpoint=DEFAULT_ENDPOINT):
        self.agency = agency
        self.endpoint = endpoint
        self.headers = {'content-type': 'application/json'}
        self.timeout = 10


    def _make_request(self, command, params={}):
       params.update({'command': command})
       return _cached_request(self.endpoint,
                              headers=self.headers,
                              timeout=self.timeout,
                              params=params)

    def agency_list(self):
        command = 'agencyList'
        return self._make_request(command)

    def route_list(self):
        command = 'routeList'
        return self._make_request(command, params={'a': self.agency})

    def route_config(self, route_tag=None):
        command = 'routeConfig'
        params = {'a': self.agency}
        if route_tag is not None:
            params.update({'r': route_tag})
        return self._make_request(command, params=params)


