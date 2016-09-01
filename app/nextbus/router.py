from nextbus import app

import time
import string
import random

from flask import Flask
from flask_restful import Resource, Api
from flask_cache import Cache

from nextbus.common.config import APP_CONFIG
from nextbus.resources import Agency, Routes, RouteConfig
#~, Predictions \
#                              MultiStopPredictions

_add = app.api.add_resource

_add(Agency, '/agency')

_add(Routes, '/routes')

#_add(RouteSchedule, '/routes/schedule'

_add(RouteConfig, '/routes/config', '/routes/config/<tag>')



"""

_add(Predictions, '/predictions')

# Optional Route or Routes
_add(Messages, '/messages

_add(VehicleLocations

# list agencies
/agency

# list routes
/routes

# routes configuration
/routes/config

# specific route tag configuration
/routes/config/<route_tag>


/stop
/predictions/

#
#/route/<route_tag_or_tags> -> ['config', '
#/route/<route_tag>/config

/route/<route_tag>/stop/predictions
"""
