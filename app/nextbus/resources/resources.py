import time
import string
import random

from flask_restful import Resource

from nextbus import app
#from nextbus.common.nextbusapi import NextbusApiClient


class NextBus(Resource):
    def get(self):
        return {'hello': 'world'}

class NextBusCached(Resource):
    @app.cache.memoize(30)
    def get(self):
        time.sleep(2)
        return {'random': ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(32))}
    def __repr__(self):
        return "NextBusCached"


