#!/usr/bin/python3

from encryption import Encryption
import pickle
import selectors
import socket
import sys
import sqlite3
import threading


class UserDatabase:
    def __init__(self, db_file):
        self.db_connection = sqlite3.connect(db_file)
        self.create_users_table()

    def handle_sql_query(self, *args):
        try:
            c = self.db_connection.cursor()
            c.execute(*args)
        except sqlite3.Error as e:
            print(f'DATABASE ERROR: {e}')

    def create_users_table(self):
        query = """ CREATE TABLE 
                    IF NOT EXISTS users (
                        id integer PRIMARY KEY,
                        username text NOT NULL UNIQUE,
                        password text NOT NULL
                    );"""
        self.handle_sql_query(query)

    def add_user(self, username, password):
        query = "INSERT INTO users (username, password) VALUES (?, ?)"
        self.handle_sql_query(query, (username, password))
        self.db_connection.commit()

    def check_user(self, username):
        values = self.handle_sql_query(
            'SELECT username, password FROM users WHERE username=?',
            (username,)).fetchone()
        return bool(values)

    def get_password(self, username):
        return self.handle_sql_query(
            'SELECT password FROM users WHERE username=?',
            (username,)).fetchone()[0]


class Server:
    def __init__(self, host: str, port: int):
        self.server_address = (host, port)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.selector = selectors.DefaultSelector()
        self.database = UserDatabase('users.db')
        self.encryption = Encryption()

    def configure_server(self):
        self.server_socket.setblocking(False)
        self.server_socket.bind(self.server_address)
        self.server_socket.listen(100)
        self.selector.register(self.server_socket,
                               selectors.EVENT_READ,
                               self.accept)

    def accept(self, sock, mask):
        connection, address = sock.accept()
        print('accepted from', address)
        connection.setblocking(False)
        self.selector.register(connection,
                               selectors.EVENT_READ,
                               self.identify_user)

    def identify_user(self, connection, mask):
        try:
            data = pickle.loads(connection.recv(256))
            if data:
                operation, username, password = data
                print(password)
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
        if self.database.check_user(username):
            return f'{username} is already taken'
        else:
            self.database.add_user(username,
                                   self.encryption.encrypt_password(password))
            return f'{username} is successfully registered'

    def login_user(self, username, password):
        print('logging existing user...')
        if self.database.check_user(username):
            user_password = self.database.get_password(username)
            if self.encryption.check_password(password, user_password):
                return f'User {username} logged in'
        else:
            return f'No such user - {username}'

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
