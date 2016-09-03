import socket

def sucket(*args, **kwargs):
    raise Exception("No network access during testing!")

socket.socket = sucket
