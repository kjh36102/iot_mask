import os
import pygame
import time
import threading
from mutagen.mp3 import MP3     #pip install mutagen

class Mp3Player():
    def __init__(self, target_path):
        self.target_path =  os.path.abspath(target_path)
        self.last_played = 'None'
        self.mute_state = False
        pygame.mixer.init()

    def __play_action(self, file_name):
        pygame.mixer.music.load(self.target_path + '/' + file_name + '.mp3')
        pygame.mixer.music.play()
        time.sleep(self.__get_mp3_len(file_name))

    def __play(self, file_name, join):
        # self.mute_state = False

        self.th = threading.Thread(target=self.__play_action, args=(file_name, ))
        self.th.daemon = True
        
        if join == True: self.th.run()
        else: self.th.start()

    def play(self, file_name, join=True):
        if file_name == self.last_played or self.mute_state == True: return

        self.__play(file_name, join)
        self.last_played = file_name

    def replay(self, join=True):
        self.__play(self.last_played, join)

    def stop(self):
        pygame.mixer.music.stop()

    def mute(self):
        self.mute_state = True

    def speak(self):
        self.mute_state = False

    def __get_mp3_len(self, file_name):
        time = MP3(self.target_path + '/' + file_name + '.mp3').info.length
        rnd_time = round(time)

        if time - rnd_time > 0: return rnd_time + 0.5
        else: return rnd_time

    


