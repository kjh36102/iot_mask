import socket
import threading
import time

def local_ip() -> str:
    '''
    접속된 local ip 를 리턴하는 함수
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 0))
    return s.getsockname()[0]

class __SocketConnection(threading.Thread):
    def __init__(self, host, port, debug):
        super().__init__(daemon=True)

        self.host = host
        self.port = port
        self.debug = debug

        self.my_ip = local_ip()
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connections = {}
        self.receive_buffer = []
        self.stop_flag = False
    
    def __del__(self):
        self.stop()
        self.my_socket.close()

    def start(self):
        self.stop_flag = False
        super().start()

    def stop(self):
        self.stop_flag = True
    
    def send(self, data:str, target_ip:str) -> bool:
        '''
        목표에게 데이터를 전송하는 함수
        Args
            data: 전송할 데이터
            target_ip: 목표의 IP주소
        '''
        try:
            self.connections[target_ip][0].sendall(data.encode())
            return True
        except KeyError:
            self._log(f'전송 실패! {target_ip} 은(는) 오프라인 입니다.')

        return False
    
    def broadcast(self, data):
        '''
        연결된 모든 장치에게 데이터를 전송하는 함수
        '''
        for target_ip in self.connections:
            target_socket = self.connections[target_ip]
            if target_socket == None:
                self.my_socket.sendall(f'{chr(0)}/BRIDGE/{self.my_ip}/{target_ip}/{data}'.encode())
            else:
                target_socket[0].sendall(data.encode())

    def _receive(self, sender_ip):
        sender_socket = self.connections[sender_ip][0]

        try:
            while True:
                data = sender_socket.recv(128)
                if not data: break

                decoded = data.decode()

                if decoded[0] != chr(0):
                    self.receive_buffer.append((sender_ip, self.my_ip, decoded))
                    self._log(f'[{sender_ip} -> {self.my_ip}]: {decoded}')
                elif len(decoded) > 1:
                    self._receive_action(decoded)

        except ConnectionResetError:
            self.connections.pop(sender_ip)
            self.broadcast(f'{chr(0)}/LEFT/{sender_ip}')    #퇴장 알리기

            self._log(f'{sender_ip} 에서 연결을 끊었습니다.')
            self._log(f'접속자 수: {len(self.connections)}')
    
    def _receive_action(self, decoded):
        pass

    def next(self) -> tuple:
        '''
        수신 버퍼에서 다음 패킷을 가져오는 함수
        Return
            tuple(보낸 IP, 받는 IP, 데이터)
        '''
        try:
            return self.receive_buffer.pop(0)
        except IndexError:
            return None
    
    def connectors(self) -> list:
        '''
        연결된 장치들의 IP주소 리스트를 반환하는 함수
        Return
            IP주소 리스트
        '''
        return list(self.connections.keys())

    def _log(self, message):
        if self.debug == True:
            print(f'[{time.strftime("%H:%M:%S", time.localtime(time.time()))}]  {message}')

class SocketServer(__SocketConnection):
    def __init__(self, port:int, debug:bool=False):
        '''
        SocketServer의 생성자
        Args
            port: 포트번호
            debug: 디버그 여부
        '''
        super().__init__(host=None, port=port, debug=debug)
        self.host = local_ip()

    def __del__(self):
        super().__del__()

    def run(self):
        self.__create_server()

        while not self.stop_flag:
            self.__accept_connection()

    def __create_server(self):
        try:
            self.my_socket.bind((self.host, self.port))
        except Exception as e:
            self._log(f'서버 생성 실패! {e}')
            return

        self.my_socket.listen(1)
        self._log(f'서버가 {self.my_ip} 에서 실행되었습니다.')

    def __accept_connection(self):
        connection = self.my_socket.accept()
        sender_socket = connection[0]
        sender_ip = connection[1][0]
        
        self._log(f'서버가 {sender_ip} 의 연결을 허용했습니다.')

        #접속자에게 목록 넘겨주기
        if len(self.connections) > 0:
            cmd = f'{chr(0)}/LIST/{"/".join(list(self.connections.keys()))}'
            sender_socket.sendall(cmd.encode())

        self.broadcast(f'{chr(0)}/JOIN/{sender_ip}')    #모두에게 입장 알리기

        self.connections[sender_ip] = (sender_socket, sender_ip)

        self._log(f'접속자 수: {len(self.connections)}')

        receive_th = threading.Thread(target=self._receive, args=(sender_ip, ))
        receive_th.daemon = True
        receive_th.start()

    def _receive_action(self, decoded):
        args = decoded.split(sep='/')

        if args[1] == 'BRIDGE':
            sender_ip = args[2]
            target_ip = args[3]
            data = args[4]
            self.send(f'{chr(0)}/BRIDGED/{sender_ip}/{data}', target_ip)
            self._log(f'[{sender_ip} -> {target_ip}]: {data}')

class SocketClient(__SocketConnection):
    def __init__(self, host, port, reconn_time=3, debug=False):
        '''
        SocketClient의 생성자
        Args
            host: 호스트 주소
            port: 포트 번호
            reconn_time: 재연결 사이클 단위시간
            debug: 디버그 여부
        Description
            재연결 사이클 생성시간은 호스트와 연결이 끊길 때 재연결을 시도하는 시간 간격
        '''
        super().__init__(host, port, debug)

        self.reconn_time = reconn_time
        self.connect_state = False

    def __del__(self):
        super().__del__()

    def run(self):
        while not self.stop_flag:
            while not self.connect_state:
                self.__connect_host()
            
            time.sleep(self.reconn_time) #연결 끊겼는지 reconnect_time마다 확인
            try:
                self.send(chr(0), self.host) #chr(0)은 ping에 사용되는 코드
            except ConnectionAbortedError:
                self._log(f'호스트 {self.host} 와(과)의 연결이 끊겼습니다.')
                self.connect_state = False
                self.my_socket.close()

                #접속자목록 초기화
                self.connections.clear()
    
    def __connect_host(self):
        try:
            self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.my_socket.connect((self.host, self.port))
            self.connections[self.host] = (self.my_socket, self.host)
        except ConnectionRefusedError:
            self._log(f'호스트 {self.host} 으(로)부터 연결이 거부되었습니다. 서버가 열려있는지 또는 동일 네트워크에 연결되어있는지 확인하십시오.')
            return
            
        self._log(f'호스트 {self.host} 에 연결되었습니다.')
        self.connect_state = True

        receive_th = threading.Thread(target=self._receive, args=(self.host,))
        receive_th.daemon = True
        receive_th.start()

    def _receive_action(self, decoded):
        args = decoded.split(sep='/')

        if args[1] == 'BRIDGED':
            sender_ip = args[2]
            data = args[3]
            self._log(f'[{sender_ip}]: {data}')
            self.receive_buffer.append((sender_ip, self.my_ip, data))
        elif args[1] == 'JOIN':
            self.connections[args[2]] = None
            self._log(f'{args[2]} 이(가) 통신에 참가했습니다.')
        elif args[1] == 'LEFT':
            self.connections.pop(args[2])
            self._log(f'{args[2]} 이(가) 통신을 종료했습니다.')
        elif args[1] == 'LIST':
            join_list = args[2:]
            for who in join_list:
                self.connections[who] = None

    def send(self, data, target_ip):
        try:
            target_socket = self.connections[target_ip]
        except KeyError:
            self._log(f'전송 실패! {target_ip} 은(는) 오프라인입니다.')
            return False

        if target_socket == None:
            #포워딩 요청
            self.my_socket.sendall(f'{chr(0)}/BRIDGE/{self.my_ip}/{target_ip}/{data}'.encode())
        else:
            super().send(data, target_ip)
        
        return True