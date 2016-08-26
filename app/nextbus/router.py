from nextbus import app

import time
import string
import random

from flask import Flask
from flask_restful import Resource, Api
from flask_cache import Cache

from nextbus.common.config import APP_CONFIG
from nextbus.resources import NextBus, NextBusCached

app.api.add_resource(NextBus, '/')
app.api.add_resource(NextBusCached, '/cached')
