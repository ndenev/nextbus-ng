import logging

from flask import Flask
from flask_restful import Api
from flask_cache import Cache

from nextbus.common.config import APP_CONFIG

__author__ = "ndenev@gmail.com"


app = Flask(__name__)
app.cache = Cache(app, config=APP_CONFIG['flask_cache_config'])
app.api = Api(app)
app.logger.setLevel(logging.DEBUG)

from nextbus.router import setup_router
from nextbus.common.nextbusapi import NextbusObjectSerializer

app.config.update({'RESTFUL_JSON': {'separators': (', ', ': '),
                                    'indent': 2,
                                    'cls': NextbusObjectSerializer}})

setup_router(app)

