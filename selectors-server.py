#!/usr/bin/python3

from encryption import Encryption
import pickle
import selectors
import socket
import sys
import sqlite3
import threading


class Server:
    def __init__(self, host: str, port: int):
        self.server_address = (host, port)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.selector = selectors.DefaultSelector()
        self.encryption = Encryption()

    def configure_server(self):
        self.server_socket.setblocking(False)
        self.server_socket.bind(self.server_address)
        self.server_socket.listen(100)
        self.selector.register(fileobj=self.server_socket,
                               events=selectors.EVENT_READ,
                               data=self.accept)

    def accept(self, sock, mask):
        connection, address = sock.accept()
        print('accepted from', address)
        connection.setblocking(False)
        self.selector.register(fileobj=connection,
                               events=selectors.EVENT_READ,
                               data=self.identify_user)

    def identify_user(self, connection, mask):
        try:
            data = pickle.loads(connection.recv(256))
            if data:
                operation, username, password = data
                if operation == 'login':
                    self.login_user(username, password)
                elif operation == 'register':
                    self.register_user(username, password)
            else:
                self.close_connection(connection)
        except ConnectionRefusedError:
            self.close_connection(connection)

    def register_user(self, username, password):
        print('sign up new user...')

    def login_user(self, username, password):
        print('logging existing user...')

    def close_connection(self, connection):
        self.selector.unregister(connection)
        connection.close()

    # def read(self, connection, mask):
    #     try:
    #         data = connection.recv(1024)
    #         client_address = connection.getpeername()
    #         if data:
    #             print(f'Received {data} from {client_address}')
    #         else:
    #             self.close_connection(connection)
    #     except ConnectionResetError:
    #         self.close_connection(connection)

    def run(self):
        while True:
            events = self.selector.select(timeout=1)
            for key, mask in events:
                handler = key.data
                handler(key.fileobj, mask)


try:
    if len(sys.argv) != 3:
        print('Usage: python3 script.py <hostname> <port>')
        sys.exit(1)
    else:
        server = Server(str(sys.argv[1]), int(sys.argv[2]))
        server.configure_server()
        server.run()
except KeyboardInterrupt:
    print('\nshutting down the server...')
