import socket
import threading
import time

class SocketServer(threading.Thread):
    def __init__(self, port):
        super().__init__()
        self.daemon = True

        #-------------------------
        self.port = port
        self.host = local_ip()
        self.my_socket = None
        self.connections = {}
        #-------------------------

        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def __del__(self):
        self.my_socket.close()

    def create_server(self):
        try:
            self.my_socket.bind((self.host, self.port))
        except socket.error as e:
            print('서버 생성 실패: bind()불가')

        self.my_socket.listen(1)
        print('서버가 클라이언트를 기다리는 중..')

    def accept_connection(self):
        while True:
            conn = self.my_socket.accept()
            addr = conn[1][0]
            self.connections[addr] = conn
            print(f'서버가 {addr} 와(과) 연결되었습니다.')

            print('접속 수:', len(self.connections))

            receive_th = threading.Thread(target=receive, args=(self, addr, ))
            receive_th.daemon = True
            receive_th.start()

    def run(self):
        self.create_server()

        accept_connection_th = threading.Thread(target=self.accept_connection)
        accept_connection_th.daemon = True
        accept_connection_th.start()

    def send(self, data, target_ip):
        self.connections[target_ip][0].sendall(data.encode())

class SocketClient(threading.Thread):
    def __init__(self, host, port, name, reconnect_time=3):
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
        self.stop_flag = False
        #-------------------------

    def __del__(self):
        self.my_socket.close()

    def connect_host(self):
        try:
            self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.my_socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            print('호스트로부터 연결이 거부되었습니다. 서버가 열려있는지 또는 동일 네트워크에 연결되어있는지 확인하십시오.')
            return
            
        print(f'{self.host}에 연결되었습니다.')
        self.connect_state = True
        self.send(f'{chr(0)}{self.name}'.encode())    #이름 보내기

        receive_th = threading.Thread(target=receive, args=(self, self.host))
        receive_th.daemon = True
        receive_th.start()

    def run(self):
        while not self.stop_flag:
            while not self.connect_state:
                self.connect_host()
            
            time.sleep(self.reconnect_time) #연결 끊겼는지 reconnect_time마다 확인
            self.send(chr(0)) #chr(0)은 ping에 사용되는 코드
            
    def stop(self):
        self.stop_flag = True

    def send(self, data):
        try:
            self.my_socket.sendall(data.encode())
        except ConnectionAbortedError:
            print(f'{self.host} 와(과)의 연결이 끊겼습니다.')
            self.connect_state = False
            self.my_socket.close()


def receive(socket_object, target_ip):
    if type(socket_object.connections) == dict:
        conn_raw = socket_object.connections[target_ip]
        conn = conn_raw[0]
        addr = conn_raw[1][0]
    else:
        conn = socket_object.my_socket
        addr = target_ip
    
    print(f'{addr} 로부터 수신이 시작되었습니다.')

    while True:
        try:
            data = conn.recv(128).decode()
            if not data:
                break
            
            decoded = data.decode()

            # if decoded != chr(0).encode(): #ping 받으면
            print(f'{addr}: {decoded}')    
        except:
            if type(socket_object.connections) == dict:
                del socket_object.connections[addr]
            else:
                socket_object.connect_state = False
            print(f'{addr} 와(과)의 연결이 종료되었습니다.')
            print('접속 수:', len(socket_object.connections))

def local_ip():
    '''
    접속된 local ip를 알아내는 함수
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 0))
    return s.getsockname()[0]
