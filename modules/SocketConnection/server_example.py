from SocketConnection import SocketServer, local_ip

print('장치 ip:', local_ip())

my_server = SocketServer(port=20000)

my_server.start()

try:
    while True:
        message = input()
        my_server.send(message, 'desktop')
        my_server.send(message, 'laptop')
        pass
except KeyboardInterrupt:
    pass