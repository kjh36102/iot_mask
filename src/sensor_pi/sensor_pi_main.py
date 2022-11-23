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
PIGPIOD_PORT = 20001
# ---------

# 임포트 경로 설정
import os
import sys

#base_path = '../../modules/'
base_path = './modules/'
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
from time import sleep
from threading import Thread

from Logger import log
from SocketConnection import SocketClient
from Mp3Player import Mp3Player
from UltrasonicDetector import UltrasonicDetector
from ServoDriver import ServoDriver
#--------------------

# 모듈 객체화
# socket_client = SocketClient(SOCKET_HOST, SOCKET_PORT).start()
voice_player = Mp3Player('./TTS_records')
ultrasonic_left = UltrasonicDetector(
    echo=PIN_HYPER_LEFT_ECHO, 
    trig=PIN_HYPER_LEFT_TRIG, 
    detect_range=0.3, 
    daemon_port=PIGPIOD_PORT,
    name='left', 
    debug=True
)
ultrasonic_right = UltrasonicDetector(
    echo=PIN_HYPER_RIGHT_ECHO,
    trig=PIN_HYPER_RIGHT_TRIG,
    detect_range=0.3,
    daemon_port=PIGPIOD_PORT,
    name='right',
    debug=True
)
servo_baricade = ServoDriver(
    pin=PIN_SERVO_BARICADE,
    init_angle=0,
    daemon_port=PIGPIOD_PORT,
    name='baricade',
    debug=True
)
servo_sanitizer = ServoDriver(
    pin=PIN_SERVO_SANITIZER,
    init_angle=0,
    daemon_port=PIGPIOD_PORT,
    name='sanitizer',
    debug=True
)
#----------

# 모듈 전처리
#socket_client.start()

#------------

#================================================================================================
sleep(2)

servo_baricade.move(90)
servo_sanitizer.move(-90)

def print_ultrasonic():
    while True:
        ultrasonic_left.distance()
        left_state = ultrasonic_left.detect()

        ultrasonic_right.distance()
        right_state = ultrasonic_right.detect()

        GPIO.output(21, left_state)
        GPIO.output(20, right_state)

        sleep(0.5)


print_ultrasonic_th = Thread(target=print_ultrasonic)
print_ultrasonic_th.daemon = True
print_ultrasonic_th.start()


try:
    while True:
        args = input().split(' ')
        log(f'input_args: {args}')

        if args[0] == 'none': pass
        elif args[0] == 'servo_move':
            servo_baricade.move(int(args[1]))
            servo_sanitizer.move(int(args[1]))
        elif args[0] == 'send':
            # socket_client.send('person', SOCKET_HOST)
            pass

except KeyboardInterrupt:
    print('end')

