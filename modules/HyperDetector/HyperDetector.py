#HyperDetector.py

import threading as th
import RPi.GPIO as GPIO
import time

class HyperDetector(th.Thread):

    def __init__(self, echo_pin, trig_pin, 
                                            interval=0.1,
                                            weight=20,
                                            name='no_name', 
                                            accept_range=20, 
                                            debug=False):
        super().__init__()
        self.daemon = True

        self.stop_flag = False
        self.measure_list = []
        self.measure_cursor = 0
        self.weight = weight
        self.interval = interval
        self.echo_pin = echo_pin
        self.trig_pin = trig_pin
        self.name = name
        self.detect_point = None
        self.accept_range = accept_range
        self.detect_state = False
        self.debug = debug
        
        for i in range(self.weight):
            self.measure_list.append(0)

        GPIO.setup(echo_pin, GPIO.IN)
        GPIO.setup(trig_pin, GPIO.OUT)

        GPIO.output(trig_pin, False)


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

            if self.is_in_range(self.detect_point, self.accept_range, distance) and self.detect_state == False:
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

    def is_in_range(self, center, range, value):
        if value >= center - range and value <= center + range: return True
        else: return False

    def stop(self):
        self.stop_flag = True

    def get_avg_value(self):
        return sum(self.measure_list) / self.weight

    def set_detect_point(self, value=None):
        if value == None: measure_point = self.get_avg_value()
        else: measure_point = value

        self.detect_point = measure_point
    
    def set_accept_range(self, value):
        self.accept_range = value

    def detect(self):
        self.detect_state = self.is_in_range(self.detect_point, self.accept_range, self.get_avg_value())
        return self.detect_state
