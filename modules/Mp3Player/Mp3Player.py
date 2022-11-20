import os
import pygame
import time
import threading
from mutagen.mp3 import MP3     #pip install mutagen

class Mp3Player():
    def __init__(self, target_path):
        self.target_path =  os.path.abspath(target_path)
        pygame.mixer.init()

    def __play_action(self, file_name):
        pygame.mixer.music.load(self.target_path + '/' + file_name + '.mp3')
        pygame.mixer.music.play()
        time.sleep(self.__get_mp3_len(file_name))

    def play(self, file_name):
        self.th = threading.Thread(target=self.__play_action, args=(file_name, ))
        self.th.daemon = True
        self.th.start()

    def stop(self):
        pygame.mixer.music.stop()

    def __get_mp3_len(self, file_name):
        time = MP3(self.target_path + '/' + file_name + '.mp3').info.length
        rnd_time = round(time)

        if time - rnd_time > 0: return rnd_time + 0.5
        else: return rnd_time

    


