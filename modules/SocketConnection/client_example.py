#클라이언트 실행 및 일반 입력은 데이터 보내기, !next 입력은 수신버퍼에서 하나씩 꺼내오는 예시코드

from SocketConnection import SocketClient, local_ip

print('장치 ip:', local_ip())   #실행 장치의 ip출력

socket_client = SocketClient(host='192.168.0.5', port=20000, debug=True)
socket_client.start()

try:
    while True:
        msg = input() 

        if msg == '!next':  #!next를 입력하면 수신 버퍼에서 가져와 출력함
            print('next message:', socket_client.next())
        elif msg == '!list':    #!list를 입력하면 현재 접속된 주소를 반환함
            print('who connected: ', socket_client.connectors())
        else:
            socket_client.send(msg, target_ip='192.168.0.5') #타겟 주소로 메시지 전송

except KeyboardInterrupt:
    pass
