import selectors
import socket
import queue

selector = selectors.DefaultSelector()
message_queue = {}


def accept(sock, mask):
    connection, address = sock.accept()
    print('accepted from', address)
    connection.setblocking(False)
    selector.register(connection, selectors.EVENT_READ, read)


def read(connection, mask):
    client_address = connection.getpeername()
    data = connection.recv(1024)
    if data:
        print(f'...received {data} from {client_address}')
        message_queue[connection] = queue.Queue()

    else:
        print('...closing', connection)
        selector.unregister(connection)
        connection.close()


server_address = (socket.gethostname(), 10000)
print('starting on {} port {}'.format(*server_address))
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(False)
server.bind(server_address)
server.listen(5)

selector.register(server, selectors.EVENT_READ, accept)
while True:
    for key, mask in selector.select(timeout=1):
        callback = key.data
        callback(key.fileobj, mask)
