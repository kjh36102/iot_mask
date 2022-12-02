'''
File:		sensor_pi_main.py
Desc:		센서가 연결된 라즈베리파이 메인코드
Author: 	김주현
'''

# 핀 설정
PIN_HYPER_RIGHT_ECHO 		= 8
PIN_HYPER_RIGHT_TRIG 		= 7
PIN_HYPER_LEFT_ECHO 		= 24
PIN_HYPER_LEFT_TRIG 		= 23
PIN_SERVO_BARICADE 			= 18
PIN_SERVO_SANITIZER 		= 19
PIN_MOTION 					= 26
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

# 필요한 import
from time import sleep

from Logger import log
from SocketConnection import SocketClient
from Mp3Player import Mp3Player
from UltrasonicDetector import UltrasonicDetector
from ServoDriver import ServoDriver, map_value
from InfraredTempmeter import InfraredTempmeter
from PIR import PIR
from LCD import LCD
#--------------------


# 모듈 객체화
socket_client = SocketClient(host=SOCKET_HOST, port=SOCKET_PORT, debug=True).start()
voice_player = Mp3Player('./TTS_records')
ultrasonic_left = UltrasonicDetector(
    echo=PIN_HYPER_LEFT_ECHO, trig=PIN_HYPER_LEFT_TRIG, 
    detect_range=0.4, max_range=0.5, queue_len=1, daemon_port=PIGPIOD_PORT,
    name='left', debug=False
).start()
ultrasonic_right = UltrasonicDetector(
    echo=PIN_HYPER_RIGHT_ECHO, trig=PIN_HYPER_RIGHT_TRIG,
    detect_range=0.4, max_range=0.5, queue_len=40,
    daemon_port=PIGPIOD_PORT, name='right', debug=False
).start()
servo_baricade = ServoDriver(
    pin=PIN_SERVO_BARICADE, init_angle=0, daemon_port=PIGPIOD_PORT, name='baricade',
    debug=True
).start()
servo_sanitizer = ServoDriver(
    pin=PIN_SERVO_SANITIZER, init_angle=-15, daemon_port=PIGPIOD_PORT, name='sanitizer',
    debug=True
).start()
tempmeter = InfraredTempmeter(
    detect_temp=37.5
).start()
pir = PIR(pin=PIN_MOTION, daemon_port=20001, queue_len=10)
lcd = LCD()
#------------

# 상태 정의
from enum import Enum, auto

class State(Enum):
    BARICADE_CLOSE = auto()
    WAIT_APPROCH_PERSON = auto()
    WAIT_MEASURE_TEMP = auto()
    WAIT_SANITIZE_HAND = auto()
    WAIT_PERSON_PASS = auto()
    BARICADE_OPEN = auto()


#-----------

# 기능 함수들 ----------------------------------------------------
def expect(target_runnable, expect_return_value, callback):
    if target_runnable() == expect_return_value: 
        if callback != None: callback()
        return True

    return False

NO_MASK_BORDER = 39
MASK_BORDER = 60
BUFFER_MAX = 25
mask_result_buffer = []
mask_result_avg = None
mask_last_label = None

def detect_mask(voice=False):
        global mask_result_buffer
        global mask_result_avg
        global mask_last_label

        socket_client.send('PERSON_DETECTED', SOCKET_HOST)

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
                mask_result_buffer.append(50)
            elif label == 'NO_MASK':
                mask_result_buffer.append(map_value(probability, 0, 100, NO_MASK_BORDER, 0))
            elif label == 'MASK':
                mask_result_buffer.append(map_value(probability, 0, 100, MASK_BORDER, 100))

            print('prob:', probability)

            # 평균 구하기
            if len(mask_result_buffer) >= BUFFER_MAX: 
                mask_result_avg = sum(mask_result_buffer) / BUFFER_MAX
                mask_result_buffer.clear()
                print('\tresult_avg:', mask_result_avg)
                break 

        #음소거 해제
        voice_player.speak()

        # 결과에 따른 리턴값
        if mask_result_avg == None: ret = 'None'
        elif mask_result_avg >= MASK_BORDER: ret = 'MASK'
        elif mask_result_avg < NO_MASK_BORDER:  ret = 'NO_MASK'
        else: ret = 'NO_PERSON'

        if mask_result_avg != None: mask_result_avg = None

        return ret

def init_mask_factor():
        global mask_result_buffer
        global mask_result_avg
        global mask_last_label

        mask_result_buffer.clear()
        mask_result_avg = None
        mask_last_label = None
# ----------------------------------------------------------------

# 모니터링 콜백 함수들 -------------------------------------------

#사용자가 사라질 때 호출할 콜백 함수
def when_person_vanish():
    global mask_result_buffer
    mask_result_buffer.clear()

    # global mask_last_label
    # mask_last_label = None

    global system_state
    system_state = State.BARICADE_CLOSE
    voice_player.play('process_aborted')

    lcd.lcd_display_string('--------------------', 1)
    lcd.lcd_display_string('   process aborted  ', 2)
    lcd.lcd_display_string('                    ', 3)
    lcd.lcd_display_string('--------------------', 4)

    socket_client.send('PERSON_VANISHED', SOCKET_HOST)

#사용자가 마스크를 벗을 때 호출할 콜백 함수
def when_mask_off():
    global system_state

    system_state = State.WAIT_APPROCH_PERSON
    voice_player.play('no_mask')

# ---------------------------------------------------------------

# 상태에 따른 동작 함수들 -----------------------------------------
def on_baricade_close():

    #초음파센서 사람 없으면 패스
    while ultrasonic_right.detect() == False: pass

    #greeting 음성 출력
    # voice_player.play('greeting')

    #다음 상태로 전환
    global system_state
    system_state = State.WAIT_APPROCH_PERSON

def on_wait_approach_person():

    #소켓 버퍼 비우기(이전 측정 결과가 남아있기 때문)
    socket_client.receive_buffer.clear()

    while True:
        # 사용자가 사라지는지 모니터링
        if expect(ultrasonic_right.detect, False, when_person_vanish): break

        res = detect_mask(voice=True)
        sleep(0.2)

        if res == 'NO_PERSON':
            print('there is no person')
            voice_player.play('please_look_camera', join=False)
            break
        elif res == 'MASK':
            print('mask on')
            global system_state
            system_state = State.WAIT_MEASURE_TEMP
            break
        elif res == 'NO_MASK':
            print('no mask')
            voice_player.play('no_mask', join=False)
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

        sleep(0.2)

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
    global system_state

    voice_player.play('sanitizer_guide', join=False)

    while True:
        # 사용자가 사라지는지 모니터링
        if expect(ultrasonic_right.detect, False, when_person_vanish): break
        
        # 사용자가 마스크를 벗는지 모니터링
        if expect(detect_mask, 'NO_MASK', when_mask_off): break

        # 사용자가 손을 집어넣을때까지 기다림
        if expect(pir.detect, True, None):
            #손소독제 펌핑
            servo_sanitizer.move(angle=10, smooth=3).move(angle=-10, smooth=0.2)
            system_state = State.BARICADE_OPEN
            break
        
        sleep(0.2)

def on_baricade_open():
    global system_state

    voice_player.play('barricade_open', join=False)
    servo_baricade.move(angle=90, smooth=2)


    system_state = State.WAIT_PERSON_PASS

def on_person_pass():
    global system_state
    if expect(ultrasonic_left.detect, True, None):
        while True:
            if expect(ultrasonic_left.detect, False, None): break
            sleep(0.2)
        
        voice_player.play('barricade_close')
        servo_baricade.move(angle=0, smooth=2)

        init_mask_factor()
        system_state = State.BARICADE_CLOSE
# -------------------------------------------------------




system_state = State.BARICADE_CLOSE     #초기 상태

# 메인 ------------------------------------------------------------------------------------------------

lcd.backlight(True)
lcd.lcd_display_string('====================', 1)
lcd.lcd_display_string('       HELLO        ', 2)
lcd.lcd_display_string('                    ', 3)
lcd.lcd_display_string('====================', 4)

sleep(2)

try:
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
        elif system_state == State.WAIT_PERSON_PASS:
            on_person_pass()
        else:
            log(f'알 수 없는 system_state: {system_state}')
        sleep(0.2)
except (KeyboardInterrupt or Exception) as e:
    print('오류:', e)
    lcd.backlight(False)
# -----------------------------------------------------------------------------------------------------

