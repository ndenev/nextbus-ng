import time
import string
import random

from flask_restful import Resource

from nextbus import app
from nextbus.common.nextbusapi import NextbusApiClient



class Agency(Resource):
    def get(self):
        nb_api = NextbusApiClient()
        return nb_api.agency_list()

class Routes(Resource):
    def get(self):
        nb_api = NextbusApiClient()
        return nb_api.route_list()

class RouteConfig(Resource):
    def get(self, route_tag=None):
        nb_api = NextbusApiClient()
        return nb_api.route_config(route_tag)

