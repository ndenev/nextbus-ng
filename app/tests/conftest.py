import os
import sys
import socket
import pytest

from flask import Flask
from flask_restful import Api
from flask_cache import Cache

from mockredis import mock_redis_client

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)+"/.."))
from nextbus.common.nextbusapi import NextbusApiClient
from nextbus.errors import api_error_map


def sucket(*args, **kwargs):
    raise Exception("No network access during testing!")

socket.socket = sucket


@pytest.fixture
def app(monkeypatch):
    mock_app = Flask(__name__)
    mock_app.api = Api(mock_app,
                       prefix='/api/v1',
                       errors=api_error_map,
                       catch_all_404s=True)
    mock_app.config['CACHE_TYPE'] = 'simple'
    mock_app.cache = Cache(mock_app)
    mock_app.testing = True
    mock_app.debug = True

    from nextbus.router import setup_router
    setup_router(mock_app)
    mock_app.stats_redis = mock_redis_client()
    mock_app.nextbus_api = NextbusApiClient()

    return mock_app
