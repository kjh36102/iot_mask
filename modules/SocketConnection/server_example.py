from SocketConnection import SocketServer

my_server = SocketServer(20000)

my_server.start()

try:
    while True:
        message = input('>> ')
        my_server.send(message)
        pass
except KeyboardInterrupt:
    pass
