import select
import socket
import sys
import queue


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(False)

server_address = ('localhost', 1024)
server.bind(server_address)
server.listen(10)

inputs, outputs, message_queues = [server], [], {}

while inputs:
    print('Waiting for the next event')
    readable, writable, exceptional = select.select(inputs, outputs, inputs)
    for s in readable:
        if s is server:
            connection, client_address = s.accept()
            print(f'New connection from {client_address}')
            connection.setblocking(False)
            inputs.append(connection)
            message_queues[connection] = queue.Queue()
        else:
            data = s.recv(1024)
            if data:
                print(f'Received {data} from {s.getpeername()}')
                message_queues[s].put(data)
                if s not in outputs:
                    outputs.append(s)
            else:
                if s in outputs:
                    outputs.remove(s)
                inputs.remove(s)
                s.close()
                del message_queues[s]

    for s in writable:
        try:
            next_msg = message_queues[s].get_nowait()
        except queue.Empty:
            print(f'Output que for {s.getpeername()} is empty')
            outputs.remove(s)
        else:
            print(f'Sending {next_msg} to {s.getpeername()}')
            s.send(next_msg)

    for s in exceptional:
        print(f'Handling exceptional condition for {s.getpeername()}')
        inputs.remove(s)
        if s in outputs:
            outputs.remove(s)
        s.close()
        del message_queues[s]
