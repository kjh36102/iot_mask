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
        self.echo = echo
        self.trig = trig
        self.daemon_port = daemon_port
        self.detect_range = detect_range
        self.max_range = max_range
        self.queue_len = queue_len
        self.name = name
        self.debug = debug
        #-------------------------

        

    def start(self):
        res = run(['sudo', 'pigpiod', '-p', str(self.daemon_port)], capture_output=True).stderr.decode()

        if res == '':
            log(f'포트번호 {self.daemon_port} 에서 pigpiod 실행됨', self)
            sleep(0.5)

        self.pin_factory = PiGPIOFactory('127.0.0.1', self.daemon_port)
        self.sensor = DistanceSensor(echo=self.echo, trigger=self.trig, threshold_distance=self.detect_range, max_distance=self.max_range, queue_len=self.queue_len,pin_factory=self.pin_factory)

        log(f'초음파센서 {self.name} 이(가) 초기화 됨', self)
        return self
    
    def __del__(self):
        log(f'({self.name}) 삭제됨', self)
    
    def distance(self):
        if self.sensor == None: return

        log(f'({self.name}) 거리: {self.sensor.distance}', self)
        return self.sensor.distance

    def detect(self):
        if self.sensor == None: return
        
        log(f'({self.name}) 측정 결과: {self.sensor.in_range}', self)
        return self.sensor.in_range

    def set_detect_range(self, value):
        self.sensor.threshold_distance = value

    def set_max_range(self, value):
        self.sensor.max_distance = value

