import threading

class StopableThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)

        self.can_run = threading.Event()
        self.thing_done = threading.Event()
        self.thing_done.set()
        self.can_run.set()    

    def loop(self):
        '''
        자식 클래스에서 오버라이딩 해서 사용, 무한반복함
        '''
        pass

    def run(self):
        while True:
            self.can_run.wait()
            try:
                self.thing_done.clear()
                self.loop()
            finally:
                self.thing_done.set()

    def pause(self):
        '''
        loop()를 반복하기 전에 멈춤
        '''
        self.can_run.clear()
        self.thing_done.wait()

    def resume(self):
        '''
        loop()를 반복함
        '''
        self.can_run.set()