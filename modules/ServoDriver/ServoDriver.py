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
        self.daemon_port = daemon_port
        self.pin = pin
        self.init_angle = init_angle
        self.current_angle = None
        self.command_buffer = []
        self.thread_lock = False
        self.debug = debug
        #-----------------------------------------

        

    def start(self):
        res = run(['sudo', 'pigpiod', '-p', str(self.daemon_port)], capture_output=True).stderr.decode()

        if res == '':
            log(f'포트번호 {self.daemon_port} 에서 pigpiod 실행됨', self)
            sleep(0.5)

        self.pin_factory = PiGPIOFactory('127.0.0.1', self.daemon_port)
        self.servo = Servo(self.pin, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory=self.pin_factory)

        if self.current_angle == None:
            self.move(self.init_angle, delay=DELAY_MAX)
        else:
            self.move(self.init_angle)
        
        log(f'서보모터 {self.name} 이(가) 초기화 됨', self)
    
    def __del__(self):
        log(f'({self.name}) 삭제됨', self)

    def __set_angle(self):
        self.thread_lock = True     #스레드 생성 잠금 (command_buffer를 비우는 도중 move가 호출될 시, 새 스레드 생성을 방지)

        while len(self.command_buffer) > 0: #버퍼를 비울때까지 계속
            command = self.command_buffer.pop(0)
            angle = command[0]
            delay = command[1]
            smooth = command[2]

            if delay is None:   #최적 delay 자동계산, 현재 각도와 목표 각도의 차이로 계산
                delay = map_value(abs(self.current_angle - angle), 0, 180, 0, DELAY_MAX)

            # if smooth == 1.0:
            #     self.servo.value = sin(radians(angle))
            #     log(f'({self.name}) 각도 조정 {self.current_angle} -> {angle}', self)

            #     sleep(delay)
            # else:
                # sliced_delay = delay / abs(self.current_angle - angle)
                
                i = self.current_angle
                sliced_angle = (1 if self.current_angle - angle <= 0 else -1) / smooth
                print('smooth:', smooth, 'sliced_angle:', sliced_angle)

                while True:
                    self.servo.value = sin(radians(i))
                    print('moving:', self.servo.value)
                    i += sliced_angle

                    if (sliced_angle < 0 and i < angle) or (sliced_angle > 0 and i > angle): break
                    sleep(0.01)

                # for angle in range(self.current_angle, angle, (1 if self.current_angle - angle >= 0 else -1) / smooth):
                #     self.servo.value = sin(radians(angle))
                #     sleep(sliced_delay * smooth)

            self.current_angle = angle
        
        self.thread_lock = False

    def move(self, angle, delay=None, smooth=5.0):
        '''
        서보모터의 각도를 움직이는 함수, 스레드로 동작함
        Args
            angle: 원하는 각도
            delay: 소요시간(None이면 최적의 시간 자동계산)
        '''
        self.command_buffer.append((angle, delay, smooth))  #command_buffer에 추가

        if self.thread_lock == False:   #스레드 시작
            th1 = Thread(target=self.__set_angle)
            th1.start()

def map_value(x, in_min, in_max, out_min, out_max):
    return float((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)