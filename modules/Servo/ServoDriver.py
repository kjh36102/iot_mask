import RPi.GPIO as GPIO
import time
import threading as th

DELAY_MAX = 0.6 #끝에서 끝까지 필요한 시간

class ServoDriver():
    def __init__(self, pin, init_angle=0):
        '''
        ServoDriver의 생성자
          Args
            pin: 핀 번호
            init_angle: 초기화 각도(optional)
        '''
        
        #클래스 변수 생성-------
        self.pin = pin
        self.pwm = None 
        self.current_angle = None
        self.command_buffer = []
        self.thread_lock = False
        #-----------------------

        GPIO.setup(pin, GPIO.OUT)       #pwm 객체 생성 및 시작
        self.pwm = GPIO.PWM(pin, 50)
        self.pwm.start(0)

        if self.current_angle is None:  #init_angle 위치로 이동
            self.move(init_angle, delay=DELAY_MAX)
        else:
            self.move(init_angle)
    
    #소멸자, pwm객체와 GPIO핀을 정리함
    def __del__(self):
        self.pwm.stop()
        GPIO.cleanup(self.pin)


    def move(self, angle, delay=None):
        '''
        서보모터의 각도를 움직이는 함수, 스레드로 동작함
          Args
            angle: 원하는 각도
            delay: 소요시간(None이면 최적의 시간 자동계산)
        '''
        self.command_buffer.append((angle, delay))  #command_buffer에 추가

        if self.thread_lock == False:   #스레드 시작
            th1 = th.Thread(target=self.__set_angle)
            th1.start()

    
    def __set_angle(self):
        self.thread_lock = True     #스레드 잠금 (command_buffer를 비우는 도중 move가 호출될 시, 새 스레드 생성을 방지)

        while len(self.command_buffer) > 0:
            command = self.command_buffer.pop(0)
            angle = command[0]
            delay = command[1]

            if angle == 0:
                duty = 7.5
            elif angle > 0:
                duty = self.__map_value(angle, 0, 90, 7.5, 2.5)
            elif angle < 0:
                duty = self.__map_value(angle, -90, 0, 12.5, 7.5)
            
            self.pwm.ChangeDutyCycle(duty)

            if delay is None:   #최적 delay 자동계산, 현재 각도와 목표 각도의 차이로 계산
                delay = self.__map_value(abs(self.current_angle - angle), 0, 180, 0, DELAY_MAX)

            time.sleep(delay)

            self.current_angle = angle
        
        self.thread_lock = False    #스레드 잠금 해제

    #input output 범위를 맵핑해주는 비례함수
    def __map_value(self, x, in_min, in_max, out_min, out_max):
        return float((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)