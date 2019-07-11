#!/usr/bin/python3

from getpass import getpass
import pickle
import re
import selectors
import socket
import sys


class Client:
    def __init__(self, host: str, port: int):
        self.logged_in = False
        self.server_address = (host, port)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.selector = selectors.DefaultSelector()

    @staticmethod
    def prompt():
        sys.stdout.write('<You> ')
        sys.stdout.flush()

    def connect_to_server(self):
        try:
            self.client_socket.connect(self.server_address)
            self.client_socket.setblocking(False)
            print('connecting to {} port {}'.format(*self.server_address))
        except ConnectionRefusedError:
            print(f'Can\'t connect to server {self.server_address}')
            sys.exit(1)
        self.selector.register(self.client_socket,
                               selectors.EVENT_READ,)
        self.selector.register(sys.stdin,
                               selectors.EVENT_WRITE)

    def read(self, connection):
        data = connection.recv(1024)
        if data:
            # print(f'Received: {pickle.loads(data)}')
            self.selector.modify(self.client_socket, selectors.EVENT_WRITE)
            return pickle.loads(data)

    def write(self, outgoing=None):
        if outgoing:
            # print(f'Sending: {outgoing}')
            self.client_socket.send(pickle.dumps(outgoing))

    def identify_user(self):
        choice = ''
        while choice not in ['1', '2']:
            choice = input('Enter 1 - to sign up, 2 - to log in\n: ')
        if choice == '1':
            return self.handle_credentials('register')
        elif choice == '2':
            return self.handle_credentials('login')

    def handle_credentials(self, operation_type):
        username = input('Enter username: ')
        password = getpass('Enter password: ')
        if not self.logged_in:
            self.selector.modify(self.client_socket, selectors.EVENT_READ)
        return operation_type, username, password

    @staticmethod
    def route_message(message):
        splited_message = re.search('@(.*?)\s(.*)', message)
        user, message = splited_message.group(1), splited_message.group(2)
        return user,message

    def close_connection(self, connection):
        self.selector.unregister(connection)
        connection.close()
        self.selector.close()

    def run(self):
        while True:
            for key, mask in self.selector.select(timeout=1):
                connection = key.fileobj
                if mask & selectors.EVENT_READ:
                    if not self.logged_in:
                        server_response = self.read(connection)
                        self.logged_in = server_response['flag']
                        print(server_response['verbose'])
                    else:
                        self.read(connection)
                elif mask & selectors.EVENT_WRITE:
                    if not self.logged_in:
                        self.write(self.identify_user())
                    else:
                        message = input('<You>: ')
                        if message == 'quit':
                            self.write(message)
                            self.close_connection(connection)
                            sys.exit(0)
                        self.write(message)


if __name__ == "__main__":
    try:
        if len(sys.argv) != 3:
            print('Usage: python3 script.py <hostname> <port>')
            sys.exit(1)
        else:
            client = Client(str(sys.argv[1]), int(sys.argv[2]))
            client.connect_to_server()
            client.run()
    except KeyboardInterrupt:
        print('\nshutting down the client...')
