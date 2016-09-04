
import os
import sys
import time

import requests
import redis

from flask import Flask
from flask_cache import Cache
from flask_restful import Api

import pytest
from mock import Mock, MagicMock
from mockredis import mock_redis_client

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)+"/.."))

from nextbus.errors import api_error_map
from nextbus.common.nextbusapi import NextbusApiClient, NextbusAgency, \
                                      NextbusAgencyList, NextbusRouteList, \
                                      NextbusRoute, NextbusRouteConfig, \
                                      NextbusRouteStop, NextbusDirection, \
                                      NextbusPath, NextbusPoint, \
                                      NextbusDirectionStop

from nextbus.resources import NextbusApiResource, Agency, Routes, \
                              RouteSchedule, RouteConfig




MOCK_DIR = os.path.join(os.path.realpath(os.path.dirname(__file__)),
                                         'data/nextbus-xml')
MOCK_MAP = {'agencyList': 'agencyList.xml',
            'routeList': 'routeList.xml'}


class MockResponse(object):
    def __init__(self, *args, **kwargs):
        assert len(args) == 1
        assert args[0] == 'http://webservices.nextbus.com/service/publicXMLFeed'
        self.params = kwargs.get('params', None)

    def raise_for_status(self):
        pass

    def __repr__(self):
        return "MockResponse({})".format(self.params)

    @property
    def text(self):
        xml_file = "{}{}.xml".format(self.params['command'],
                                   "_r_{}".format(self.params.get('r')) if 'r' in self.params else "")
        return open(os.path.join(MOCK_DIR, xml_file), 'r').read()


@pytest.fixture
def mock_get_request(monkeypatch):
    monkeypatch.setattr(requests, 'Response', MockResponse)

    def mock_get(*args, **kwargs):
        return MockResponse(*args, **kwargs)
    monkeypatch.setattr(requests, 'get', mock_get)


def test_new_client():
    assert(NextbusApiClient())


def test_agency_list(monkeypatch, mock_get_request, app, mock_redis):

    expected = NextbusAgencyList([NextbusAgency(tag='sf-muni',
                                                title='San Francisco Muni',
                                                shortTitle='SF Muni',
                                                regionTitle='California-Northern'),
                                  NextbusAgency(tag='seattle-sc',
                                                title='Seattle Streetcar',
                                                shortTitle='Seattle Streetcar',
                                                regionTitle='Washington')])

    with app.test_request_context('/agency'):
        agencies = Agency().get()
        assert agencies == (expected, 200)


def test_route_list(mock_get_request, app, mock_redis):

    expected = NextbusRouteList([NextbusRoute(tag='E', title='E-Embarcadero'),
                                 NextbusRoute(tag='F', title='F-Market & Wharves'),
                                 NextbusRoute(tag='J', title='J-Church'),
                                 NextbusRoute(tag='KT', title='KT-Ingleside/Third Street'),
                                 NextbusRoute(tag='L', title='L-Taraval')])

    with app.test_request_context('/routes'):
        route_rest = Routes().get()
        assert route_rest == (expected, 200)


def test_route_config(mock_get_request, app, mock_redis):

    stops = [NextbusRouteStop(tag='3892',
                              title='California St & Presidio Ave',
                              lat='37.7872699',
                              lon='-122.44696',
                              stopId='13892')]
    directions = [NextbusDirection([NextbusDirectionStop(tag='4277'),
                                    NextbusDirectionStop(tag='3555')],
                                   tag='1____I_F00',
                                   title='Inbound to Drumm + Clay',
                                   name='Inbound',
                                   useForUI='true'),
                  NextbusDirection([NextbusDirectionStop(tag='4015'),
                                    NextbusDirectionStop(tag='6294')],
                                   tag='1____O_F00',
                                   title='Outbound to Geary + 33rd Avenue',
                                   name='Outbound',
                                   useForUI='true')]
    paths = [NextbusPath([NextbusPoint(lat='37.7797399', lon='-122.49311'),
                          NextbusPoint(lat='37.78154', lon='-122.49335')]),
             NextbusPath([NextbusPoint(lat='37.78727', lon='-122.44696'),
                          NextbusPoint(lat='37.78692', lon='-122.44996')])]
    expected = [NextbusRouteConfig(stops, directions, paths, tag="1",
                                   title="1-California", color="cc6600",
                                   oppositeColor="000000", latMin="37.7797399",
                                   latMax="37.7954399", lonMin="-122.49335",
                                   lonMax="-122.39682")]

    with app.test_request_context('/routes/config/1') as ctx:
        #ctx.start = time.time()
        #assert app.nextbus_api.route_config(route_tag="1") == expected
        routecfg = RouteConfig().get(tag=1)
        #expected_rest = (: expected}, 200)
        assert routecfg == ({'routeconfig': expected}, 200)



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
