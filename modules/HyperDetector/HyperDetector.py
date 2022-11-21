# #HyperDetector.py

import sys
sys.path.append('./modules/StopableThread')

from StopableThread import StopableThread
import RPi.GPIO as GPIO
import time

class HyperDetector(StopableThread):
    def __init__(self):
        super().__init__()

        #--------------------------------
        self.measure_cursor = 0
        self.weight = 10
        self.interval = 0.2
        self.detectors = {}
        self.register_cnt = 0
        #--------------------------------
    
    def __del__(self):
        #GPIO cleanup
        for name in self.detectors:
            detector = self.detectors[name]
            echo = detector['echo']
            trig = detector['trig']

            GPIO.cleanup([echo, trig])

    def register(self, name, echo, trig, detect_point, accept_range):
        self.detectors[name] = {
            'name': name,
            'trig': trig,
            'echo': echo,
            'detect_point': detect_point,
            'accept_range': accept_range,
            'detect_state': False,
            'measure_list': []
        }

        #GPIO 초기화
        GPIO.setup(echo, GPIO.IN)
        GPIO.setup(trig, GPIO.OUT)
        GPIO.output(trig, False)

        #measure_list 초기화
        for i in range(self.weight):
            self.detectors[name]['measure_list'].append(0)
        
        self.register_cnt += 1

    def loop(self):
        for name in self.detectors:
            detector = self.detectors[name]

            GPIO.output(detector['trig'], True)
            time.sleep(0.000000001)
            GPIO.output(detector['trig'], False)

            while GPIO.input(detector['echo']) == 0: start = time.time()
            while GPIO.input(detector['echo']) == 1: stop = time.time()

            measured_time = stop - start
            distance = measured_time * 34300 / 2

            if self.__is_in_range(detector['detect_point'], detector['accept_range'], distance) and detector['detect_state'] == False:
                detector['measure_list'] = [distance for i in range(self.weight)]
                detector['detect_state'] = True
            else:
                detector['detect_state'] = False
            
            detector['measure_list'][self.measure_cursor] = distance

            time.sleep(self.interval / self.register_cnt)

        
        self.measure_cursor += 1
        if self.measure_cursor >= self.weight: self.measure_cursor = 0
        
    def __is_in_range(self, center, range, value):
        if value >= center - range and value <= center + range: return True
        else: return False
    
    def get_avg_value(self, name) -> float:
        '''
        측정 평균값을 리턴하는 함수
        '''
        detector = self.detectors[name]
        return round(sum(detector['measure_list']) / self.weight, 2)

    def set_detect_point(self, name, value):
        detector = self.detectors[name]

        detector['detect_point'] = value

    def set_accept_range(self, name, value):
        detector = self.detectors[name]

        detector['accpet_range'] = value

    def detect(self, name):
        detector = self.detectors[name]

        return self.__is_in_range(detector['detect_point'], detector['accept_range'], self.get_avg_value(name))

    

    

    