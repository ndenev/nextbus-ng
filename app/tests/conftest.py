import socket
import redis
from mockredis import mock_redis_client, mock_strict_redis_client


def sucket(*args, **kwargs):
    raise Exception("No network access during testing!")

socket.socket = sucket

redis.Redis = mock_redis_client
redis.StrictRedis = mock_strict_redis_client
