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
SOCKET_HOST = '192.168.0.8'
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

from Logger import log
from SocketConnection import SocketClient
from Mp3Player import Mp3Player
from UltrasonicDetector import UltrasonicDetector
from ServoDriver import ServoDriver, map_value
from StopableThread import StopableThread
from InfraredTempmeter import InfraredTempmeter
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
    detect_range=0.3, queue_len=20,
    daemon_port=PIGPIOD_PORT, name='right', debug=False
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
tempmeter = InfraredTempmeter()
#------------



# 모듈 및 소자 전처리
# socket_client.start()

#-------------------



# 상태 정의
from enum import Enum, auto

class State(Enum):
    BARICADE_CLOSE = auto()
    WAIT_APPROCH_PERSON = auto()
    WAIT_MEASURE_TEMP = auto()
    WAIT_SANITIZE_HAND = auto()
    BARICADE_OPEN = auto()

system_state = State.BARICADE_CLOSE     #초기 상태

def expect(target_runnable, expect_return_value, callback):
    while True:
        if target_runnable() == expect_return_value: 
            callback()
            break
        sleep(0.5)    
    print('종료')
#-----------

# 전역변수
mask_last_label = None
mask_guided_state = False
mask_moniter_created = False
temp_measure_created = False
#------------

# 함수들 ------------------------------------------------------------

#마스크 착용 결과를 str로 반환하는 함수
def detect_mask():
    global mask_last_label
    global mask_guided_state

    result_buffer = []
    buffer_max = 10     #결과 버퍼 크기
    result_avg = None

    while True:
        socket_client.send('PERSON_DETECTED', SOCKET_HOST)

        while len(socket_client.receive_buffer) > 0:
            packet = socket_client.next()
            print('packet:', packet)
            raw_str_list = packet[2].split(':')

            label = raw_str_list[0]
            probability = float(raw_str_list[1])

            print(f'label: {label}, prob: {probability}')

            if label != mask_last_label:
                voice_player.play('waiting_mask_recognize', join=False)
                mask_last_label = label

            if label == 'NO_PERSON':
                result_buffer.append(50)
            elif label == 'NO_MASK':
                result_buffer.append(map_value(probability, 0, 100, 39, 0))
            elif label == 'MASK':
                result_buffer.append(map_value(probability, 0, 100, 60, 100))

            print(f'res: {result_buffer[len(result_buffer) - 1]}')

            if len(result_buffer) >= buffer_max: 
                result_avg = sum(result_buffer) / buffer_max
                print('result_avg:', result_avg)
                break
        
        if result_avg == None:
            sleep(0.5)      #요청 딜레이
        elif result_avg >= 60:
            return 'MASK'
        elif result_avg < 39:
            return 'NO_MASK'
        else: return 'NO_PERSON'

def measure_temp():

    pass

# ----------------------------------------------------------------


# 상태에 따른 동작 함수들 -----------------------------------------
def on_baricade_close():

    #초음파센서 값 읽기
    while ultrasonic_right.detect() == False: pass

    #안내음성 재생
    #voice_player.play('') #안녕하세요 재생

    GPIO.output(20, True) #디버그용

    #다음 상태로 전환
    global system_state
    system_state = State.WAIT_APPROCH_PERSON


def on_wait_approach_person():
    #사용자가 사라질 때 호출할 함수 정의
    def when_person_vanish():
        global system_state
        global mask_moniter_created

        system_state = State.BARICADE_CLOSE
        voice_player.play('process_aborted')
        mask_moniter_created = False

    global mask_moniter_created

    # 변수 모니터링 스레드 실행
    if mask_moniter_created == False:
        moniter_th = StopableThread(target=expect, args=(ultrasonic_right.detect, False, when_person_vanish))
        moniter_th.start()
        mask_moniter_created = True
    
    res = detect_mask()

    print('res:', res)

    if system_state != State.WAIT_APPROCH_PERSON:
        return

    if res == 'NO_PERSON':
        print('there is no person')
        voice_player.play('please_look_camera')
        sleep(1)
    elif res == 'MASK':
        print('mask on')
        system_state = State.WAIT_MEASURE_TEMP
    elif res == 'NO_MASK':
        print('no mask')
        voice_player.play('no_mask')


def on_wait_measure_temp():
    global temp_measure_created
    #체온 측정 스레드 시작

    if temp_measure_created != True:
        # temp_measure_th = StopableThread(target=)
        pass

def on_wait_sanitize_hand():
    pass

def on_baricade_open():
    pass
# -------------------------------------------------------



# 메인 ------------------------------------------------------------------------------------------------
while True:
    if system_state == State.BARICADE_CLOSE:
        on_baricade_close()
    elif system_state == State.WAIT_APPROCH_PERSON:
        on_wait_approach_person()
    elif system_state == State.WAIT_MEASURE_TEMP:
        on_wait_measure_temp()
    elif system_state == State.WAIT_SANITIZE_HAND:
        on_wait_sanitize_hand()
    elif system_state == State.BARICADE_OPEN:
        on_baricade_open()
    else:
        log(f'알 수 없는 system_state: {system_state}')
# -----------------------------------------------------------------------------------------------------
