#ServoDriver.py 사용을 위한 예시코드
#스레드를 사용해서 서보모터의 개별제어 가능

from ServoDriver import ServoDriver
import time

servo1_pin = 18

servo1 = ServoDriver(servo1_pin, init_angle=90, daemon_port=20001).start()
smooth = 1

try:
    while True:
        msg = input().split(' ')

        if msg[0] == 'move':
            servo1.move(angle=float(msg[1]), smooth=smooth)
        elif msg[0] == 'set_smooth':
            smooth = float(msg[1])
        elif msg[0] == 'smooth_move':
            current = servo1.current_angle
            angle = float(msg[1])
            slow_point = current + (angle - current) * 0.7
            print('current:', current, ', angle:', angle, ', slow_point:', slow_point)
            servo1.move(angle=slow_point, smooth=smooth)
            servo1.move(angle=angle, smooth=2.5 * smooth)
        elif msg[0] == 'pump':
                servo1.move(angle=10, smooth=3)
                servo1.move(angle=-15, smooth=0.5)

except KeyboardInterrupt:
    pass





print('servo_test.py end..')

#GPIO.cleanup() 호출하면 서보모터 안움직임, ServoDriver 내에서 알아서 cleanup 하게 만들어놓음.
