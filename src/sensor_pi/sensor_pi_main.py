'''
File:		sensor_pi_main.py
Desc:		센서가 연결된 라즈베리파이 메인코드
Author: 	김주현
'''

# 핀 설정
PIN_HYPER_RIGHT_ECHO 		= 8
PIN_HYPER_RIGHT_TRIG 		= 7
PIN_HYPER_LEFT_ECHO 		= 23
PIN_HYPER_LEFT_TRIG 		= 24
PIN_SERVO_BARICADE 			= 13
PIN_SERVO_SANITIZER 		= 18
PIN_BUZZER 					= 21
# -------

# 통신 설정
SOCKET_HOST = '192.168.0.5'
SOCKET_PORT = 20000
# ---------

# 임포트 경로 설정
import os
import sys

base_path = '../../modules/'
module_names = os.listdir(base_path)

for module in module_names:
    sys.path.append(base_path + module)
#-----------------

# GPIO 초기화
import RPi._GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(20, GPIO.OUT)
GPIO.setup(21, GPIO.OUT)
# -----------

# 필요한 모듈들 import
import time
import threading

from SocketConnection import SocketClient
from Mp3Player import Mp3Player
from HyperDetector import HyperDetector
from ServoDriver import ServoDriver
#--------------------

# 모듈 객체화
socket_client = SocketClient(SOCKET_HOST, SOCKET_PORT)
voice_player = Mp3Player('./TTS_records')
hyper_detector = HyperDetector()
servo_baricade = ServoDriver(PIN_SERVO_BARICADE)
servo_sanitizer = ServoDriver(PIN_SERVO_SANITIZER)
#----------

# 모듈 전처리
#socket_client.start()

hyper_detector.register('left', PIN_HYPER_LEFT_ECHO, PIN_HYPER_LEFT_TRIG, 20, 10)
hyper_detector.register('right', PIN_HYPER_RIGHT_ECHO, PIN_HYPER_RIGHT_TRIG, 70, 20)
hyper_detector.start()
#------------

#================================================================================================
time.sleep(2)

servo_baricade.move(90)
servo_sanitizer.move(-90)

def start_measure():
    while True:
        print(f'avg_left: {hyper_detector.get_avg_value("left")}, avg_right: {hyper_detector.get_avg_value("right")}')
            
        #left_detect = hyper_detector.detect("left")
        right_detect = hyper_detector.detect("right")

        #print(f'            {left_detect}                     {right_detect}')

        #if left_detect == True:
            #socket_client.send('hyper left detected!', SOCKET_HOST)
        
        #if right_detect == True:
            #socket_client.send('hyper right detected!', SOCKET_HOST)

        #print('next:', socket_client.next())

        #GPIO.output(21, left_detect)
        GPIO.output(20, right_detect)

        time.sleep(0.2)

th = threading.Thread(target=start_measure)
th.daemon = True
th.start()

try:
    while True:
        args = input().split(' ')
        print(args)

        if args[0] == 'pause': hyper_detector.pause()
        elif args[0] == 'resume': hyper_detector.resume()
        elif args[0] == 'servo_move':
            print('moving..', args[1])
            servo_baricade.move(int(args[1]))
            servo_sanitizer.move(int(args[1]))
        elif args[0] == 'send':
            socket_client.send('person', SOCKET_HOST)

except KeyboardInterrupt:
    print('end')

