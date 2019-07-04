#!/usr/bin/python3

import selectors
import socket

selector = selectors.DefaultSelector()

server_address = (socket.gethostname(), 10000)
print('connecting to {} port {}'.format(*server_address))

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(server_address)
sock.setblocking(False)

selector.register(
    sock,
    selectors.EVENT_READ | selectors.EVENT_WRITE,
)

try:
    while True:
        for key, mask in selector.select(timeout=1):
            connection = key.fileobj
            client_address = connection.getpeername()

            if mask & selectors.EVENT_READ:
                data = connection.recv(1024)
                if data:
                    print(f'Received: {data}')

            if mask & selectors.EVENT_WRITE:
                print('Enter message:')
                outgoing = input()
                if not outgoing:
                    selector.modify(sock, selectors.EVENT_READ)
                else:
                    print(f'Sending: {outgoing}')
                    sock.send(str.encode(outgoing))
finally:
    selector.unregister(connection)
    connection.close()
    selector.close()
