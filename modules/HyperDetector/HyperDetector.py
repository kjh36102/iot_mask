#HyperDetector.py

import threading as th
import RPi.GPIO as GPIO
import time

class HyperDetector(th.Thread):
    def __init__(self, echo_pin:int, trig_pin:int, name:str='no_name', debug:bool=False):
        '''
        HyperDetector의 생성자
        Args
            echo_pin: 음파 발생 핀
            trig_pin: 반향 감지 핀
            name: 센서 이름 (디버깅 목적)
            debug: 디버그 여부
        '''
        super().__init__()
        self.daemon = True

        #------------------------------------
        self.stop_flag = False
        self.measure_list = []
        self.measure_cursor = 0
        self.weight = 20
        self.interval = 0.1
        self.echo_pin = echo_pin
        self.trig_pin = trig_pin
        self.name = name
        self.detect_point = None
        self.accept_range = 20
        self.detect_state = False
        self.debug = debug
        #------------------------------------
        
        for i in range(self.weight):
            self.measure_list.append(0)

        GPIO.setup(echo_pin, GPIO.IN)
        GPIO.setup(trig_pin, GPIO.OUT)

        GPIO.output(trig_pin, False)
    
    def __del__(self):
        GPIO.cleanup([self.echo_pin, self.trig_pin])

    def run(self):
        while not self.stop_flag:        
            GPIO.output(self.trig_pin, True)
            time.sleep(0.00001)
            GPIO.output(self.trig_pin, False)

            while GPIO.input(self.echo_pin) == 0:
                    start = time.time()
            while GPIO.input(self.echo_pin) == 1:
                    stop = time.time()

            measured_time = stop - start
            distance = measured_time * 34300 / 2

            if self.__is_in_range(self.detect_point, self.accept_range, distance) and self.detect_state == False:
                self.measure_list = [self.detect_point for i in range(self.weight)]
                self.detect_state = True

            if self.measure_cursor >= self.weight:
                self.measure_cursor = 0

            self.measure_list[self.measure_cursor] = round(distance, 2)

            self.measure_cursor += 1

            if self.debug: 
                print('{0} 의 거리: {1:.1f} cm'.format(self.name, distance))
                print('{0} 의 List: '.format(self.name), end='')
                print(self.measure_list, end='\n\n')
            
            time.sleep(self.interval)
        
        print('HyperDetector %s stopped..' % self.name)

    
    def stop(self):
        '''
        측정을 멈추는 함수
        '''
        self.stop_flag = True

    def get_avg_value(self) -> float:
        '''
        측정 평균값을 리턴하는 함수
        '''
        return sum(self.measure_list) / self.weight

    def set_detect_point(self, value:float=None):
        '''
        측정범위의 정 중앙지점을 설정하는 함수
        Args
            value: 측정범위 중앙지점 설정 (cm단위)
        '''
        if value == None: measure_point = self.get_avg_value()
        else: measure_point = value

        self.detect_point = measure_point
    
    def set_accept_range(self, range:float):
        '''
        측정범위 중앙지점 앞 뒤로 탐지반경을 설정하는 함수
        Args
            range: 측정반경 (cm)
        '''
        self.accept_range = range

    def detect(self) -> bool:
        '''
        탐지결과를 리턴하는 함수
        '''
        self.detect_state = self.__is_in_range(self.detect_point, self.accept_range, self.get_avg_value())
        return self.detect_state

    def __is_in_range(self, center, range, value):
        if value >= center - range and value <= center + range: return True
        else: return False
