#ServoDriver.py 사용을 위한 예시코드
#스레드를 사용해서 서보모터의 개별제어 가능

import RPi.GPIO as GPIO
from ServoDriver import ServoDriver
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

servo1_pin = 13
servo2_pin = 18

servo1 = ServoDriver(servo1_pin, init_angle=-90)
servo2 = ServoDriver(servo2_pin, init_angle=90)

servo1.move(-70)
servo1.move(45)

for i in range(10):
    servo1.move(-20)
    servo1.move(20)

servo2.move(-90)
servo2.move(0)

for i in range(3):
    servo2.move(-90)
    servo2.move(90)

time.sleep(1)
for i in range(5):
    servo1.move(-40)
    servo1.move(40)

for i in range(10):
    servo2.move(-20)
    servo2.move(20)

print('servo_test.py end..')

#GPIO.cleanup() 호출하면 서보모터 안움직임, ServoDriver 내에서 알아서 cleanup 하게 만들어놓음.