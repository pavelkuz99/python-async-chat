#!/usr/bin/python3

from getpass import getpass
import pickle
import select
import selectors
import socket
import sys


class Client:
    def __init__(self, host: str, port: int):
        self.logged_in = False
        self.server_address = (host, port)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.settimeout(2)
        self.selector = selectors.DefaultSelector()

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

    def choose_auth_operation(self):
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

    def close_connection(self, connection):
        if not self.logged_in:
            self.selector.unregister(connection)
        connection.close()
        self.selector.close()

    def read(self, connection):
        data = connection.recv(1024)
        if data:
            # print(f'Received: {pickle.loads(data)}')
            return pickle.loads(data)

    def write(self, outgoing=None):
        if outgoing:
            self.client_socket.send(pickle.dumps(outgoing))

    def authorize(self):
        while True:
            for key, mask in self.selector.select(timeout=1):
                connection = key.fileobj
                if not self.logged_in:
                    if mask & selectors.EVENT_READ:
                        server_response = self.read(connection)
                        self.logged_in = server_response['flag']
                        print(server_response['verbose'])
                        self.selector.modify(self.client_socket, 
                                            selectors.EVENT_WRITE)
                    elif mask & selectors.EVENT_WRITE:
                        self.write(self.choose_auth_operation())
                else:
                    return True

    @staticmethod
    def prompt(user=None, message=None):
        if user:
            sys.stdout.write(f"\r<{user.getpeername()}> {message}\n<You> ")
        else:
            sys.stdout.write(f'<You> ')
        sys.stdout.flush()

    
    def run(self):
        self.prompt()
        while 1:
            streams = [sys.stdin, self.client_socket]
            readable, writable, err = select.select(streams, [], [])
            for sock in readable:
                if sock == self.client_socket:
                    data = sock.recv(1024)
                    if data:
                        self.prompt(sock, pickle.loads(data))
                    
                else:
                    message = sys.stdin.readline().rstrip()
                    self.client_socket.send(pickle.dumps(message))
                    if message == 'quit':
                        sys.exit(1)
                    else:
                        self.prompt()


if __name__ == "__main__":
    try:
        if len(sys.argv) != 3:
            print('Usage: python3 script.py <hostname> <port>')
            sys.exit(1)
        else:
            client = Client(str(sys.argv[1]), int(sys.argv[2]))
            client.connect_to_server()
            if client.authorize():
                client.run()
    except KeyboardInterrupt:
        print('\nshutting down the client...')
