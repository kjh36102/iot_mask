#클라이언트 실행 및 일반 입력은 데이터 보내기, !next 입력은 수신버퍼에서 하나씩 꺼내오는 예시코드

from SocketConnection import SocketClient, local_ip

print('장치 ip:', local_ip())   #실행 장치의 ip출력

socket_client = SocketClient(host='192.168.0.13', port=20000, name='desktop', debug=True)
socket_client.start()

try:
    while True:
        message = input()

        if message == '!next':  #!next를 입력하면 수신 버퍼에서 가져와 출력함
            print('next message:', socket_client.next())
        else:
            socket_client.send(message) #일반 입력은 메시지 보내기

except KeyboardInterrupt:
    pass
