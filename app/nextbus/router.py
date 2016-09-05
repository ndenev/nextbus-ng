import re
from datetime import datetime

from werkzeug.routing import BaseConverter
from nextbus.resources import Agency, Routes, RouteConfig, \
                              RouteSchedule, StopPredictions, \
                              ApiStats, ApiRoot, ApiSlowLog, NotInService
from nextbus.resources.exceptions import InvalidRouteTagFormat


class RouteTagConverter(BaseConverter):
    _re = re.compile(r'^[0-9A-Z_]+$')

    def to_python(self, value):
        if not self._re.match(value):
            raise InvalidRouteTagFormat
        return value


class EpochTimeConverter(BaseConverter):
    def to_python(self, value):
        return datetime.fromtimestamp(float(value))


def setup_routing_converters(app):
    app.url_map.converters['route_tag'] = RouteTagConverter
    app.url_map.converters['epoch_time'] = EpochTimeConverter


def setup_router(app):
    setup_routing_converters(app)
    app.api.add_resource(ApiRoot, '/')
    app.api.add_resource(ApiStats, '/stats')
    app.api.add_resource(ApiSlowLog, '/stats/slowlog')
    app.api.add_resource(Agency, '/agency')
    app.api.add_resource(Routes, '/routes')
    app.api.add_resource(RouteConfig, '/routes/config',
                                      '/routes/config/<route_tag:tag>')
    """ Route schedule endpoint. """
    app.api.add_resource(RouteSchedule, '/routes/schedule',
                                        '/routes/schedule/<route_tag:tag>')
    app.api.add_resource(NotInService, '/routes/notinservice',
                                       '/routes/notinservice/<route_tag:tag>')
    app.api.add_resource(StopPredictions, '/predictions')
