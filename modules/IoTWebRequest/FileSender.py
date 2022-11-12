import requests

class FileSender:
    def __init__(self, host_ip:str='127.0.0.1', port:str='5000') -> None:
        '''
        FileSender의 생성자\n
        Args:
          host_ip: 목적지 ip 주소
          port: 목적지 포트번호
        Example:
          from FileSender import FileSender\n
          fs = FileSender()\n
          fs.send_binary('./images/yee.png')
        '''
        self.host_ip = host_ip
        self.port = port
        self.build_url()
    
    def set_host_ip(self, host_ip:str) -> None:
        '''
        host_ip 설정\n
        Args:
          host_ip: 목적지 ip 주소
        '''
        self.host_ip = host_ip
        self.build_url()
    
    def set_port(self, port) -> None:
        '''
        port 설정\n
        Args:
          port: 목적지 포트번호
        '''
        self.port = port
        self.build_url()

    def build_url(self) -> None:
        self.url = 'http://%s:%s/__file_send__' % (self.host_ip, self.port)

    
    def send_file(self, file_dir:str) -> str:
        '''
        파일 전송\n
        Args:
          file_dir: 파일의 경로 + 파일 이름 + 확장자
        Returns:
          성공 또는 오류메세지
        '''
        try:
            file = {
                'file': open(file_dir, 'rb')
            }

            result = requests.post(self.url, files=file)
            
            return file['file'].name + ' 이(가) 전송됨'
        
        except Exception as e:
            return 'FileSender.__send_file() 에서 오류 발생'

    def send_object(self, sending_object:object) -> str:
      '''
        Object 전송\n
        Args:
          sending_object: 변수, 리스트, 딕셔너리, 튜플 등 모든 Object
        Returns:
          성공 또는 오류메세지
      '''
      try:
        requests.post(self.url, json={'data':sending_object})
        return 'Object ' + str(object) + ' 이(가) 전송됨'
      except Exception as e:
        return 'FileSender.__send_object() 에서 오류 발생'
    