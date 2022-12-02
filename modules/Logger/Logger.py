from time import strftime, localtime, time

def log(called_instance, *msg):
    debug_flag = True
    
    if called_instance == None:
        class_name = 'MAIN'
    else:
        class_name = called_instance.__class__.__name__
        debug_flag = called_instance.debug

    if debug_flag == True:
        print(f'[{strftime("%H:%M:%S", localtime(time()))}][{class_name}] {str.join(" ", map(str, msg))}\n', end='')
