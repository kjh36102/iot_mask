#초음파 센서로 물체를 감지해 LED를 켜는 예시코드

import RPi.GPIO as GPIO
from HyperDetector import HyperDetector
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

led_pin = 8

GPIO.setup(led_pin, GPIO.OUT)

my_hyper = HyperDetector(
        echo_pin=23, 
        trig_pin=24,
        name='myhyper',
        #interval=0.1,
        #weight=20,  # 둔감도
        #debug=True,
        #accept_range=20 # detect_point로부터의 인식 반경
    )
#my_hyper.set_accept_range(20)
my_hyper.set_detect_point(60)

my_hyper.start()

print('센서 안정화중...')
GPIO.output(led_pin, False)
time.sleep(3)

try:
    while True:
        print('\tavg: ', my_hyper.get_avg_value()) 
        detect = my_hyper.detect()

        if detect: 
            print('detected!')
            GPIO.output(led_pin, True)
        else: 
            print('vanished!')
            GPIO.output(led_pin, False)
        
        time.sleep(0.5)

except KeyboardInterrupt:
    my_hyper.stop()


print('main end')
GPIO.cleanup()



