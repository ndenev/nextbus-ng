import logging

from flask import Flask
from flask_restful import Api
from flask_cache import Cache
from redis import Redis

from nextbus.common.config import APP_CONFIG, REDIS_CONFIG
from nextbus.errors import api_error_map
from nextbus.common.nextbusapi import NextbusApiClient

__author__ = "ndenev@gmail.com"

__all__ = ['create_app']

def setup_logging(app):
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    logger.addHandler(handler)
    #app.logger.addHandler(handler)
    if app.debug:
        app.logger.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    else:
        app.logger.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)


def create_app(config=None, environment=None):
    app = Flask(__name__)
    app.config['ENVIRONMENT'] = environment
    app.config.update(config or {})

    app.api = Api(app, errors=api_error_map)

    app.cache = Cache(app, config=APP_CONFIG['flask_cache_config'])

    app.stats_redis = Redis(host=REDIS_CONFIG['redis_host'],
                            port=REDIS_CONFIG['redis_port'],
                            password=REDIS_CONFIG['redis_pass'],
                            db=1)
    setup_logging(app)
    app.nextbus_api = NextbusApiClient(agency='sf-muni')
    from nextbus.router import setup_router
    setup_router(app)

    from nextbus.common.nextbusapi import NextbusObjectSerializer
    app.config.update({'RESTFUL_JSON': {'separators': (', ', ': '),
                                        'indent': 2,
                                        'cls': NextbusObjectSerializer}})
    from nextbus.resources import teardown_request
    app.teardown_request(teardown_request)
    
    return app
