import os
import json

import pytest
import requests
import xml.etree.ElementTree as ET

from nextbus.common.nextbusapi import NextbusApiClient, NextbusAgency, \
                                      NextbusAgencyList, NextbusRouteList, \
                                      NextbusRoute, NextbusRouteConfig, \
                                      NextbusRouteConfigList, NextbusPathTag, \
                                      NextbusRouteStop, NextbusDirection, \
                                      NextbusPath, NextbusPoint, \
                                      NextbusDirectionStop, \
                                      NextbusRouteSchedulePrediction, \
                                      NextbusRouteScheduleBlock

from nextbus.resources import Agency, Routes, RouteSchedule, RouteConfig
from nextbus.resources.exceptions import InvalidRouteTagFormat

MOCK_DIR = os.path.join(os.path.realpath(os.path.dirname(__file__)),
                                         'data/nextbus-xml')


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

    with pytest.raises(ValueError):
        agency_list = NextbusAgencyList()
        agency_list.add_agency({'tag': 'z', 'title': 'xxx'})


def test_route_list(mock_get_request, app, mock_redis):

    expected = NextbusRouteList([NextbusRoute(tag='E', title='E-Embarcadero'),
                                 NextbusRoute(tag='F', title='F-Market & Wharves'),
                                 NextbusRoute(tag='J', title='J-Church'),
                                 NextbusRoute(tag='KT', title='KT-Ingleside/Third Street'),
                                 NextbusRoute(tag='L', title='L-Taraval')])

    with app.test_request_context('/routes'):
        route_rest = Routes().get()
        assert route_rest == (expected, 200)

    with pytest.raises(ValueError):
        route_list = NextbusRouteList()
        route_list.add_route({'tag': 'z', 'title': 'xxx'})

    x = '<route tag="test" title="test_title" shortTitle="short_title" />'

    etree = ET.fromstring(x)
    route = NextbusRoute.from_etree(etree)

    assert route.get('tag') == "test"
    assert route.get('title') == "test_title"
    assert route.get('shortTitle') == "short_title"
    assert route.get('asdf', 'fdsa') == "fdsa"
    assert route.get('asdf') is None


def test_route_path():

    # From &verbose output
    pxv = '''\
    <path>
    <tag id="E____I_S10_6_4530_33095"/>
    <point lat="37.80835" lon="-122.41029"/>
    <point lat="37.80833" lon="-122.4105"/>
    <point lat="37.80784" lon="-122.41081"/>
    </path>'''

    # from normal
    px = '''\
    <path>
    <point lat="37.80835" lon="-122.41029"/>
    <point lat="37.80833" lon="-122.4105"/>
    <point lat="37.80784" lon="-122.41081"/>
    </path>'''

    expected = NextbusPath(points=[NextbusPoint(lat="37.80835",
                                                lon="-122.41029"),
                                   NextbusPoint(lat="37.80833",
                                                lon="-122.4105"),
                                   NextbusPoint(lat="37.80784",
                                                lon="-122.41081")])
    from_etree = NextbusPath.from_etree(ET.fromstring(px))
    assert from_etree == expected

    expected.add_tag(NextbusPathTag(id="E____I_S10_6_4530_33095"))
    from_etree_verbose = NextbusPath.from_etree(ET.fromstring(pxv))
    assert from_etree_verbose == expected


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
    expected = NextbusRouteConfigList([NextbusRouteConfig(stops, directions, paths, tag="1",
                                       title="1-California", color="cc6600",
                                       oppositeColor="000000", latMin="37.7797399",
                                       latMax="37.7954399", lonMin="-122.49335",
                                       lonMax="-122.39682")])

    with app.test_request_context('/routes/config/1'):
        routecfg = RouteConfig().get(tag=1)
        assert routecfg == (expected, 200)


def test_bad_route(mock_get_request, app):
    with app.test_client() as c:
        #TODO: this should not raise, but set 4xx response code
        with pytest.raises(InvalidRouteTagFormat):
            resp = c.get('/routes/config/_Invalid_$Route_#name')
        #data = json.loads(resp.data)
        #assert resp.status_code == 500


def test_notinservice_all(mock_get_request, app):

    expected = {"notinservice": ["E", "KT"]}

    with app.test_client() as c:
        resp = c.get('/routes/notinservice?time=1473142292')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data == expected


def test_notinservice_single(mock_get_request, app):

    expected_E = {"notinservice": ["E"]}
    expected_L = {"notinservice": []}

    with app.test_client() as c:
        resp = c.get('/routes/notinservice/E?time=1473142292')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data == expected_E

    with app.test_client() as c:
        resp = c.get('/routes/notinservice/L?time=1473142292')
        data = json.loads(resp.data)
        assert resp.status_code == 200
        assert data == expected_L


def test_route_config_list_obj():
    nrcl = NextbusRouteConfigList()

    nrc1 = NextbusRouteConfig()
    nrc2 = NextbusRouteConfig()
    nrc3 = NextbusRouteConfig()

    for rc in [nrc1, nrc2, nrc3]:
        nrcl.add_route_config(rc)

    assert NextbusRouteConfigList(routes=[nrc1, nrc2, nrc3])



def test_route_schedule_prediction_obj():
    nrsp = NextbusRouteSchedulePrediction("00:00", tag='tag', epochTime=666)
    assert nrsp.get('time') == "00:00"
    assert nrsp.get('tag') == 'tag'
    assert nrsp.get('epochTime') == 666


def test_route_schedule_block_obj():
    nrsb = NextbusRouteScheduleBlock([], blockID="xxx")
    assert nrsb.get('blockID') == "xxx"
    assert nrsb.get('stop_prediction') == []


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


def test_repr_and_str():
    p = NextbusPoint(lat="0.0", lon="1.1")
    assert repr(p) == "NextbusPoint(lat='0.0', lon='1.1')"
    assert str(p) == "NextbusPoint(lat='0.0', lon='1.1')"
