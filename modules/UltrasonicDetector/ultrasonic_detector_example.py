import sys
sys.path.append('./modules/UltrasonicDetector')
sys.path.append('./modules/Logger')
from UltrasonicDetector import UltrasonicDetector
from Logger import log

#-------------------------------------------

from time import sleep
import RPi.GPIO as GPIO
from threading import Thread

PIN_LED = 20
PIN_BUZZER = 21

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(PIN_LED, GPIO.OUT)
GPIO.setup(PIN_BUZZER, GPIO.OUT)

sensor1 = UltrasonicDetector(echo=8, trig=7, detect_range=0.3, daemon_port=20001, name='sensor1', debug=True)
sensor2 = UltrasonicDetector(echo=23, trig=24, detect_range=0.5, daemon_port=20001, name='sensor2', debug=True)

def print_out():
    while True:
        log(f'Distance1: {sensor1.distance():.2f}, Distance2: {sensor2.distance():.2f}')
        log(f'in_range1: {sensor1.detect()}, in_range2: {sensor2.detect()}')

        GPIO.output(PIN_LED, sensor1.detect())
        GPIO.output(PIN_BUZZER, sensor2.detect())

        sleep(0.5)

th = Thread(target=print_out)
th.daemon = True
th.start()

try:
    while True:
        msg = input().split(' ')

        if msg[0] == 'detect_point':    #'detect_point 0.1' detect_point를 0.1m로 바꾸기
            sensor1.sensor.threshold_distance = float(msg[1])
except Exception as e:
    print('Exception on MAIN:', e)
    pass

