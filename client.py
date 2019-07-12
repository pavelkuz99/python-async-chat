#!/usr/bin/python3

import pickle
import select
import selectors
import socket
import sys
from getpass import getpass


class ClientAuthentication:
    def __init__(self):
        pass

    def choose_auth_operation(self):
        choice = ''
        while choice not in ['1', '2']:
            choice = input('Enter 1 - to sign up, 2 - to log in\n: ')
        if choice == '1':
            return self.handle_credentials('register')
        elif choice == '2':
            return self.handle_credentials('login')

    @staticmethod
    def handle_credentials(operation_type):
        username = input('Enter username: ')
        password = getpass('Enter password: ')
        return operation_type, username, password


class Client:
    def __init__(self, host: str, port: int):
        self.logged_in = False
        self.server_address = (host, port)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(2)
        self.selector = selectors.DefaultSelector()
        self.auth = ClientAuthentication()

    def connect_to_server(self):
        try:
            self.client_socket.connect(self.server_address)
            self.client_socket.setblocking(False)
            print('connecting to {} port {}'.format(*self.server_address))
        except ConnectionRefusedError:
            print(f'Can\'t connect to server {self.server_address}')
            sys.exit(1)
        self.selector.register(self.client_socket,
                               selectors.EVENT_READ | selectors.EVENT_WRITE, )

    @staticmethod
    def read(connection):
        data = connection.recv(1024)
        if data:
            return pickle.loads(data)

    def write(self, outgoing=None):
        if outgoing:
            self.client_socket.send(pickle.dumps(outgoing))

    @staticmethod
    def check_for_shutdown(response):
        if isinstance(response, tuple) and response[1] == '[server shutdown]':
            sys.stdout.write(f'\r{response[1]}\n')
            sys.exit(1)

    def check_for_login(self, response):
        if isinstance(response, dict):
            self.logged_in = response['flag']
            print(response['verbose'])
            self.selector.modify(self.client_socket, selectors.EVENT_WRITE)

    def authorize(self):
        while True:
            for key, mask in self.selector.select(timeout=1):
                connection = key.fileobj
                if not self.logged_in:
                    if mask & selectors.EVENT_READ:
                        server_response = self.read(connection)
                        self.check_for_shutdown(server_response)
                        self.check_for_login(server_response)
                    elif mask & selectors.EVENT_WRITE:
                        self.write(self.auth.choose_auth_operation())
                        if not self.logged_in:
                            self.selector.modify(self.client_socket,
                                                 selectors.EVENT_READ)
                else:
                    self.selector.unregister(connection)
                    self.selector.close()
                    return True

    @staticmethod
    def prompt(sender=None, message=None):
        if sender:
            sys.stdout.write(f"\r<{sender}>: {message}\n<You>: ")
        else:
            sys.stdout.write(f'<You>: ')
        sys.stdout.flush()

    def run(self):
        self.prompt()
        self.write('[client connected]')
        try:
            while 1:
                streams = [sys.stdin, self.client_socket]
                readable, writable, err = select.select(streams, [], [])
                for sock in readable:
                    if sock == self.client_socket:
                        data = self.read(sock)
                        if data:
                            self.check_for_shutdown(data)
                            sender, message = data
                            self.prompt(sender, message)
                    else:
                        message = sys.stdin.readline().rstrip()
                        self.write(message)
                        if message == 'quit':
                            sys.exit(1)
                        else:
                            self.prompt()
        finally:
            self.client_socket.close()


if __name__ == "__main__":
    try:
        if len(sys.argv) != 3:
            print('Usage: python3 client.py <hostname> <port>')
            sys.exit(1)
        else:
            client = Client(str(sys.argv[1]), int(sys.argv[2]))
            client.connect_to_server()
            if client.authorize():
                client.run()
    except KeyboardInterrupt:
        print('\nshutting down the client...')
