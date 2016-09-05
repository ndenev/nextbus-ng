import logging
import xml.etree.ElementTree as ET
import requests
from flask import current_app
from requests.exceptions import ConnectionError
from json import JSONEncoder
from retry import retry

#from nextbus.resources.exceptions import ResourceNotFound


logger = logging.getLogger('nextbusapi')

DEFAULT_AGENCY = 'sf-muni'
DEFAULT_ENDPOINT = 'http://webservices.nextbus.com/service/publicXMLFeed'
CACHE_TTL = 30

#
# XML Api Specification
# http://www.nextbus.com/xmlFeedDocs/NextBusXMLFeed.pdf
#


CMD_AGENCY_LIST = 'agencyList'
CMD_ROUTE_LIST = 'routeList'
CMD_ROUTE_CONFIG = 'routeConfig'
CMD_ROUTE_SCHEDULE = 'schedule'


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
        """
        self._data = {}
        for k, v in params.items():
            if k not in self._attributes:
                raise ValueError("Unknown attribute {} for {}",
                                 k, self.__class__.__name__)
            self._data[k] = v

    def get(self, key, default=None):
        return self._data.get(key, default)

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
    _attributes = ['agency']

    def __init__(self, agency_list=[]):
        super(NextbusAgencyList, self).__init__()
        self._data['agency'] = []
        for agency in agency_list:
            self.add_agency(agency)

    def add_agency(self, agency):
        if not isinstance(agency, NextbusAgency):
            raise ValueError("Expected NextbusAgency instance.")
        self._data['agency'].append(agency)

    @classmethod
    def from_etree(cls, etree):
        agency_list_obj = cls()
        for agency in etree.findall('agency'):
            agency_list_obj.add_agency(NextbusAgency.from_etree(agency))
        return agency_list_obj


class NextbusAgency(NextbusObject):
    """ Agency class """
    _attributes = ['tag', 'title', 'shortTitle', 'regionTitle']

    def __init__(self, **params):
        super(NextbusAgency, self).__init__(**params)

    @classmethod
    def from_etree(cls, etree):
        params = {'tag': etree.get('tag'),
                  'title': etree.get('title'),
                  'shortTitle': etree.get('shortTitle', etree.get('title')),
                  'regionTitle': etree.get('regionTitle')}
        return cls(**params)


class NextbusRouteList(NextbusObject):
    _attributes = ['routes']

    def __init__(self, route_list=[]):
        super(NextbusRouteList, self).__init__()
        self._data['routes'] = []
        for route in route_list:
            self.add_route(route)

    def add_route(self, route):
        if not isinstance(route, NextbusRoute):
            raise ValueError("Expected NextbusRoute instance.")
        self._data['routes'].append(route)

    @classmethod
    def from_etree(cls, etree):
        route_list = cls()
        for route in etree.findall('route'):
            route_list.add_route(NextbusRoute.from_etree(route))
        return route_list


class NextbusRoute(NextbusObject):
    """ Bus route class. """
    _attributes = ['tag', 'title', 'shortTitle']

    def __init__(self, **params):
        super(NextbusRoute, self).__init__(**params)

    @classmethod
    def from_etree(cls, etree):
        params = {'tag': etree.get('tag'),
                  'title': etree.get('title')}
        short_title = etree.get('shortTitle', None)
        if short_title:
            params.update({'shortTitle': short_title})
        return cls(**params)


class NextbusRouteConfigList(NextbusObject):
    _attributes = ['routeconfig']

    def __init__(self, routes=[], **params):
        super(NextbusRouteConfigList, self).__init__(**params)
        self._data['routeconfig'] = []
        for route in routes:
            self.add_route_config(route)

    def add_route_config(self, route):
        if not isinstance(route, NextbusRouteConfig):
            raise ValueError("Expected NextbusRouteConfig instance.")
        self._data['routeconfig'].append(route)

    @classmethod
    def from_etree(cls, etree):
        route_configs = cls()
        for route_cfg_et in etree.findall('route'):
            route_cfg = NextbusRouteConfig.from_etree(route_cfg_et)
            route_configs.add_route_config(route_cfg)
        return route_configs


class NextbusRouteConfig(NextbusObject):
    """ Bus route configuration object. """
    """ useForUI """
    """ verbose """
    _attributes = ['tag', 'title', 'color', 'oppositeColor', 'stop',
                   'direction', 'useForUI', 'latMax', 'latMin',
                   'lonMax', 'lonMin']

    def __init__(self, stops=[], directions=[], paths=[], **params):
        super(NextbusRouteConfig, self).__init__(**params)
        self._data['stop'] = []
        self._data['direction'] = []
        self._data['path'] = []

        for stop in stops:
            self.add_stop(stop)

        for direction in directions:
            self.add_direction(direction)

        for path in paths:
            self.add_path(path)

    def add_stop(self, stop):
        if not isinstance(stop, NextbusRouteStop):
            raise ValueError("Expected NextbusRouteStop instance.")
        self._data['stop'].append(stop)

    def add_direction(self, direction):
        if not isinstance(direction, NextbusDirection):
            raise ValueError("Expected NextbusDirection instance.")
        self._data['direction'].append(direction)

    def add_path(self, path):
        if not isinstance(path, NextbusPath):
            raise ValueError("Expected NextbusRoutePath instance.")
        self._data['path'].append(path)

    @classmethod
    def from_etree(cls, etree):
        params = {k: etree.get(k) for k in cls._attributes}
        if not etree.get('useForUI'):
            del params['useForUI']

        route_conf = cls(**params)

        for stop in etree.findall('stop'):
            route_conf.add_stop(NextbusRouteStop.from_etree(stop))

        for directn in etree.findall('direction'):
            route_conf.add_direction(NextbusDirection.from_etree(directn))

        for path in etree.findall('path'):
            route_conf.add_path(NextbusPath.from_etree(path))

        return route_conf


class NextbusRouteStop(NextbusObject):
    _attributes = ['tag', 'title', 'shortTitle', 'lat', 'lon', 'stopId']

    def __init__(self, **params):
        super(NextbusRouteStop, self).__init__(**params)

    @classmethod
    def from_etree(cls, etree):
        params = {'tag': etree.get('tag'),
                  'title': etree.get('title'),
                  'lat': etree.get('lat'),
                  'lon': etree.get('lon'),
                  'stopId': etree.get('stopId')}
        short_title = etree.get('shortTitle')
        if short_title:
            params.update({'shortTitle': short_title})
        return cls(**params)


class NextbusDirection(NextbusObject):
    _attributes = ['tag', 'title', 'name', 'useForUI']

    def __init__(self, stops=[], **params):
        super(NextbusDirection, self).__init__(**params)
        self._data['stop'] = []
        for stop in stops:
            self.add_stop(stop)

    def add_stop(self, stop):
        if not isinstance(stop, NextbusDirectionStop):
            raise ValueError("Expected NextbusDirectionStop instance.")
        self._data['stop'].append(stop)

    @classmethod
    def from_etree(cls, etree):
        params = {'tag': etree.get('tag'),
                  'title': etree.get('title'),
                  'name': etree.get('name')}
        use_for_ui = etree.get('useForUI')
        if use_for_ui:
            params.update({'useForUI': use_for_ui})
        direction = cls(**params)
        for stop in etree.findall('stop'):
            direction.add_stop(NextbusDirectionStop.from_etree(stop))
        return direction


class NextbusPath(NextbusObject):
    def __init__(self, points=[], tags=[]):
        super(NextbusPath, self).__init__()

        self._data['tag'] = []
        for tag in tags:
            self.add_tag(tag)

        self._data['point'] = []
        for point in points:
            self.add_point(point)

    def add_tag(self, tag):
        if not isinstance(tag, NextbusPathTag):
            raise ValueError("Expected NextbusPathTag")
        self._data['tag'].append(tag)

    def add_point(self, point):
        if not isinstance(point, NextbusPoint):
            raise ValueError("Expected NextbusPoint instance.")
        self._data['point'].append(point)

    @classmethod
    def from_etree(cls, etree):
        path = cls()

        for tag in etree.iter('tag'):
            path.add_tag(NextbusPathTag.from_etree(tag))

        for point in etree.iter('point'):
            path.add_point(NextbusPoint.from_etree(point))

        return path


class NextbusPathTag(NextbusObject):
    _attributes = ['id']

    def __init__(self, **params):
        super(NextbusPathTag, self).__init__(**params)

    @classmethod
    def from_etree(cls, etree):
        return cls(id=etree.get('id'))


class NextbusPoint(NextbusObject):
    _attributes = ['lat', 'lon']

    def __init__(self, **params):
        super(NextbusPoint, self).__init__(**params)

    @classmethod
    def from_etree(cls, etree):
        params = {'lat': etree.get('lat'),
                  'lon': etree.get('lon')}
        return cls(**params)


class NextbusDirectionStop(NextbusObject):
    _attributes = ['tag']

    def __init__(self, **params):
        super(NextbusDirectionStop, self).__init__(**params)

    @classmethod
    def from_etree(cls, etree):
        return cls(tag=etree.get('tag'))


class NextbusRouteSchedule(NextbusObject):
    _attributes = ['tag', 'title', 'scheduleClass',
                   'serviceClass', 'direction']

    def __init__(self, header, blocks, **params):
        super(NextbusRouteSchedule, self).__init__(**params)
        self._data['header'] = header
        self._data['block'] = blocks

    @classmethod
    def from_etree(cls, etree):
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
    def _make_request(self, command, params={}, set_agency=True, cache_ttl=CACHE_TTL):
        if set_agency:
            params['a'] = self.agency
        params['command'] = command

        def _cached_request(endpoint, params, headers, timeout):
            current_app.logger.info("Making HTTP request to NextbusXMLFeed: "
                                    " {} with params {}".format(endpoint,
                                                                params))
            req = requests.get(endpoint, headers=headers,
                               timeout=timeout, params=params)
            req.raise_for_status()
            return req

        # abuse the flask-cache decorator so we can set custom ttl per request type
        cached_request = current_app.cache.memoize(cache_ttl)(_cached_request)

        req = cached_request(self.endpoint, params,
                             self.headers, self.timeout)

        etree = self._parse_xml(req.text)

        return etree

    def agency_list(self):
        etree = self._make_request(CMD_AGENCY_LIST,
                                   set_agency=False,
                                   cache_ttl=3600)
        return NextbusAgencyList.from_etree(etree)

    def route_list(self):
        etree = self._make_request(CMD_ROUTE_LIST, cache_ttl=3600)
        return NextbusRouteList.from_etree(etree)

    def route_config(self, route_tag=None, verbose=False, terse=False):
        params = {}
        if route_tag is not None:
            params['r'] = route_tag
        if verbose is not False:
            params['verbose'] = True
        if terse is not False:
            params['terse'] = True
        etree = self._make_request(CMD_ROUTE_CONFIG, params=params)
        return NextbusRouteConfigList.from_etree(etree)

    def route_schedule(self, route_tag=None):
        params = {}
        if route_tag is not None:
            params.update({'r': route_tag})

        etree = self._make_request(CMD_ROUTE_SCHEDULE,
                                   params=params,
                                   cache_ttl=3600)
        return NextbusRouteSchedule.from_etree(etree)


class NextbusObjectSerializer(JSONEncoder):
    def default(self, o):
        return o._data
