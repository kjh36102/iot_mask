'''
File:		sensor_pi_main.py
Desc:		센서가 연결된 라즈베리파이 메인코드
Author: 	김주현
'''
#카메라 파이 해상도 960x720 30fps <-- 베스트

# 핀 설정-------------------------------------------------------------------------------
PIN_HYPER_RIGHT_ECHO 		= 8
PIN_HYPER_RIGHT_TRIG 		= 7
PIN_HYPER_LEFT_ECHO 		= 24
PIN_HYPER_LEFT_TRIG 		= 23
PIN_SERVO_BARICADE 			= 18
PIN_SERVO_SANITIZER 		= 19
PIN_SERVO_CAMERA            = 13
PIN_MOTION 					= 26
# ------------------------------------------------------------------------------------

# 통신 설정----------------------------------------------------------------------------
SOCKET_HOST = '192.168.1.4'
SOCKET_PORT = 20000
PIGPIOD_PORT = 20001
# -------------------------------------------------------------------------------------


# 임포트 경로 설정-----------------------------------------------------------------------
import os
import sys

#base_path = '../../modules/'
base_path = './modules/'
module_names = os.listdir(base_path)

for module in module_names:
    sys.path.append(base_path + module)
#---------------------------------------------------------------------------------------

# 필요한 import--------------------------------------------------------------------------
from time import sleep

from Logger import log
from SocketConnection import SocketClient
from Mp3Player import Mp3Player
from UltrasonicDetector import UltrasonicDetector
from StopableThread import StopableThread
from ServoDriver import ServoDriver, map_value
from InfraredTempmeter import InfraredTempmeter
from PIR import PIR
from LCD import LCD
#-----------------------------------------------------------------------------------------


# 모듈 객체화------------------------------------------------------------------------------
socket_client = SocketClient(host=SOCKET_HOST, port=SOCKET_PORT, debug=True).start()
voice_player = Mp3Player('./TTS_records')
ultrasonic_left = UltrasonicDetector(
    echo=PIN_HYPER_LEFT_ECHO, trig=PIN_HYPER_LEFT_TRIG, 
    detect_range=0.5, max_range=0.6, queue_len=1, daemon_port=PIGPIOD_PORT,
    name='left', debug=False
).start()
ultrasonic_right = UltrasonicDetector(
    echo=PIN_HYPER_RIGHT_ECHO, trig=PIN_HYPER_RIGHT_TRIG,
    detect_range=0.6, max_range=1, queue_len=30,
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
servo_camera = ServoDriver(
    pin=PIN_SERVO_CAMERA, init_angle=0, daemon_port=PIGPIOD_PORT, name='camera', debug=True
).start()
tempmeter = InfraredTempmeter(
    detect_temp=37.5
).start()
pir = PIR(pin=PIN_MOTION, daemon_port=20001, queue_len=10)
lcd = LCD()
#------------------------------------------------------------------------------------------

# 상태 정의---------------------------------------------------------------------------------
from enum import Enum, auto

class State(Enum):
    BARICADE_CLOSE = auto()
    WAIT_APPROCH_PERSON = auto()
    WAIT_MEASURE_TEMP = auto()
    WAIT_SANITIZE_HAND = auto()
    WAIT_PERSON_PASS = auto()
    BARICADE_OPEN = auto()
#--------------------------------------------------------------------------------------------

# 전역 변수들 --------------------------------------------------------------------------------
# 진행상황 저장하는 변수들
mask_checked = False
temperature_checked = False
sanitizer_checked = False

# 마스크 인식과 관련된 변수들
NO_MASK_BORDER = 39
MASK_BORDER = 60
BUFFER_MAX = 10
mask_result_buffer = []
mask_result_avg = None
mask_last_label = None

# 체온 인식과 관련된 변수
TEMP_BUFFER_MAX = 20

#카메라 움직이는 스레드 변수
camera_servo_th = None
#--------------------------------------------------------------------------------------------

# 기능 함수들 --------------------------------------------------------------------------------
def expect(target_runnable, expect_return_value, callback):
    if target_runnable() == expect_return_value:
        if callback != None: callback()
        return True
    return False

# 사용자의 방역조치 진행사항과 관련된 요소 초기화
def clear_user_checks():
    global mask_checked; mask_checked = False
    global temperature_checked; temperature_checked = False
    global sanitizer_checked; sanitizer_checked = False

def detect_mask(voice=False):
        global mask_result_buffer
        global mask_result_avg
        global mask_last_label

        socket_client.send('PERSON_DETECTED', SOCKET_HOST)

        #음소거 필요한경우
        if voice == False: voice_player.mute()

        # 버퍼에 받은 패킷이 있으면 연속적으로 실행
        while len(socket_client.receive_buffer[SOCKET_HOST]) > 0:
            packet = socket_client.next(SOCKET_HOST)
            # print('packet:', packet)

            raw_str_list = packet[2].split(':')

            label = raw_str_list[0]
            probability = float(raw_str_list[1])

            # 사용자의 상태가 변화하면 인식중 음성 재생
            if label != mask_last_label:
                if voice == True:
                    lcd.lcd_display_string('  [Mask Detection]  ', 2)
                    lcd.lcd_display_string('  Detecting mask... ', 3)

                voice_player.play('mask_detect_start', join=False)
                mask_last_label = label
                mask_result_buffer.clear()

    
                    
            global camera_servo_th  
            # 값 맵핑
            if label == 'NO_PERSON':
                mask_result_buffer.append(50)
            elif label == 'NO_MASK':
                mask_result_buffer.append(map_value(probability, 0, 100, NO_MASK_BORDER, 0))
            elif label == 'MASK':
                mask_result_buffer.append(map_value(probability, 0, 100, MASK_BORDER, 100))

            if label != 'NO_PERSON':    #사람 발견 시

                #카메라 움직이고 있다면 취소
                if camera_servo_th != None:
                    servo_camera.stop_move()
                    camera_servo_th.stop()
                    camera_servo_th = None

            # print('prob:', probability)

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

        # 이전 평균값이 남아있으면 제거
        if mask_result_avg != None: 
            mask_result_avg = None

        return ret

# 마스크 인식과 관련된 요소 초기화
def init_mask_factor():
        global mask_result_buffer
        global mask_result_avg
        global mask_last_label

        mask_result_buffer.clear()
        mask_result_avg = None
        mask_last_label = None

#사람이 안보일때 카메라 움직이기
def camera_seek_person():
    servo_camera.move(15, smooth=4)
    sleep(3)
    servo_camera.move(-15, smooth=4)
    sleep(3)
    servo_camera.move(0, smooth=4)
    sleep(2)
# ------------------------------------------------------------------------------------------

# 모니터링 콜백 함수들 ------------------------------------------------------------------------
#사용자가 사라질 때 호출할 콜백 함수
def when_person_vanish():
    global mask_result_buffer
    global camera_servo_th
    global system_state
    system_state = State.BARICADE_CLOSE

    lcd.lcd_display_string('  PROCESS CANCELED  ', 2)
    lcd.lcd_display_string('                    ', 3)

    #문 닫기
    servo_baricade.move(0, smooth=3)

    #카메라 움직이고 있다면 취소
    if camera_servo_th != None:
        servo_camera.stop_move()
        camera_servo_th.stop()
        camera_servo_th = None

    servo_camera.move(0, smooth=4)

    voice_player.play('process_aborted')

#사용자가 마스크를 벗을 때 호출할 콜백 함수
def when_mask_off():
    global system_state
    global mask_checked

    system_state = State.WAIT_APPROCH_PERSON
    mask_checked = False

    #문 닫기
    servo_baricade.move(0, smooth=3)

    voice_player.play('mask_not_detected')

# 카메라이 사람이 없으면 호출하는 함수
def when_no_person():
    global system_state
    global mask_checked

    system_state = State.WAIT_APPROCH_PERSON
    mask_checked = False

    #문 닫기
    servo_baricade.move(0, smooth=3)

    voice_player.play('mask_no_person')

# ---------------------------------------------------------------

# 상태에 따른 동작 함수들 -----------------------------------------
def on_baricade_close():
    lcd.lcd_display_string('   Waiting user..   ', 2)
    lcd.lcd_display_string('                    ', 3)

    clear_user_checks()

    ultrasonic_right.queue_len = 30

    #초음파센서 사람 없으면 패스
    while ultrasonic_right.detect() == False: pass

    #greeting 음성 출력
    voice_player.play('greeting')

    #다음 상태로 전환
    global system_state
    system_state = State.WAIT_APPROCH_PERSON

    #LCD 출력
    lcd.lcd_display_string('      Welcome!      ', 2)
    lcd.lcd_display_string('                    ', 3)

def on_wait_approach_person():
    global system_state
    global mask_checked

    if mask_checked == True:    #이미 했으면 스킵
        system_state = State.WAIT_MEASURE_TEMP
        return

    #오른쪽 초음파 둔감하게하기
    ultrasonic_right.queue_len = 100

    #소켓 버퍼 비우기(이전 측정 결과가 남아있기 때문)
    socket_client.receive_buffer[SOCKET_HOST].clear()

    while True:
        # 사용자가 사라지는지 모니터링
        if expect(ultrasonic_right.detect, False, when_person_vanish): break

        res = detect_mask(voice=True)
        sleep(0.2)  #메세지 전송 딜레이

        if res == 'NO_PERSON':
            print('there is no person')

            lcd.lcd_display_string('  [Mask Detection]  ', 2)
            lcd.lcd_display_string('Plz stare the camera', 3)

            voice_player.play('mask_no_person')

            #카메라 각도 조정 스레드 시작
            global camera_servo_th
            if camera_servo_th == None or not camera_servo_th.is_alive():
                camera_servo_th = StopableThread(target=camera_seek_person, args=()).start()
        

        elif res == 'MASK':
            print('mask on')

            lcd.lcd_display_string('  [Mask Detection]  ', 2)
            lcd.lcd_display_string('Ur mask is detected!', 3)

            voice_player.play('mask_detected')
            system_state = State.WAIT_MEASURE_TEMP
            mask_checked = True
        elif res == 'NO_MASK':
            print('no mask')

            lcd.lcd_display_string('  [Mask Detection]  ', 2)
            lcd.lcd_display_string('Plz put your mask on', 3)

            voice_player.play('mask_not_detected')

        if res != 'None': break
        

def on_wait_measure_temp():
    global system_state
    global temperature_checked

    if temperature_checked == True:     #스킵
        system_state = State.WAIT_SANITIZE_HAND
        return

    lcd.lcd_display_string('   [Temp measure]   ', 2)
    lcd.lcd_display_string(' Check Ur body temp ', 3)

    voice_player.play('guide_tempmeter')

    temp_buffer = []

    guide_state = False
    try_cnt = 0

    while True:
        # 사용자가 사라지는지 모니터링
        if expect(ultrasonic_right.detect, False, when_person_vanish): break
        
        mask_label = detect_mask()

        # 사용자가 마스크를 벗는지 모니터링
        if mask_label == 'NO_MASK': when_mask_off(); break
        # 사용자가 카메라에서 사라지는지 모니터링
        elif mask_label == 'NO_PERSON': when_no_person(); break



        temp = tempmeter.peek()[1]

        if temp <= 30: continue

        if guide_state == False:
            lcd.lcd_display_string('   [Temp measure]   ', 2)
            lcd.lcd_display_string(' Start measuring... ', 3)

            voice_player.play('tempmeter_measure_start', join=False)
            guide_state = True

        temp_buffer.append(temp)

        if len(temp_buffer) >= TEMP_BUFFER_MAX:
            avg = sum(temp_buffer) / TEMP_BUFFER_MAX

            if avg > tempmeter.detect_temp: #열이 나는경우
                if try_cnt == 0:
                    lcd.lcd_display_string('   [Temp measure]   ', 2)
                    lcd.lcd_display_string('High temp, Try again', 3)

                    voice_player.play('tempmeter_high_retry')
                    try_cnt += 1
                    guide_state = False
                    temp_buffer.clear()
                    continue
                elif try_cnt == 1:
                    lcd.lcd_display_string('   [Temp measure]   ', 2)
                    lcd.lcd_display_string("Sorry, U can't enter", 3)
                    voice_player.play('tempmeter_high_banned')
                    system_state = State.BARICADE_CLOSE
                    sleep(5)
                    break
            else: #열이 나지 않는경우
                lcd.lcd_display_string('   [Temp measure]   ', 2)
                lcd.lcd_display_string("    Normal temp!    ", 3)
                voice_player.play('tempmeter_normal')
                system_state = State.WAIT_SANITIZE_HAND
                temperature_checked = True
                break

        sleep(0.2)

    
def on_wait_sanitize_hand():
    global system_state
    global sanitizer_checked

    if sanitizer_checked == True:       #스킵
        system_state = State.BARICADE_OPEN
        return

    lcd.lcd_display_string(' [Hand sanitizing]  ', 2)
    lcd.lcd_display_string(" Plz get sanitizer! ", 3)

    voice_player.play('guide_sanitizer', join=False)

    while True:
        # 사용자가 사라지는지 모니터링
        if expect(ultrasonic_right.detect, False, when_person_vanish): break
        
        mask_label = detect_mask()

        # 사용자가 마스크를 벗는지 모니터링
        if mask_label == 'NO_MASK': when_mask_off(); break
        # 사용자가 카메라에서 사라지는지 모니터링
        elif mask_label == 'NO_PERSON': when_no_person(); break

        # 사용자가 손을 집어넣을때까지 기다림
        if expect(pir.detect, True, None):
            #손소독제 펌핑
            servo_sanitizer.move(angle=17, smooth=4).move(angle=-10, smooth=0.2)
            system_state = State.BARICADE_OPEN
            sanitizer_checked = True
            break
        
        sleep(0.2)

def on_baricade_open():
    global system_state
    global mask_checked
    global temperature_checked
    global sanitizer_checked

    #모든 checked 상태 검사
    if mask_checked == True and temperature_checked == True and sanitizer_checked == True:
        lcd.lcd_display_string('     [Very Good]    ', 2)
        lcd.lcd_display_string("Opening Barricade...", 3)

        voice_player.play('barricade_open')
        servo_baricade.move(angle=90, smooth=2)
        system_state = State.WAIT_PERSON_PASS
    elif mask_checked == False:
        system_state = State.WAIT_APPROCH_PERSON; 
    elif temperature_checked == False:
        system_state = State.WAIT_MEASURE_TEMP; 
    elif sanitizer_checked == False:
        system_state = State.WAIT_SANITIZE_HAND; 

def on_person_pass():
    global system_state

    # 사람이 없어지는지 모니터링
    if expect(ultrasonic_right.detect, False, when_person_vanish): return

    mask_label = detect_mask()

    # 사용자가 마스크를 벗는지 모니터링
    if mask_label == 'NO_MASK': when_mask_off(); return
    # 사용자가 카메라에서 사라지는지 모니터링
    elif mask_label == 'NO_PERSON': when_no_person(); return
    
    if ultrasonic_left.detect() == True:
        while True:
            if ultrasonic_left.detect() == False: break
            sleep(0.05)

        lcd.lcd_display_string('     [Watch out]    ', 2)
        lcd.lcd_display_string("Closing Barricade...", 3)

        voice_player.play('barricade_close')
        servo_baricade.move(angle=0, smooth=3)

        init_mask_factor()
        system_state = State.BARICADE_CLOSE

        sleep(5)
# -------------------------------------------------------




# 메인 ------------------------------------------------------------------------------------------------
system_state = State.BARICADE_CLOSE     #초기 상태

lcd.backlight(True)
lcd.lcd_display_string('====================', 1)
lcd.lcd_display_string('      LOADING...    ', 2)
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

