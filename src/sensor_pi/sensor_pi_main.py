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
SOCKET_HOST = '192.168.0.3'
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

GPIO.output(20, False)
GPIO.output(21, False)
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
socket_client = SocketClient(SOCKET_HOST, SOCKET_PORT).start()
voice_player = Mp3Player('./TTS_records')
ultrasonic_left = UltrasonicDetector(
    echo=PIN_HYPER_LEFT_ECHO, trig=PIN_HYPER_LEFT_TRIG, 
    detect_range=0.3, daemon_port=PIGPIOD_PORT,
    name='left', debug=True
)
ultrasonic_right = UltrasonicDetector(
    echo=PIN_HYPER_RIGHT_ECHO, trig=PIN_HYPER_RIGHT_TRIG,
    detect_range=0.3, daemon_port=PIGPIOD_PORT,
    name='right', debug=False
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
# socket_client.start()

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

def expect_not(target_runnable, expect_return_value, callback):
    while True:
        if target_runnable() != expect_return_value: callback(); break
        sleep(0.5)
    print('종료')
#-----------



# 상태에 따른 동작 함수들
def on_baricade_close():
    global system_state

    #right 초음파센서 값 읽기
    while ultrasonic_right.detect() != True: pass
    system_state = State.WAIT_APPROCH_PERSON
    
    GPIO.output(20, True)   #디버그용

    #사람이 없어지면 실행될 함수
    def when_person_vanish():
        global system_state
        GPIO.output(20, False)
        system_state = State.BARICADE_CLOSE

        #취소되었다고 음성 재생
        voice_player.play('process_aborted')

    #스레드 실행
    expect_th = Thread(target=expect_not, args=(ultrasonic_right.detect, True, when_person_vanish))
    expect_th.daemon = True
    expect_th.start()
    print('스레드 생성됨')
    pass

def on_wait_approach_person():
    # voice_player.play('please_look_camera')   #음성재생 딜레이때문에 send가 늦게 가는 문제 해결해야함
    log('on_wait_approach_person')

    socket_client.send('PERSON_DETECTED', SOCKET_HOST)
    while len(socket_client.receive_buffer) > 0:
        print('받은 값: ', socket_client.next())
    sleep(0.5)
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
