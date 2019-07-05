#!/usr/bin/env python3

import socket

HOST = socket.gethostname()
PORT = 1066

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b"Hello, world")
    data = s.recv(1024)

print("Received", repr(data))