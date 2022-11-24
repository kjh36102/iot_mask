from threading import Thread
import ctypes 
import time

class StopableThread(Thread): 
    def __init__(self, target=None, args=None): 
        super().__init__(daemon=True)

        self.target = target
        self.args = args

    def register(self, target, args):
        self.target = target
        self.args = args
              
    def run(self):
        if self.target != None:
            self.target(*self.args)
   
    def stop(self): 
        thread_id = self.ident
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 
              ctypes.py_object(SystemExit)) 
        if res > 1: 
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0) 
            print('Failed to stop thread with id', thread_id)