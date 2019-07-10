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
            if len(args) == 1:
                return c.execute(args[0])
            elif len(args) == 2:
                return c.execute(args[0], args[1])
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


class UserAuthentication:
    def __init__(self, database):
        self.database = database
        self.encryption = Encryption()

    def identify_user(self, operation, username, password):
        if operation == 'login':
            return self.login_user(username, password)
        elif operation == 'register':
            return self.register_user(username, password)

    def register_user(self, username, password):
        if self.database.check_user(username):
            message = f'"{username}" is already taken'
            return {'flag': False, 'verbose': message}
        else:
            self.database.add_user(username,
                                   self.encryption.encrypt_password(password))
            message = f'"{username}" is successfully registered'
            return {'flag': True, 'verbose': message}

    def login_user(self, username, password):
        if self.database.check_user(username):
            user_password = self.database.get_password(username)
            if self.encryption.check_password(password, user_password):
                message = f'User "{username}" logged in'
                return {'flag': True, 'verbose': message}
            else:
                message = f'Wrong password for "{username}"'
                return {'flag': False, 'verbose': message}
        else:
            message = f'No such user - "{username}"'
            return {'flag': True, 'verbose': message}


class Server:
    def __init__(self, host: str, port: int):
        self.server_address = (host, port)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.selector = selectors.DefaultSelector()
        self.database = UserDatabase('users.db')
        self.auth = UserAuthentication(self.database)
        self.connections = []

    def configure_server(self):
        self.server_socket.setblocking(False)
        self.server_socket.bind(self.server_address)
        self.server_socket.listen(100)
        self.selector.register(self.server_socket,
                               selectors.EVENT_READ,
                               self.accept)

    def accept(self, sock, mask):
        connection, address = sock.accept()
        print('accepted connection from', address)
        connection.setblocking(False)
        self.connections.append(connection)
        self.selector.register(connection,
                               selectors.EVENT_READ,
                               self.handle_incoming_data)

    def close_connection(self, connection):
        self.selector.unregister(connection)
        connection.close()

    def handle_incoming_data(self, connection, mask):
        data = self.read(connection)
        is_authentication = (data[0] == 'login' or data[0] == 'register')
        if isinstance(data, tuple) and is_authentication:
            connection.send(pickle.dumps(self.auth.identify_user(*data)))

            # if :
            #     connection.send(pickle.dumps(True))
            # else:
            #     connection.send(pickle.dumps(False))
        else:
            print(f'Received {data} for {connection.getpeername()}')

    def read(self, connection):
        try:
            data = connection.recv(1024)
            if data:
                return pickle.loads(data)
            else:
                self.close_connection(connection)
        except ConnectionResetError:
            self.close_connection(connection)

    def run(self):
        while True:
            for key, mask in self.selector.select(timeout=1):
                handler = key.data
                handler(key.fileobj, mask)


if __name__ == "__main__":
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
