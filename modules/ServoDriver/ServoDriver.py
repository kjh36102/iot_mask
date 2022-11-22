# sudo pigpiod 실행해야함

from gpiozero import Servo
import math
import time
from gpiozero.pins.pigpio import PiGPIOFactory
import threading

DELAY_MAX = 0.6 #끝에서 끝까지 필요한 시간

pi_gpio_factory = PiGPIOFactory('127.0.0.1')

def map_value(x, in_min, in_max, out_min, out_max):
    return float((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

class ServoDriver:
    def __init__(self, pin, init_angle=0):
        self.servo = Servo(pin, min_pulse_width=0.5/1000, max_pulse_width=2.5/1000, pin_factory=pi_gpio_factory)
        self.current_angle = None
        self.command_buffer = []
        self.thread_lock = False

        if self.current_angle == None:
            self.move(init_angle, DELAY_MAX)
        else:
            self.move(init_angle)
    
    def __set_angle(self):
        self.thread_lock = True     #스레드 잠금 (command_buffer를 비우는 도중 move가 호출될 시, 새 스레드 생성을 방지)

        while len(self.command_buffer) > 0:
            command = self.command_buffer.pop(0)
            angle = command[0]
            delay = command[1]

            self.servo.value = math.sin(math.radians(angle))
            
            if delay is None:   #최적 delay 자동계산, 현재 각도와 목표 각도의 차이로 계산
                delay = map_value(abs(self.current_angle - angle), 0, 180, 0, DELAY_MAX)

            time.sleep(delay)

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
            th1 = threading.Thread(target=self.__set_angle)
            th1.start()
