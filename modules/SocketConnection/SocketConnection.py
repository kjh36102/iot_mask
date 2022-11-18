import socket
import threading
import time

def receive( connection):
    conn = connection[0]
    addr = connection[1]

    print(f'{addr[0]}에서 수신시작')

    while True:
            try:
                data = conn.recv(128)
                if not data:
                    break
                print(f'{addr[0]}: {data.decode()}')
            except:
                print(f'{addr[0]}와의 연결이 종료되었습니다.')


def local_ip():
    '''
    접속된 local ip를 알아내는 함수
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 0))
    return s.getsockname()[0]

class SocketServer(threading.Thread):
    def __init__(self, port, conn_max=2):
        super().__init__()
        self.daemon = True

        #-------------------------
        self.port = port
        self.host = local_ip()
        self.conn_max = conn_max
        self.my_socket = None
        self.conn_list = []
        #-------------------------

        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f'{self.host} 에서 소켓 생성됨')
    

    def create_server(self):
        try:
            self.my_socket.bind((self.host, self.port))
        except socket.error as e:
            print('서버 생성 실패: bind()불가')

        self.my_socket.listen(self.conn_max)
        print('서버가 클라이언트를 기다리는 중..')

    def accept_connection(self):
        connection = self.my_socket.accept()
        print('connection:', connection)
        # self.conn_list.append(connection)
        # print(f'서버가 {connection[1]} 과(와) 연결되었습니다.')

        # th = threading.Thread(target=receive, args=(connection, ))
        # th.daemon = True
        # th.start()

    def run(self):
        self.create_server()
        self.accept_connection()

    def send(self, data, target_ip):
        print(f'send {data} to {target_ip}')

        

# class SocketConnection(threading.Thread):
#     def __init__(self, port, host=None, conn_max=2):
#         super().__init__()
#         self.daemon = True

#         #---------------------------------
#         self.host = host
#         self.port = port
#         self.conn_max = conn_max
#         self.server_state = False
#         self.my_socket = None
#         self.send_buffer = []
#         self.conn_list = []
#         self.stop_flag = False
#         self.server_accept_flag = False
#         #---------------------------------

#         if self.host == None: self.server_state = True

#         self.host = self.local_ip()

#         self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         print(f'{self.host} 에서 소켓 생성됨')

#     def __del__(self):
#         print(f'{self.host}의 SocketConnection 삭제됨')

#     def receive(self, connection):
#         conn = connection[0]
#         addr = connection[1]

#         print(f'{addr[0]}에서 수신시작')

#         while True:
#                 try:
#                     data = conn.recv(128)
#                     if not data:
#                         break
#                     print(f'{addr[0]}: {data.decode()}')
#                 except:
#                     print(f'{addr[0]}와의 연결이 종료되었습니다.')

#     def send(self, data, target_ip=None):
#         if target_ip == None:
#             self.my_socket.sendall(data.encode())
#         else:
#             for connection in self.conn_list:
#                 if connection[1]

#     def stop(self):
#         self.stop_flag = True

#     def create_server(self):
#         try:
#             self.my_socket.bind((self.host, self.port))
#         except socket.error as e:
#             print('서버 생성 실패: bind()불가')

#         self.my_socket.listen(self.conn_max)
#         print('서버가 클라이언트를 기다리는 중..')
#         self.server_accept_flag = True

#     def run(self):
#         receive_th = None

#         if self.server_state == True: #서버일 때 실행코드
#             self.create_server()
#             connection = self.my_socket.accept()
#             self.conn_list.append(connection)

#             print(f'서버가 {connection[1]} 과(와) 연결되었습니다.')    

#             receive_th = threading.Thread(target=self.receive, args=(connection, ))
#             receive_th.daemon = True
#             receive_th.start()
#         else:                         #클라이언트 일 때 실행코드
#             try:
#                 self.my_socket.connect((self.host, self.port))
#             except ConnectionRefusedError:
#                 print('호스트로부터 연결이 거부되었습니다. 서버가 열려있는지 동일 네트워크인지 확인하십시오.')
#                 return

#             print(f'{self.host}에 연결되었습니다.')

#             receive_th = threading.Thread(target=self.receive, args=(s, None))
        
#         receive_th.daemon = True
#         receive_th.start()

#         try:
#             while not self.stop_flag:
#                 if len(self.send_buffer) > 0:
#                     connection.sendall(self.send_buffer.pop(0).encode())
#                     time.sleep(0.3)
#         except ConnectionAbortedError:
#             print(f'{self.host}: 연결이 끊어졌습니다.')
#         finally:
#             connection.close()

#     def local_ip(self):
#         '''
#         접속된 local ip를 알아내는 함수
#         '''
#         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         s.connect(('8.8.8.8', 0))
#         return s.getsockname()[0]
