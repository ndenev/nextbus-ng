__author__="ndenev@gmail.com"

from flask import Flask
from flask_restful import Api
from flask_cache import Cache

from .common.config import APP_CONFIG

app = Flask(__name__)
app.cache = Cache(app, config=APP_CONFIG['flask_cache_config'])
app.api = Api(app)

import router
