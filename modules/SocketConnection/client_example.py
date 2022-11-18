from SocketConnection import SocketClient, local_ip

print('Device ip:', local_ip())

socket_client = SocketClient(host='192.168.0.13', port=20000)

socket_client.start()

try:
    while True:
        message = input()
        socket_client.send(message)
        pass
except KeyboardInterrupt:
    pass
