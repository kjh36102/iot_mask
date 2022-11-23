from InfraredTempmeter import InfraredTempmeter
import time

my_tempmeter = InfraredTempmeter(name='체온센서', detect_temp=30, debug=True)
my_tempmeter.start()

try:
    while True:
        values = my_tempmeter.peek()
        my_tempmeter.detect()
        time.sleep(0.5)

except KeyboardInterrupt:
    pass