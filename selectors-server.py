#!/usr/bin/python3

from encryption import Encryption
import logging
import pickle
import selectors
import socket
import sys
import sqlite3

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')


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
            """SELECT username, password 
               FROM users 
               WHERE username=?""", (username,)).fetchone()
        return bool(values)

    def get_password(self, username):
        return self.handle_sql_query(
            """SELECT password 
               FROM users 
               WHERE username=?""", (username,)).fetchone()[0]


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
            return self.auth_output(False, f'"{username}" is already taken')
        else:
            self.database.add_user(username,
                                   self.encryption.encrypt_password(password))
            return self.auth_output(True, f'"{username}" is registered')

    def login_user(self, username, password):
        if self.database.check_user(username):
            user_password = self.database.get_password(username)
            if self.encryption.check_password(password, user_password):
                return self.auth_output(True, f'"{username}", login success')
            else:
                return self.auth_output(False, 'Wrong password')
        else:
            return self.auth_output(True, f'No such user - "{username}"')

    @staticmethod
    def auth_output(flag, message):
        logging.info(message)
        return {'flag': flag, 'verbose': message}


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
        logging.info(f'Server is listening for incoming connections')
        self.selector.register(self.server_socket,
                               selectors.EVENT_READ,
                               self.accept)

    def accept(self, sock, mask):
        connection, address = sock.accept()
        logging.info(f'accepted connection from {address}')
        connection.setblocking(False)
        self.connections.append(address)
        self.selector.register(connection,
                               selectors.EVENT_READ,
                               self.handle_incoming_data)

    def close_connection(self, connection):
        logging.info(f'Connection {connection.getpeername()} is closing')
        self.connections.remove(connection.getpeername())
        self.selector.unregister(connection)
        connection.close()

    def handle_incoming_data(self, connection, mask):
        client_address = connection.getpeername()
        data = self.read(connection)
        if data == 'quit':
            logging.info(f'{client_address} has disconnected')
            self.close_connection(connection)
        elif isinstance(data, tuple) and data[0] in ('login', 'register'):
            connection.send(pickle.dumps(self.auth.identify_user(*data)))
        else:
            logging.info(f'Received "{data}" from {client_address}')

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

    def shutdown(self):
        pass


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
        logging.info('Shutting down the server...')
