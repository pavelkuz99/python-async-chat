#!/usr/bin/python3

from passlib.context import CryptContext
import pickle
import selectors
import socket
import sys
import threading


class Encryption(CryptContext):
    def __init__(self):
        super().__init__(schemes=["pbkdf2_sha256"],
                         default="pbkdf2_sha256",
                         bkdf2_sha256__default_rounds=30000)

    def encrypt_password(self, password):
        return self.encrypt(password)

    def check_encrypt_password(self, password, hashed):
        return self.verify(password, hashed)


class Server:
    def __init__(self, host: str, port: int):
        self.server_address = (host, port)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.selector = selectors.DefaultSelector()

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
        data = connection.recv(256)
        if data == b'register_user':
            self.register_user(connection)
        if data == b'login_user':
            self.login_user(connection)

    def register_user(self, connection):
        pass

    def login_user(self, connection):
        print('lets login')

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
