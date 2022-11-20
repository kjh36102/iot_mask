import pygame
import time
#TTS_records_barricade_close.mp3
class MP3_Controller():
    def play(self, data):
        if data == 'barricade_close' :
            self.barricade_close()
            time.sleep(3)
            return True
        elif data == 'barricade_open':
            self.barricade_open()
            time.sleep(3)
            return True
        elif data == 'high_temp_banned':
            self.high_temp_banned()
            time.sleep(3)
            return True
        elif data == 'high_temp_try_again':
            self.high_temp_try_again()
            time.sleep(3)
            return True
        elif data == 'no_mask':
            self.no_mask()
            time.sleep(3)
            return True
        elif data == 'normal_temp':
            self.normal_temp()
            time.sleep(3)
            return True
        elif data == 'on_trespass':
            self.on_trespass()
            time.sleep(3)
            return True
        elif data == 'please_look_camera':
            self.please_look_camera()
            time.sleep(3)
            return True
        elif data == 'process_aborted':
            self.process_aborted()
            time.sleep(3)
            return True
        elif data == 'put_on_your_mask':
            self.put_on_your_mask()
            time.sleep(3)
            return True
        elif data == 'sanitizer_guide':
            self.sanitizer_guide()
            time.sleep(3)
            return True
        elif data == 'siren':
            self.siren()
            time.sleep(3)
            return True
        elif data == 'sanitizer_guide':
            self.sanitizer_guide()
            time.sleep(3)
            return True
        elif data == 'temp_measure_guide':
            self.temp_measure_guide()
            time.sleep(3)
            return True
        elif data == 'waiting_mask_recognize':
            self.waiting_mask_recognize()
            time.sleep(3)
            return True
        elif data == 'waiting_temp_measuring':
            self.waiting_temp_measuring()
            time.sleep(3)
            return True
    def __init__(self, path):
        pygame.mixer.init()
        self.path = path +'/'
    def barricade_close(self):
        pygame.mixer.music.load(self.path+'barricade_close.mp3')
        pygame.mixer.music.play()
    def barricade_open(self):
        pygame.mixer.music.load(self.path+'barricade_open.mp3')
        pygame.mixer.music.play()
    def high_temp_banned(self):
        pygame.mixer.music.load(self.path+'high_temp_banned.mp3')
        pygame.mixer.music.play()
    def high_temp_try_again(self):
        pygame.mixer.music.load(self.path+'high_temp_try_again.mp3')
        pygame.mixer.music.play()
    def no_mask(self):
        pygame.mixer.music.load(self.path+'no_mask.mp3')
        pygame.mixer.music.play()
    def normal_temp(self):
        pygame.mixer.music.load(self.path+'normal_temp.mp3')
        pygame.mixer.music.play()
    def on_trespass(self):
        pygame.mixer.music.load(self.path+'on_trespass.mp3')
        pygame.mixer.music.play()
    def please_look_camera(self):
        pygame.mixer.music.load(self.path+'please_look_camera.mp3')
        pygame.mixer.music.play()
    def process_aborted(self):
        pygame.mixer.music.load(self.path+'process_aborted.mp3')
        pygame.mixer.music.play()
    def put_on_your_mask(self):
        pygame.mixer.music.load(self.path+'put_on_your_mask.mp3')
        pygame.mixer.music.play()
    def sanitizer_guide(self):
        pygame.mixer.music.load(self.path+'sanitizer_guide.mp3')
        pygame.mixer.music.play()
    def siren(self):
        pygame.mixer.music.load(self.path+'siren.mp3')
        pygame.mixer.music.play()
    def sanitizer_guide(self):
        pygame.mixer.music.load(self.path+'sanitizer_guide.mp3')
        pygame.mixer.music.play()
    def temp_measure_guide(self):
        pygame.mixer.music.load(self.path+'temp_measure_guide.mp3')
        pygame.mixer.music.play()
    def waiting_mask_recognize(self):
        pygame.mixer.music.load(self.path+'waiting_mask_recognize.mp3')
        pygame.mixer.music.play()
    def waiting_temp_measuring(self):
        pygame.mixer.music.load(self.path+'waiting_temp_measuring.mp3')
        pygame.mixer.music.play()
    