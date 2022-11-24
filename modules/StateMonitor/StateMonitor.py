import sys
sys.path.append('./modules/Logger')
sys.path.append('./modules/StopableThread')
from Logger import log
from StopableThread import StopableThread

#-------------------------------------

class StateMonitor(StopableThread):
    def __init__(self):
        super().__init__(daemon=True)
        
        self.runnable = None

    def check_not_match(target_runnable, expect_return_value, callback):
        if target_runnable() != expect_return_value: callback()

    

        