#!/usr/bin/python3

import asyncio
import socket
import queue


class Server:
    def __init__(self):
        self.loop = asyncio.get_event_loop()

    def run(self):
        self.loop.create_task(self.create_conn((socket.gethostname(), 1024)))
        self.loop.run_forever()

    async def create_conn(self, address):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(address)
        server_socket.setblocking(False)
        server_socket.listen(10)
        while True:
            client, client_address = await self.loop.sock_accept(server_socket)
            self.loop.create_task(self.conn_handler(client))

    async def conn_handler(self, client):
        with client:
            client.sendall(b"Hello from server")
            while True:
                data = await self.loop.sock_recv(client, 1024)
                if not data:
                    break


server = Server()
server.run()
