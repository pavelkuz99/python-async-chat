#!/usr/bin/python3

import socket
import pickle

server_address = (socket.gethostname(), 1066)

socks = [socket.socket(socket.AF_INET, socket.SOCK_STREAM),
         socket.socket(socket.AF_INET, socket.SOCK_STREAM)]

for sock in socks:
    sock.connect(server_address)
    with sock:
        message = {'destination': 'message'}
        output = pickle.dumps(message)
        sock.send(output)
