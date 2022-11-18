#서버 생성 및 일반 입력은 데이터 보내기, !next 입력은 수신버퍼에서 하나씩 꺼내오는 예시코드

from SocketConnection import SocketServer, local_ip

print('장치 ip:', local_ip())   #실행 장치의 ip출력

my_server = SocketServer(port=20000, debug=True)
my_server.start()

try:
    while True:
        message = input()

        if message == '!next':  #!next를 입력하면 수신 버퍼에서 가져와 출력함
            print('next message:', my_server.next())
        else:
            my_server.send(message, 'desktop')  #일반 입력은 메시지 보내기

except KeyboardInterrupt:
    pass