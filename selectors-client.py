#!/usr/bin/python3

from getpass import getpass
import selectors
import socket
import sys


class Client:
    def __init__(self, host: str, port: int):
        self.server_address = (host, port)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.selector = selectors.DefaultSelector()

    def connect_to_server(self):
        self.client_socket.connect(self.server_address)
        self.client_socket.setblocking(False)
        print('connecting to {} port {}'.format(*self.server_address))
        self.selector.register(self.client_socket,
                               selectors.EVENT_READ | selectors.EVENT_WRITE, )

    def read(self, connection):
        data = connection.recv(1024)
        if data:
            print(f'Received: {data}')

    def identify_user(self):
        choice = input('1 - sign up; 2 - login:  ')
        if int(choice) == 1:
            self.write('register_user')
        elif int(choice) == 2:
            self.write('login_user')
        else:
            self.enter_credentials()

    def enter_credentials(self):
        username = input('Enter username:  ')
        password = getpass()
        self.write((username, password))

    def write(self, outgoing=None):
        if not outgoing:
            self.selector.modify(self.client_socket, selectors.EVENT_READ)
        else:
            print(f'Sending: {outgoing}')
            self.client_socket.send(str.encode(str(outgoing)))

    def close_connection(self, connection):
        self.selector.unregister(connection)
        connection.close()
        self.selector.close()

    def run(self):
        try:
            while True:
                for key, mask in self.selector.select(timeout=1):
                    connection = key.fileobj
                    client_address = connection.getpeername()
                    if mask & selectors.EVENT_READ:
                        self.read(connection)
                    if mask & selectors.EVENT_WRITE:
                        self.write()
        except ConnectionRefusedError:
            print('Cant connect to server')
        finally:
            self.close_connection(connection)


if __name__ == "__main__":
    try:
        if len(sys.argv) != 3:
            print('Usage: python3 script.py <hostname> <port>')
            sys.exit(1)
        else:
            client = Client(str(sys.argv[1]), int(sys.argv[2]))
            client.connect_to_server()
            client.identify_user()
            client.run()
    except KeyboardInterrupt:
        print('\nshutting down the client...')





