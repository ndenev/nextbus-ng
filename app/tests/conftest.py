import socket

def sucket(*args, **kwargs):
    raise Exception("No internet access during testing!")

socket.socket = sucket
