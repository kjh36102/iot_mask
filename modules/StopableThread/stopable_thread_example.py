#stop을 입력하면 멈추고, start를 입력하면 다시 시작하는 쓰레드 예제
#모든 센서들의 스레드를 이걸로 교체할 예정

from StopableThread import StopableThread
import time

class MyClass(StopableThread):
    def __init__(self, init_value):
        super().__init__()

        self.cnt = init_value

    def loop(self):
        print('cnt up:', self.cnt)
        self.cnt += 1
        time.sleep(0.5)


my_sth = MyClass(10)
my_sth.start()

try:
    while True:
        msg = input()

        if msg == 'stop':
            my_sth.pause()
        elif msg == 'start':
            my_sth.resume()
except Exception as e:
    print(e)