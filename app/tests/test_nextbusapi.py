import pytest
from mock import MagicMock
import sys, os
import json

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)+"/.."))

from nextbus.common.nextbusapi import NextbusApiClient, NextbusAgency, \
                                      NextbusRoute, NextbusRouteConfig, \
                                      NextbusRouteStop, NextbusDirection, \
                                      NextbusPath, NextbusPoint, \
                                      NextbusDirectionStop

MOCK_DIR = os.path.join(os.path.realpath(os.path.dirname(__file__)),
                                         'data/nextbus-xml')
MOCK_MAP = {'agencyList': 'agencyList.xml',
            'routeList': 'routeList.xml'}

@pytest.fixture
def mock_get_request(monkeypatch):
    import requests

    class MockResponse(object):
        def __init__(self, *args, **kwargs):
            assert len(args) == 1
            assert args[0] == 'http://webservices.nextbus.com/service/publicXMLFeed'
            self.params = kwargs.get('params', None)

        def raise_for_status(self):
            pass

        @property
        def text(self):
            xml_file = "{}{}.xml".format(self.params['command'],
                                       "_r_{}".format(self.params.get('r')) if 'r' in self.params else "")
            return open(os.path.join(MOCK_DIR, xml_file), 'r').read()

    monkeypatch.setattr(requests, 'Response', MockResponse)

    def mock_get(*args, **kwargs):
        return MockResponse(*args, **kwargs)
    monkeypatch.setattr(requests, 'get', mock_get)

'''

thing = requests
thing.method = MagicMock(return_value=3)
thing.method(3, 4, 5, key='value')

thing.method.assert_called_with(3, 4, 5, key='value')
'''

def test_new_client():
    api = NextbusApiClient()

def test_agency_list(mock_get_request):
    api = NextbusApiClient()
    expected = [NextbusAgency(tag='sf-muni',
                              title='San Francisco Muni',
                              shortTitle='SF Muni',
                              regionTitle='California-Northern'),
                NextbusAgency(tag='seattle-sc',
                              title='Seattle Streetcar',
                              regionTitle='Washington')]
    assert api.agency_list() == expected
    # XXX: assert expected[0].shortTitle != expected[0].title
    assert expected[1].shortTitle == expected[1].title



def test_route_list(mock_get_request):
    api = NextbusApiClient()
    expected = [NextbusRoute(tag='E', title='E-Embarcadero'),
                NextbusRoute(tag='F', title='F-Market & Wharves'),
                NextbusRoute(tag='J', title='J-Church'),
                NextbusRoute(tag='KT', title='KT-Ingleside/Third Street'),
                NextbusRoute(tag='L', title='L-Taraval')]
    assert api.route_list() == expected

def test_route_config(mock_get_request):
    api = NextbusApiClient()
    stops = [NextbusRouteStop(tag='3892',
                              title='California St & Presidio Ave',
                              lat='37.7872699',
                              lon='-122.44696',
                              stopId='13892')]
    directions = [NextbusDirection([NextbusDirectionStop(tag='4277'),
                                    NextbusDirectionStop(tag='3555')],
                                   tag='1____I_F00', title='Inbound to Drumm + Clay',
                                   name='Inbound', useForUI='true'),
                  NextbusDirection([NextbusDirectionStop(tag='4015'),
                                    NextbusDirectionStop(tag='6294')],
                                   tag='1____O_F00',
                                   title='Outbound to Geary + 33rd Avenue',
                                   name='Outbound', useForUI='true')]
    paths = [NextbusPath([NextbusPoint(lat='37.7797399', lon='-122.49311'),
                          NextbusPoint(lat='37.78154', lon='-122.49335')]),
             NextbusPath([NextbusPoint(lat='37.78727', lon='-122.44696'),
                          NextbusPoint(lat='37.78692', lon='-122.44996')])]
    expected = [NextbusRouteConfig(stops, directions, paths, tag="1",
                                   title="1-California", color="cc6600",
                                   oppositeColor="000000", latMin="37.7797399",
                                   latMax="37.7954399", lonMin="-122.49335",
                                   lonMax="-122.39682")]
    assert api.route_config(route_tag="1") == expected

def test_bad_object():
    with pytest.raises(ValueError):
        NextbusPoint(doesnot=False, exist=True)

def test_eq_neq():
    a = NextbusPoint(lat="0.0", lon="1.1")
    b = NextbusPoint(lat="2.2", lon="3.3")
    c = NextbusPoint(lat="0.0", lon="1.1")
    d = NextbusDirectionStop(tag='X')
    assert a != b
    assert a == c
    assert a != d

def test_repr():
    p = NextbusPoint(lat="0.0", lon="1.1")
    assert repr(p) == "NextbusPoint(lat='0.0', lon='1.1')"
