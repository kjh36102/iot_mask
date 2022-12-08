import sys
sys.path.append('./modules/Logger')
from Logger import log

from subprocess import run
from time import sleep
from gpiozero import MotionSensor
from gpiozero.pins.pigpio import PiGPIOFactory

class PIR:
    def __init__(self, pin, daemon_port, pull_up=False, active_state=None, queue_len=1, sample_rate=10, threshold=0.5, partial=False):
        self.pin = pin
        self.daemon_port = daemon_port
        res = run(['sudo', 'pigpiod', '-p', str(self.daemon_port)], capture_output=True).stderr.decode()

        if res == '':
            log(f"from port {self.daemon_port} pigpiod started.", self)
            sleep(0.5)

        self.pin_factory = PiGPIOFactory('127.0.0.1', self.daemon_port)

        self.sensor = MotionSensor(pin, pull_up, active_state, queue_len, sample_rate, threshold, partial, self.pin_factory)

    def detect(self):
        return self.sensor.motion_detected