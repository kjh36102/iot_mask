from MP3_Controller import MP3_Controller
mp3 = MP3_Controller('/home/pi/python')#MP3파일 넣을 디렉토리 경로 입력

mp3.play('barricade_close') # mp3 이름 참고해서 사용할 mp3 이름 입력
mp3.play('barricade_open')
mp3.play('high_temp_banned')
mp3.play('high_temp_try_again')
