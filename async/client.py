#!/usr/bin/python3

import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (socket.gethostname(), 1024)
sock.connect(server_address)

try:
    message = input()
    sock.sendall(message.encode())
    amount_received = 0
    amount_expected = len(message)

    while amount_received < amount_expected:
        data = sock.recv(16)
        amount_received += len(data)

finally:
    sock.close()