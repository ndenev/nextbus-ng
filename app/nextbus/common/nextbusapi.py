import logging
import xml.etree.ElementTree as ET
import requests
from requests.exceptions import ConnectionError
from json import JSONEncoder
from retry import retry

from nextbus import app

logger = logging.getLogger('nextbusapi')

DEFAULT_AGENCY = 'sf-muni'
DEFAULT_ENDPOINT = 'http://webservices.nextbus.com/service/publicXMLFeed'
CACHE_TTL = 3600

#
# XML Api Specification
# http://www.nextbus.com/xmlFeedDocs/NextBusXMLFeed.pdf
#


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
        class_name = self.__class__.__name__
        attribs = ", ".join(["{}={}".format(k, repr(v))
                            for k, v in self._data.items()])
        return "{}({})".format(class_name, attribs)

    def __str__(self):
        return self.__repr__()


class NextbusAgencyList(NextbusObject):
    @staticmethod
    def from_etree(etree):
        return [NextbusAgency(**e.attrib) for e in etree.findall('agency')]


class NextbusAgency(NextbusObject):
    """ Agency class """
    _attributes = ['tag', 'title', 'shortTitle', 'regionTitle']

    def __init__(self, **params):
        super(NextbusAgency, self).__init__(**params)

    '''
    @NextbusObject.shortTitle.getter
    def shortTitle(self):
        """ Override the shortTitle getter.
        The short title might be missing in th  e API response,
        so in this case according to the documentation we can
        use the "title" attribute.
        """
        return "XXX"
        #return self.shortTitle if self.shortTitle else self.title
    '''


class NextbusRouteList(NextbusObject):
    @staticmethod
    def from_etree(etree):
        return [NextbusRoute(**e.attrib) for e in etree.findall('route')]


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

    @staticmethod
    def from_etree(etree):
        routes = []
        for rt in etree.findall('route'):
            stops = [NextbusRouteStop(**e.attrib) for e in rt.findall('stop')]
            dirs = []
            for direc in rt.findall('direction'):
                dirstp = [NextbusDirectionStop(**e.attrib) for e
                          in direc.findall('stop')]
                dirs.append(NextbusDirection(dirstp, **direc.attrib))
            paths = []
            for path in rt.findall('path'):
                points = [NextbusPoint(**e.attrib) for e
                          in path.findall('point')]
                paths.append(NextbusPath(points, **path.attrib))
            routes.append(NextbusRouteConfig(stops,
                                             dirs,
                                             paths,
                                             **rt.attrib))
        return routes

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


class NextbusRouteSchedule(NextbusObject):
    _attributes = ['tag', 'title', 'scheduleClass',
                   'serviceClass', 'direction']

    def __init__(self, header, blocks, **params):
        super(NextbusRouteSchedule, self).__init__(**params)
        self._data['header'] = header
        self._data['block'] = blocks

    @staticmethod
    def from_etree(etree):
        routes = []
        for rt in etree.findall('route'):
            header = rt.find('header')
            hstops = [NextbusRouteScheduleHeaderEntry(e.text, **e.attrib) for e
                      in header.findall('stop')]
            blocks = []
            for block in rt.findall('tr'):
                stopdata = [NextbusRouteSchedulePrediction(e.text, **e.attrib)
                            for e in block.findall('stop')]
                blocks.append(NextbusRouteScheduleBlock(stopdata,
                                                        **block.attrib))
            routes.append(NextbusRouteSchedule(hstops, blocks, **rt.attrib))
        return routes

class NextbusRouteScheduleHeader(NextbusObject):
    def __init__(self, stops, **params):
        super(NextbusRouteScheduleHeader, self).__init__(**params)
        self._data['stop'] = stops


class NextbusRouteScheduleHeaderEntry(NextbusObject):
    _attributes = ['tag']

    def __init__(self, text, **params):
        super(NextbusRouteScheduleHeaderEntry, self).__init__(**params)
        self._data['title'] = text



class NextbusRouteScheduleBlock(NextbusObject):
    _attributes = ['blockID']

    def __init__(self, stopdata, **params):
        super(NextbusRouteScheduleBlock, self).__init__(**params)
        self._data['stop_prediction'] = stopdata


class NextbusRouteSchedulePrediction(NextbusObject):
    _attributes = ['tag', 'epochTime']

    def __init__(self, text_time, **params):
        super(NextbusRouteSchedulePrediction, self).__init__(**params)
        self._data['time'] = text_time


@app.cache.memoize(CACHE_TTL)
def _cached_request(endpoint, params, headers, timeout):
    req = requests.get(endpoint, headers=headers,
                       timeout=timeout, params=params)
    req.raise_for_status()
    return req


class NextbusApiClient(object):
    def __init__(self, agency=DEFAULT_AGENCY, endpoint=DEFAULT_ENDPOINT):
        self.agency = agency
        self.endpoint = endpoint
        self.headers = {'Accept-Encoding': 'gzip, deflate'}
        self.timeout = 10

    def _parse_xml(self, text):
        etree = ET.fromstring(text)
        err = etree.find('Error')
        if err is None:
            return etree
        if err.get('shouldRetry') == "true":
            raise NextbusApiRetriableError(err.text)
        raise NextbusApiFatalError(err.text)

    @retry((ConnectionError, NextbusApiRetriableError), tries=3, delay=10)
    def _make_request(self, command, params={}, set_agency=True):
        if set_agency:
            params.update({'a': self.agency})
        params.update({'command': command})
        logger.debug('GET {}?{} HEADERS: {}'.format(
            self.endpoint, "&".join(["{}={}".format(k, v) for k, v
                                     in params.items()]), self.headers))

        req = _cached_request(self.endpoint, params,
                              self.headers, self.timeout)

        etree = self._parse_xml(req.text)

        return etree

    def agency_list(self):
        etree = self._make_request('agencyList', set_agency=False)
        return NextbusAgencyList.from_etree(etree)

    def route_list(self):
        etree = self._make_request('routeList')
        return NextbusRouteList.from_etree(etree)

    def route_config(self, route_tag=None, verbose=False, terse=False):
        params = {}
        if route_tag is not None:
            params.update({'r': route_tag})
        if verbose is not False:
            params.update({'verbose': True})
        etree = self._make_request('routeConfig', params=params)

        routes = []
        for rt in etree.findall('route'):
            stops = [NextbusRouteStop(**e.attrib) for e in rt.findall('stop')]
            dirs = []
            for direc in rt.findall('direction'):
                dirstp = [NextbusDirectionStop(**e.attrib) for e
                          in direc.findall('stop')]
                dirs.append(NextbusDirection(dirstp, **direc.attrib))
            paths = []
            for path in rt.findall('path'):
                points = [NextbusPoint(**e.attrib) for e
                          in path.findall('point')]
                paths.append(NextbusPath(points, **path.attrib))
            routes.append(NextbusRouteConfig(stops,
                                             dirs,
                                             paths,
                                             **rt.attrib))
        return routes

    def route_schedule(self, route_tag=None):
        params = {}
        if route_tag is not None:
            params.update({'r': route_tag})

        etree = self._make_request('schedule', params=params)
        return NextbusRouteSchedule.from_etree(etree)


class NextbusObjectSerializer(JSONEncoder):
    def default(self, o):
        return o._data
