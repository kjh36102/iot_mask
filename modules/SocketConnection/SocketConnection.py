import socket
import threading
import time

class SocketServer(threading.Thread):
    def __init__(self, port:int, debug:bool=False):
        '''
        소켓통신 서버를 생성해주는 클래스
          Args
            port: 포트번호
            debug: 디버그 여부
          Example
            my_server = SocketServer(port=20000)\n
            my_server.start()
        '''
        super().__init__()
        self.daemon = True

        #-------------------------
        self.host = local_ip()
        self.port = port
        self.my_socket = None
        self.connections = {}
        self.receive_buffer = []
        self.stop_flag = False
        self.debug = debug
        #-------------------------

        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def __del__(self):
        self.my_socket.close()

    def run(self):
        self.create_server()

        while not self.stop_flag:
            self.accept_connection()

    def start(self) -> None:
        '''
        서버를 실행하는 함수, 스레드로 동작
        '''
        super().start()

    def stop(self):
        self.stop_flag = True

    def create_server(self):
        try:
            self.my_socket.bind((self.host, self.port))
        except socket.error as e:
            log('서버 생성 실패: bind()불가', self)

        self.my_socket.listen(1)
        log('서버가 클라이언트를 기다리는 중..', self)

    def accept_connection(self):
        conn = self.my_socket.accept()
        addr = conn[1][0]
        self.connections[addr] = conn
        log(f'서버가 {addr} 와(과) 연결되었습니다.', self)

        log(f'접속 수: {len(self.connections)}', self)

        receive_th = threading.Thread(target=receive, args=(self, addr, ))
        receive_th.daemon = True
        receive_th.start()

    def send(self, data:str, target:str) -> bool:
        '''
        클라이언트에게 데이터를 보내는 함수
            Args
                data: 보낼 데이터
                target: 받는 기기 이름
            Return
                성공시 True, 실패시 False
        '''
        try:
            self.connections[target][0].sendall(data.encode())
            return True
        except KeyError:
            log(f'{target} 는 존재하지 않는 접속자입니다.', self)
        return False
    
    def broadcast(self, data:str) -> None:
        '''
        모든 클라이언트에게 보내는 함수
            Args
                data: 보낼 데이터
        '''
        for connection in self.connections:
            connection[0].sendall(data.encode())
        

    def next(self) -> str:
        '''
        수신 버퍼에 대기중인 다음 데이터를 가져오는 함수
            Return
                str 데이터 or None
        '''
        try:
            return self.receive_buffer.pop(0)
        except IndexError:
            return None

class SocketClient(threading.Thread):
    def __init__(self, host:str, port:int, name:str, reconnect_time:int=3, debug:bool=False):
        '''
        소켓통신 클라이언트를 생성해주는 클래스
            Args
                host: 호스트 IP
                port: 포트번호
                name: 클라이언트 이름
                reconnect_time: 연결확인 사이클 주기
                debug: 디버그 여부
            Example
                my_client = SocketClient(host='192.168.0.13', port=20000, name='desktop')\n
                my_client.start()
        '''
        super().__init__()
        self.daemon = True

        #-------------------------
        self.host = host
        self.port = port
        self.name = name
        self.my_socket = None
        self.connections = None
        self.connect_state = False
        self.reconnect_time = reconnect_time
        self.receive_buffer = []
        self.stop_flag = False
        self.debug = debug
        #-------------------------

    def __del__(self):
        self.my_socket.close()

    def run(self):
        while not self.stop_flag:
            while not self.connect_state:
                self.connect_host()
            
            time.sleep(self.reconnect_time) #연결 끊겼는지 reconnect_time마다 확인
            self.send(chr(0)) #chr(0)은 ping에 사용되는 코드
    
    def start(self) -> None:
        '''
        클라이언트를 실행하는 함수, 스레드로 동작
        '''
        super().start()

    def stop(self):
        self.stop_flag = True

    def connect_host(self):
        try:
            self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.my_socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            log('호스트로부터 연결이 거부되었습니다. 서버가 열려있는지 확인하십시오.', self)
            return
        except TimeoutError:
            log('해당 주소로부터 응답이 없습니다. 호스트 장치가 동일 네트워크에 연결되어있지 않거나 올바르지 않은 주소입니다.', self)
            return
            
        log(f'host[{self.host}] 에 연결되었습니다.', self)
        self.connections = self.my_socket
        self.connect_state = True
        self.send(f'{chr(0)}{self.name}')    #이름 보내기

        receive_th = threading.Thread(target=receive, args=(self, self.host))
        receive_th.daemon = True
        receive_th.start()
            
    def send(self, data:str) -> bool:
        '''
        클라이언트에게 데이터를 보내는 함수
            Args
                data: 보낼 데이터
            Return
                성공시 True, 실패시 False
        '''
        if self.connect_state == False: return

        try:
            self.my_socket.sendall(data.encode())
            return True
        except ConnectionResetError :
            log(f'host[{self.host}] 와(과)의 연결이 끊겼습니다.', self)
            self.connect_state = False
            self.my_socket.close()
        return False


    def next(self) -> str:
        '''
        수신 버퍼에 대기중인 다음 데이터를 가져오는 함수
            Return
                str 데이터 or None
        '''
        try:
            return self.receive_buffer.pop(0)
        except IndexError:
            return None

#-------------------------------------------------------------
def local_ip() -> str:
    '''
    접속된 local ip 를 리턴하는 함수
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 0))
    return s.getsockname()[0]

def log(message, socket_object) -> None:
    '''
    형식에 맞춰 로그를 출력하는 함수, 직접 호출할일 없음
        Args
            message: 로그 메시지
            socket_object: SocketServer or SocketClient의 인스턴스
    '''
    if socket_object.debug == True:
        print(f'[{time.strftime("%c", time.localtime(time.time()))}][{type(socket_object).__name__}] {message}')

def receive(socket_object, target_ip):
    '''
    SocketServer, SocketClient 모두 사용하는 데이터 수신 함수,
    직접 호출할 일 없음
    '''
    if type(socket_object.connections) == dict:
        conn_raw = socket_object.connections[target_ip]
        conn = conn_raw[0]
        addr = conn_raw[1][0]
    else:
        conn = socket_object.my_socket
        addr = target_ip

    name = 'host'
    log(f'{addr} 로부터 수신이 시작되었습니다.', socket_object)
    
    while True:
        try:
            data = conn.recv(128)
            if not data:
                break
            
            decoded = data.decode()

            if chr(0) in decoded and len(decoded) > 1:  #이름 수신
                name = decoded[1:]
                socket_object.connections[name] = socket_object.connections.pop(target_ip)
                log(f'접속자 이름: {name}', socket_object)

            if decoded[0] != chr(0): #연결확인 응답
                socket_object.receive_buffer.append((name, addr, decoded))
                log(f'{name}[{addr}]: {decoded}', socket_object)

        except ConnectionResetError:
            try:
                if type(socket_object.connections) == dict:
                    del socket_object.connections[name]

                socket_object.connect_state = False
                log(f'{name}[{addr}] 와(과)의 연결이 종료되었습니다.', socket_object)
                log(f'접속 수: {len(socket_object.connections)}', socket_object)
            except Exception as e:
                pass
            return
