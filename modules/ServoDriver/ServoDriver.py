import sys
sys.path.append('./modules/Logger')
from Logger import log

#-------------------------------------

from subprocess import run
from math import sin, radians
from time import sleep
from gpiozero import Servo
from gpiozero.pins.pigpio import PiGPIOFactory
from threading import Thread

DELAY_MAX = 0.6 #끝에서 끝까지 필요한 시간

class ServoDriver:
    def __init__(self, pin, daemon_port, init_angle=0, name='no_name', debug=False):
        #-----------------------------------------
        self.pin_factory = None
        self.servo = None
        self.name = name
        self.current_angle = None
        self.command_buffer = []
        self.thread_lock = False
        self.debug = debug
        #-----------------------------------------

        res = run(['sudo', 'pigpiod', '-p', str(daemon_port)], capture_output=True).stderr.decode()

        if res == '':
            log(f'포트번호 {daemon_port} 에서 pigpiod 실행됨', self)
            sleep(0.5)

        self.pin_factory = PiGPIOFactory('127.0.0.1', daemon_port)
        self.servo = Servo(pin, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory=self.pin_factory)

        if self.current_angle == None:
            self.move(init_angle, DELAY_MAX)
        else:
            self.move(init_angle)
        
        log(f'서보모터 {self.name} 이(가) 초기화 됨', self)
    
    def __del__(self):
        log(f'({self.name}) 삭제됨', self)

    def __set_angle(self):
        self.thread_lock = True     #스레드 생성 잠금 (command_buffer를 비우는 도중 move가 호출될 시, 새 스레드 생성을 방지)

        while len(self.command_buffer) > 0: #버퍼를 비울때까지 계속
            command = self.command_buffer.pop(0)
            angle = command[0]
            delay = command[1]

            self.servo.value = sin(radians(angle))
            log(f'({self.name}) 각도 조정 {self.current_angle} -> {angle}', self)
            
            if delay is None:   #최적 delay 자동계산, 현재 각도와 목표 각도의 차이로 계산
                delay = map_value(abs(self.current_angle - angle), 0, 180, 0, DELAY_MAX)

            sleep(delay)

            self.current_angle = angle
        
        self.thread_lock = False

    def move(self, angle, delay=None):
        '''
        서보모터의 각도를 움직이는 함수, 스레드로 동작함
        Args
            angle: 원하는 각도
            delay: 소요시간(None이면 최적의 시간 자동계산)
        '''
        self.command_buffer.append((angle, delay))  #command_buffer에 추가

        if self.thread_lock == False:   #스레드 시작
            th1 = Thread(target=self.__set_angle)
            th1.start()

def map_value(x, in_min, in_max, out_min, out_max):
    return float((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)