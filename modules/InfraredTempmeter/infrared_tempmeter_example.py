from InfraredTempmeter import InfraredTempmeter
import time

my_tempmeter = InfraredTempmeter()
my_tempmeter.start()

try:
    while True:
        msg = input()

        if msg == 'start':
            my_tempmeter.start()
        elif msg == 'stop':
            my_tempmeter.stop()

        values = my_tempmeter.peek()
        print(f'센서 온도: {values[0]}, 물체 온도: {values[1]}')
        time.sleep(0.5)

except Exception as e:
    print(e)
    pass