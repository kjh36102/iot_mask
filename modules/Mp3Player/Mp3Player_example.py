from Mp3Player import Mp3Player

# path = '/home/iot/Desktop/iot_mask/TTS_records'   #절대경로
path = './TTS_records'                              #iot_mask폴더 기준 상대경로

my_player = Mp3Player(path)

# my_player.play('high_temp_try_again.mp3')

try:
    while True:
        msg = list(input().split(' '))
        if msg[0] == 'stop':
            my_player.stop()            # stop 입력하면 재생 즉시 멈춤
        elif msg[0] == 'play':
            my_player.play(msg[1])      # play siren 입력하면 siren.mp3 즉시 재생
except Exception:
    pass


    
