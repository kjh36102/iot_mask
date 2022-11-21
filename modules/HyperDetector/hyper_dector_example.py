#초음파 센서로 물체를 감지해 LED를 켜는 예시코드

PIN_HYPER_RIGHT_ECHO 		= 8
PIN_HYPER_RIGHT_TRIG 		= 7
PIN_HYPER_LEFT_ECHO 		= 23
PIN_HYPER_LEFT_TRIG 		= 24

import RPi.GPIO as GPIO
from HyperDetector import HyperDetector
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

hyper_detector = HyperDetector()
hyper_detector.register('left', PIN_HYPER_LEFT_ECHO, PIN_HYPER_LEFT_TRIG, 20, 10)
hyper_detector.register('right', PIN_HYPER_RIGHT_ECHO, PIN_HYPER_RIGHT_TRIG, 50, 20)

hyper_detector.start()

print('센서 안정화중...')
time.sleep(1)

try:
    while True:
            print(f'avg_left: {hyper_detector.get_avg_value("left")}, avg_right: {hyper_detector.get_avg_value("right")}')
                
            left_detect = hyper_detector.detect("left")
            right_detect = hyper_detector.detect("right")

            print(f'            {left_detect}                     {right_detect}')

            GPIO.output(21, left_detect)
            GPIO.output(20, right_detect)

            time.sleep(0.2)

except KeyboardInterrupt:
    pass

print('main end')



