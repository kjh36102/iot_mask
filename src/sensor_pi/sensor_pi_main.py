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
    echo=PIN_HYPER_LEFT_ECHO, trig=PIN_HYPER_LEFT_TRIG, 
    detect_range=0.3, daemon_port=PIGPIOD_PORT,
    name='left', debug=True
)
ultrasonic_right = UltrasonicDetector(
    echo=PIN_HYPER_RIGHT_ECHO, trig=PIN_HYPER_RIGHT_TRIG,
    detect_range=0.3, daemon_port=PIGPIOD_PORT,
    name='right', debug=True
)
servo_baricade = ServoDriver(
    pin=PIN_SERVO_BARICADE, init_angle=0,
    daemon_port=PIGPIOD_PORT, name='baricade',
    debug=True
)
servo_sanitizer = ServoDriver(
    pin=PIN_SERVO_SANITIZER, init_angle=0,
    daemon_port=PIGPIOD_PORT, name='sanitizer',
    debug=True
)
#------------



# 모듈 및 소자 전처리
#socket_client.start()

#-------------------



# 상태 정의
from enum import Enum, auto

class State(Enum):
    BARICADE_CLOSE = auto()
    WAIT_APPROCH_PERSON = auto()
    WAIT_DETECT_MASK = auto()
    WAIT_MEASURE_TEMP = auto()
    WAIT_SANITIZE_HAND = auto()
    BARICADE_OPEN = auto()

system_state = State.BARICADE_CLOSE     #초기 상태
#-----------



# 상태에 따른 동작 함수들
def on_baricade_close():
    #right 초음파센서 값 읽기
    while ultrasonic_right.detect() != True: pass
    log('right 초음파센서 사람 감지')

    #사람이 계속 서있는지 감지하는 스레드 생성 및 실행
    def expect(runnable, expect_value):
        while True:
            if runnable() != expect_value:
                pass
            sleep(0.5)
    pass

def on_wait_approach_person():
    pass

def on_wait_detect_mask():
    pass

def on_wait_measure_temp():
    pass

def on_wait_sanitize_hand():
    pass

def on_baricade_open():
    pass
#-----------------------



# 메인 ------------------------------------------------------------------------------------------------
while True:
    
    if system_state == State.BARICADE_CLOSE:
        on_baricade_close()
    elif system_state == State.WAIT_APPROCH_PERSON:
        on_wait_approach_person()
    elif system_state == State.WAIT_DETECT_MASK:
        on_wait_detect_mask()
    elif system_state == State.WAIT_MEASURE_TEMP:
        on_wait_measure_temp()
    elif system_state == State.WAIT_SANITIZE_HAND:
        on_wait_sanitize_hand()
    elif system_state == State.BARICADE_OPEN:
        on_baricade_open()
    else:
        log(f'알 수 없는 system_state: {system_state}')
# -----------------------------------------------------------------------------------------------------
