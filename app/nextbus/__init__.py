import logging

from flask import Flask
from flask_restful import Api
from flask_cache import Cache
from redis import Redis

from nextbus.common.config import APP_CONFIG, REDIS_CONFIG
from nextbus.errors import api_error_map

__author__ = "ndenev@gmail.com"


app = Flask(__name__)
app.cache = Cache(app, config=APP_CONFIG['flask_cache_config'])
app.api = Api(app, default_mediatype='text/json',
              errors=api_error_map)
app.stats_redis = Redis(host=REDIS_CONFIG['redis_host'],
                        port=REDIS_CONFIG['redis_port'],
                        password=REDIS_CONFIG['redis_pass'],
                        db=1)


@app.before_first_request
def setup_logging():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    logger.addHandler(handler)
    app.logger.addHandler(handler)
    if app.debug:
        app.logger.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

#
# Modules that need to import "app" are loaded after this line.
#

from nextbus.router import setup_router
from nextbus.common.nextbusapi import NextbusObjectSerializer

app.config.update({'RESTFUL_JSON': {'separators': (', ', ': '),
                                    'indent': 2,
                                    'cls': NextbusObjectSerializer}})

setup_router(app)
