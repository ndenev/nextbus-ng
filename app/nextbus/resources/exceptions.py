
class NextbusNgBaseException(Exception):
    pass


class InvalidRouteTagFormat(NextbusNgBaseException):
    pass


class ResourceNotFound(NextbusNgBaseException):
    pass
