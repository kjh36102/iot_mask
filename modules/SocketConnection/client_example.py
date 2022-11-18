from SocketConnection import SocketConnection

socket_client = SocketConnection(host='192.168.0.13', port=20000)

socket_client.start()

try:
    while True:
        message = input('>> ')
        socket_client.send(message)
        pass
except KeyboardInterrupt:
    pass
