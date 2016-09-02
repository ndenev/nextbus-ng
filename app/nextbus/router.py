from nextbus.resources import Agency, Routes, RouteConfig


def setup_router(app):
    app.api.add_resource(Agency, '/agency')
    app.api.add_resource(Routes, '/route')
    app.api.add_resource(RouteConfig, '/route/config', '/route/config/<tag>')
