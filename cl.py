import socket, select, string, sys


def prompt():
    sys.stdout.write('<You> ')
    sys.stdout.flush()


if __name__ == "__main__":

    if len(sys.argv) < 3:
        print('Usage : python cl.py hostname port')
        sys.exit()

    host = sys.argv[1]
    port = int(sys.argv[2])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)

    try:
        s.connect((host, port))
    except:
        print('Unable to connect')
        sys.exit()

    print('Connected to remote host. Start sending messages')
    prompt()

    while 1:
        socket_list = [sys.stdin, s]
        read_sockets, write_sockets, error_sockets = select.select(socket_list, [], [])

        for sock in read_sockets:
            if sock == s:
                data = sock.recv(4096)
                if not data:
                    print('\nDisconnected from chat server')
                    sys.exit()
                else:
                    sys.stdout.write(data)
                    prompt()

            else:
                msg = sys.stdin.readline()
                s.send(msg)
                prompt()
