'''
File:		sensor_pi_main.py
Desc:		센서가 연결된 라즈베리파이 메인코드
Author: 	김주현
'''

# 핀 설정
PIN_HYPER_RIGHT_ECHO 		= 24
PIN_HYPER_RIGHT_TRIG 		= 23
PIN_HYPER_LEFT_ECHO 		= 8
PIN_HYPER_LEFT_TRIG 		= 7
PIN_SERVO_BARICADE 			= 13
PIN_SERVO_SANITIZER 		= 18
PIN_PIR 					= 10
# -------

# 통신 설정
SOCKET_HOST = '192.168.1.3'
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

# 필요한 import
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
)#.start()
ultrasonic_right = UltrasonicDetector(
    echo=PIN_HYPER_RIGHT_ECHO, trig=PIN_HYPER_RIGHT_TRIG,
    detect_range=0.3, queue_len=20,
    daemon_port=PIGPIOD_PORT, name='right', debug=False
)#.start()
servo_baricade = ServoDriver(
    pin=PIN_SERVO_BARICADE, init_angle=00,
    daemon_port=PIGPIOD_PORT, name='baricade',
    debug=True
)#.start()
servo_sanitizer = ServoDriver(
    pin=PIN_SERVO_SANITIZER, init_angle=0,
    daemon_port=PIGPIOD_PORT, name='sanitizer',
    debug=True
)#.start()
tempmeter = InfraredTempmeter(
    detect_temp=30
)#.start()
#------------

# 상태 정의
from enum import Enum, auto

class State(Enum):
    BARICADE_CLOSE = auto()
    WAIT_APPROCH_PERSON = auto()
    WAIT_MEASURE_TEMP = auto()
    WAIT_SANITIZE_HAND = auto()
    BARICADE_OPEN = auto()

def expect(target_runnable, expect_return_value, callback):
    if target_runnable() == expect_return_value: 
        callback()
        return True

    return False
#-----------

# 기능 함수들 ----------------------------------------------------
NO_MASK_BORDER = 39
MASK_BORDER = 60
BUFFER_MAX = 20
result_buffer = []
result_avg = None
mask_last_label = None

def detect_mask(voice=False):
        global result_buffer
        global result_avg
        global mask_last_label

        # socket_client.send('PERSON_DETECTED', SOCKET_HOST)

        #음소거 필요한경우
        if voice == False: voice_player.mute()

        # 버퍼에 받은 패킷이 있으면 연속적으로 실행
        while len(socket_client.receive_buffer) > 0:
            packet = socket_client.next()
            print('packet:', packet)
            raw_str_list = packet[2].split(':')

            label = raw_str_list[0]
            probability = float(raw_str_list[1])

            # 사용자의 상태가 변화하면 인식중 음성 재생
            if label != mask_last_label:
                voice_player.play('waiting_mask_recognize', join=False)
                mask_last_label = label
                socket_client.receive_buffer.clear()    #테스트 추가됨

            # 값 맵핑
            if label == 'NO_PERSON':
                result_buffer.append(50)
            elif label == 'NO_MASK':
                result_buffer.append(map_value(probability, 0, 100, NO_MASK_BORDER, 0))
            elif label == 'MASK':
                result_buffer.append(map_value(probability, 0, 100, MASK_BORDER, 100))

            print('prob:', probability)

            # 평균 구하기
            if len(result_buffer) >= BUFFER_MAX: 
                result_avg = sum(result_buffer) / BUFFER_MAX
                result_buffer.clear()
                print('\tresult_avg:', result_avg)
                break 

        #음소거 해제
        voice_player.speak()

        # 결과에 따른 리턴값
        if result_avg == None: ret = 'None'
        elif result_avg >= MASK_BORDER: ret = 'MASK'
        elif result_avg < NO_MASK_BORDER:  ret = 'NO_MASK'
        else: ret = 'NO_PERSON'

        if result_avg != None: result_avg = None

        return ret

# ----------------------------------------------------------------

# 모니터링 콜백 함수들 -------------------------------------------

#사용자가 사라질 때 호출할 콜백 함수
def when_person_vanish():
    global system_state

    system_state = State.BARICADE_CLOSE
    voice_player.play('process_aborted')

#사용자가 마스크를 벗을 때 호출할 콜백 함수
def when_mask_off():
    global system_state

    system_state = State.WAIT_APPROCH_PERSON
    voice_player.play('no_mask')

# ---------------------------------------------------------------

# 상태에 따른 동작 함수들 -----------------------------------------
def on_baricade_close():
    global system_state

    #초음파센서 값 읽기
    while ultrasonic_right.detect() == False: pass

    #다음 상태로 전환
    system_state = State.WAIT_APPROCH_PERSON

def on_wait_approach_person():
    global system_state

    #소켓 버퍼 비우기(이전 측정 결과가 남아있기 때문)
    socket_client.clear_buffer()

    while True:
        # 사용자가 사라지는지 모니터링
        if expect(ultrasonic_right.detect, False, when_person_vanish): break

        res = detect_mask(voice=True)
        sleep(0.5)

        if res == 'NO_PERSON':
            print('there is no person')
            voice_player.play('please_look_camera')
            break
        elif res == 'MASK':
            print('mask on')
            # system_state = State.WAIT_MEASURE_TEMP
            break
        elif res == 'NO_MASK':
            print('no mask')
            voice_player.play('no_mask')
            break
        

def on_wait_measure_temp():
    global system_state

    voice_player.play('temp_measure_guide')

    temp_buffer = []
    TEMP_BUFFER_MAX = 15
    guide_state = False
    try_cnt = 0

    while True:
        # 사용자가 사라지는지 모니터링
        if expect(ultrasonic_right.detect, False, when_person_vanish): break
        
        # 사용자가 마스크를 벗는지 모니터링
        if expect(detect_mask, 'NO_MASK', when_mask_off): break

        sleep(0.5)

        temp = tempmeter.peek()[1]

        if temp <= 30: continue

        if guide_state == False:
            voice_player.play('waiting_temp_measuring', join=False)
            guide_state = True

        temp_buffer.append(temp)

        if len(temp_buffer) >= TEMP_BUFFER_MAX:
            avg = sum(temp_buffer) / TEMP_BUFFER_MAX

            if avg > tempmeter.detect_temp: #열이 나는경우
                if try_cnt == 0:
                    voice_player.play('high_temp_try_again')
                    try_cnt += 1
                    guide_state = False
                    temp_buffer.clear()
                    continue
                elif try_cnt == 1:
                    voice_player.play('high_temp_banned')
                    system_state = State.BARICADE_CLOSE
                    break
            else: #열이 나지 않는경우
                system_state = State.WAIT_SANITIZE_HAND
                break

    
def on_wait_sanitize_hand():
    pass

def on_baricade_open():
    pass
# -------------------------------------------------------




system_state = State.WAIT_APPROCH_PERSON     #초기 상태

# 메인 ------------------------------------------------------------------------------------------------
while True:
    if system_state == State.BARICADE_CLOSE:
        # on_baricade_close()
        pass
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
