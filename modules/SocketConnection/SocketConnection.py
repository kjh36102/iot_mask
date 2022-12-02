import sys
sys.path.append('./modules/Logger')
sys.path.append('./modules/StopableThread')
from Logger import log
from StopableThread import StopableThread

#----------------------

import socket
import time

def local_ip() -> str:
    '''
    접속된 local ip 를 리턴하는 함수
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 0))
    return s.getsockname()[0]

class __SocketConnection(StopableThread):
    def __init__(self, port, host=local_ip(), buffer_len=30, debug=False):
        super().__init__()

        self.host = host
        self.port = port
        self.my_ip = local_ip()
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connections = {} 
        self.receive_buffer = {}
        self.buffer_len = buffer_len
        self.waiting_next_part = ''

        self.debug = debug

    def __del__(self):
        self.my_socket.close()

        for target_ip in self.connections:
            target_socket = self.connections[target_ip]

            if target_socket != None: target_socket.close()

    def send(self, data, target_ip):
        while True:
            try:
                data = data + chr(0)  #데이터 끝 식별자를 붙여 전송
                self.connections[target_ip].sendall(data.encode())
                break
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                log(self, f'전송 실패! 호스트 {target_ip} 와 연결할 수 없습니다.')

                #receive_buffer 정리
                self.receive_buffer[target_ip].clear()
            except KeyError:
                log(self, f'전송 실패! {target_ip} 은(는) 오프라인입니다.')

            time.sleep(5)
            return
            

    def broadcast(self, data):
        data = data + chr(0)

        for target_ip in self.connections:
            try:
                target_socket = self.connections[target_ip]
                if target_socket == None:
                    #호스트에게 브릿지 부탁
                    self.my_socket.sendall(f'{chr(1)}/REQ_BRIDGE/{self.my_ip}/{target_ip}/{data}'.encode())
                else:
                    #직접 전송
                    target_socket.sendall(data.encode())
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                log(self, f'전송 실패! {target_ip} 은(는) 오프라인입니다.')

            #receive_buffer 정리
            self.receive_buffer[target_ip].clear()
        
    def next(self, target_ip):
        try:
            return self.receive_buffer[target_ip].pop(0)
        except (IndexError, KeyError):
            return None
        
    
    def _data_preprocess(self, data, sender_ip):
        self.waiting_next_part = ''

        data_splited = data.split(chr(0))

        for i in range(len(data_splited) - 1):
            if chr(1) in data_splited[i]:   #커맨드 식별자가 포함되어있으면
                self._receive_action(data_splited[i])
            elif data_splited[i] != '':
                # if len(self.receive_buffer[sender_ip]) < self.buffer_len:
                    self.receive_buffer[sender_ip].append((sender_ip, self.my_ip, data_splited[i]))
                # else:
                #     log(self, f'{sender_ip} 을(를) 위한 수신버퍼가 꽉 찼습니다. 버린 데이터: {data_splited[i]}')

        self.waiting_next_part = data_splited[-1]

    def _receive(self, sender_ip=None):
        if sender_ip == None: sender_ip = self.host #클라이언트는 호스트에게서만 메시지를 받음
        
        sender_socket = self.connections[sender_ip]

        try:
            while True:
                data = self.waiting_next_part + sender_socket.recv(32).decode()
                self._data_preprocess(data, sender_ip)
        except (ConnectionAbortedError, ConnectionResetError):
            log(self, f'{sender_ip} 이(가) 강제로 연결을 끊었습니다.')

            #receive_buffer 정리
            self.receive_buffer[sender_ip].clear()

    def _receive_action(self, decoded):
        #자식클래스가 상속받아 작성
        pass


class SocketServer(__SocketConnection):
    def __init__(self, port, host=local_ip(), debug=False):
        super().__init__(port, host, debug)

        self.receive_threads = {}

    def __del__(self):
        for target_ip in self.receive_threads:
            self.receive_threads[target_ip].stop()
        super().__del__()

    def run(self):
        self.__create_server()

        StopableThread(target=self.check_connection, args=()).start()

        while True: self.__accept_connection()

    def __create_server(self):
        try:
            self.my_socket.bind((self.host, self.port))
            self.my_socket.listen(1)
            log(self, f'서버가 {self.my_ip} 에서 실행되었습니다.')
        except Exception as e:
            log(self, f'서버 생성 JOIN실패! {e}')
    
    def __accept_connection(self):
        connection = self.my_socket.accept()
        sender_socket = connection[0]
        sender_ip = connection[1][0]

        log(self, f'서버가 {sender_ip} 의 연결을 허용했습니다.')

        #접속자에게 목록 넘겨주기
        if len(self.connections) > 0:
            cmd = f'{chr(1)}/LIST/{str.join("/", list(self.connections.keys()))}{chr(0)}'
            sender_socket.sendall(cmd.encode())

        #모두에게 입장 알리기
        self.broadcast(f'{chr(1)}/JOIN/{sender_ip}')
        
        #연결목록에 추가
        self.connections[sender_ip] = sender_socket
        log(self, f'접속자 수: {len(self.connections)}')

        #수신 버퍼 생성
        self.receive_buffer[sender_ip] = []

        #수신 스레드 생성
        receive_th = StopableThread(target=self._receive, args=(sender_ip, )).start() 
        self.receive_threads[sender_ip] = receive_th
    
    def check_connection(self):
        while True:
            try:
                for target_ip in self.connections:
                    self.connections[target_ip].sendall(chr(0).encode())
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                self.connections.pop(target_ip)
                self.receive_threads.pop(target_ip).stop()
                self.receive_buffer.pop(target_ip)
                self.broadcast(f'{chr(1)}/LEFT/{target_ip}')
                log(self, f'{target_ip} 와(과) 의 연결이 끊겼습니다.')
            
            time.sleep(2)
    
    def _receive_action(self, decoded):
        args = decoded.split(sep='/')

        if args[1] == 'REQ_BRIDGE':
            sender_ip = args[2]
            target_ip = args[3]
            data = args[4]
            self.send(f'{chr(1)}/BRIDGED/{sender_ip}/{data}', target_ip)
            log(self, f'[{sender_ip} -> {target_ip}]: {data}')



class SocketClient(__SocketConnection):
    def __init__(self, port, host=local_ip(), reconn_time=5, debug=False):
        super().__init__(port, host, debug)

        self.reconn_time = reconn_time
        self.connect_state = False
        self.receive_th = None

    def __del__(self):
        if self.receive_th != None: self.receive_th.stop()
        super().__del__()

    def run(self):
        while True:
            while not self.connect_state:
                self.__connect_host()
            
            time.sleep(self.reconn_time)

            try:
                self.send('', self.host)
            except ConnectionAbortedError:
                log(self, f'호스트 {self.host} 와(과)의 연결이 끊겼습니다.')
                self.connect_state = False
                self.receive_buffer.pop(self.host)
                self.my_socket.close()

                #접속자 목록 초기화
                self.connections.clear()
            
    def __connect_host(self):
        try:
            self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            log(self, f'호스트 {self.host} 의 연결을 기다리는 중입니다...')

            self.my_socket.connect((self.host, self.port))
            self.connections[self.host] = self.my_socket

            log(self, f'호스트 {self.host} 에 연결되었습니다.')
            self.connect_state = True

            self.receive_buffer[self.host] = []

            self.receive_th = StopableThread(target=self._receive, args=(self.host, )).start()
        except ConnectionRefusedError:
            log(self, f'호스트 {self.host} 으(로)부터 연결이 거부되었습니다. 서버가 열려있는지 또는 동일 네트워크에 연결되어있는지 확인하십시오.')

    def _receive_action(self, decoded):
        args = decoded.split(sep='/')

        if args[1] == 'BRIDGED':
            sender_ip = args[2]
            data = args[3]
            log(self, f'[{sender_ip}]: {data}')
            self._data_preprocess(data, sender_ip)
        elif args[1] == 'JOIN':
            self.connections[args[2]] = None
            log(self, f'{args[2]} 이(가) 통신에 참가했습니다.')
        elif args[1] == 'LEFT':
            self.connections.pop(args[2])
            log(self, f'{args[2]} 이(가) 통신을 종료했습니다.')
        elif args[1] == 'LIST':
            join_list = args[2:]
            for who in join_list:
                self.connections[who] = None
