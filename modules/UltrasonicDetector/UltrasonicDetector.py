import sys
sys.path.append('./modules/Logger')
from Logger import log

#-------------------------------------

from subprocess import run
from gpiozero import DistanceSensor
from time import sleep
from gpiozero.pins.pigpio import PiGPIOFactory

class UltrasonicDetector:
    def __init__(self, echo, trig, daemon_port, detect_range=0.3, max_range=1, queue_len=9,name='no_name', debug=False) -> None:
        #-------------------------
        self.pin_factory = None
        self.sensor = None
        self.name = name
        self.debug = debug
        #-------------------------

        res = run(['sudo', 'pigpiod', '-p', str(daemon_port)], capture_output=True).stderr.decode()

        if res == '':
            log(f'포트번호 {daemon_port} 에서 pigpiod 실행됨', self)
            sleep(0.5)

        self.pin_factory = PiGPIOFactory('127.0.0.1', daemon_port)
        self.sensor = DistanceSensor(echo=echo, trigger=trig, threshold_distance=detect_range, max_distance=max_range, queue_len=queue_len,pin_factory=self.pin_factory)

        log(f'초음파센서 {self.name} 이(가) 초기화 됨', self)
    
    def __del__(self):
        log(f'({self.name}) 삭제됨', self)
    
    def distance(self):
        log(f'({self.name}) 거리: {self.sensor.distance}', self)
        return self.sensor.distance

    def detect(self):
        log(f'({self.name}) 측정 결과: {self.sensor.in_range}', self)
        return self.sensor.in_range

    def set_detect_range(self, value):
        self.sensor.threshold_distance = value

    def set_max_range(self, value):
        self.sensor.max_distance = value

