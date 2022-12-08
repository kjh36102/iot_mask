
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

class MyClass(StopableThread):
    def __init__(self, a, b, c):
        super().__init__()

        self.a = a
        self.b = b
        self.c = c

    def run(self):
        try:
            counter(self.a, self.b, self.c)
        except Exception:
            print('MyClass end')

my_class = MyClass(3, 2, 1)

my_class.start()

try:
    while True:
        msg = input()

        if msg == 'stop':
            print('alive state:', my_th.is_alive())
            print('alive state:', my_class.is_alive())
            my_th.stop()
            my_class.stop()
            time.sleep(0.3)
            print('alive state:', my_th.is_alive())
            print('alive state:', my_class.is_alive())

except KeyboardInterrupt:
    print('main end')