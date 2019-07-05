import selectors
import socket
import pickle

selector = selectors.DefaultSelector()


def accept(sock, mask):
    connection, address = sock.accept()
    print('accepted from', address)
    connection.setblocking(False)
    selector.register(connection, selectors.EVENT_READ, read)


def read(connection, mask):
    client_address = connection.getpeername()
    data = connection.recv(1024)
    if data:
        print(f'...received {pickle.loads(data)} from {client_address}')

    else:
        print('...closing', connection)
        selector.unregister(connection)
        connection.close()


server_address = (socket.gethostname(), 1066)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(False)
server.bind(server_address)
server.listen(5)


def run():
    selector.register(server, selectors.EVENT_READ | selectors.EVENT_WRITE,
                      accept)
    while True:
        for key, mask in selector.select(timeout=1):
            callback = key.data
            callback(key.fileobj, mask)


try:
    run()
except KeyboardInterrupt:
    print('shutting down the server')
