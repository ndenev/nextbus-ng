from nextbus import app
import xml.etree.ElementTree as ET
import requests

ENDPOINT='http://webservices.nextbus.com/service/publicXMLFeed'

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
    def serialize(self):
        # return {k: v for k, v in self._data.items()}
        return self._data
    def __repr__(self):
        return "{}<{}>".format(self.__class__.__name__,
                               self._data)


class NextbusAgency(NextbusObject):
    """ Agency class """
    def __init__(tag, title, region_title, short_title=None):
        self._data = {'tag': tag,
                      'title': title,
                      'shortTitle': short_title,
                      'regionTitle': region_title}

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
    """ Bus route class """
    def __init__(tag, title, short_title=None):
        self._data = {'tag': tag,
                      'title': title,
                      'shortTitle': short_title}

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






class NextbusApiClient(object):
    def __init__(agency):
        self.agency = agency

    def agency_list(self):
        pass

    def route_list(self):
        pass

    def route_config(self, route_tag=None):
        pass


