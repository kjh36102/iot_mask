#임포트 경로 설정
import os
import sys

module_path = os.path.abspath('../../modules/')
sys.path.append(module_path)

#필요한 모듈들 import
from SocketConnection import SocketConnection   #from [폴더명] import [모듈파일이름] <- 이런식으로 import 할 수 있음

my_server = SocketConnection.SocketServer(port=20000, debug=True)   #모듈파일이름.클래스  <- 이런식으로 클래스 가져올 수 있음
my_server.start()

try:
	while True:
		msg = input()
		print(msg)
except KeyboardInterrupt:
	pass

print('end')
