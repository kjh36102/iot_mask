from SocketConnection import SocketServer, local_ip

print('Device ip:', local_ip())

my_server = SocketServer(port=20000)

my_server.start()

try:
    while True:
        message = input()
        my_server.send(message, '192.168.0.8')
        pass
except KeyboardInterrupt:
    pass