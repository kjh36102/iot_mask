
from StopableThread import StopableThread
import time

cnt = 0

def counter(a, b, c):
    global cnt
    while True:    
        print(f'cnt: {cnt}, a: {a}, b: {b}, c: {c}')
        cnt += 1
        time.sleep(1)


my_th = StopableThread(target=counter, args=(1, 3, 2))
my_th.start()

try:
    while True:
        msg = input()

        if msg == 'stop':
            print('alive state:', my_th.is_alive())
            my_th.stop()
            time.sleep(1)
            print('alive state:', my_th.is_alive())

except KeyboardInterrupt:
    print('main end')