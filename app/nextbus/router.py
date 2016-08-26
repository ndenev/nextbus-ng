from nextbus import app

import time
import string
import random

from flask import Flask
from flask_restful import Resource, Api
from flask_cache import Cache

from nextbus.common.config import APP_CONFIG
from nextbus.resources import Agency, Routes, RouteConfig

app.api.add_resource(Agency, '/agency')
app.api.add_resource(Routes, '/routes')
app.api.add_resource(RouteConfig, '/routes/config')
