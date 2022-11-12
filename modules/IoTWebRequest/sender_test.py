'''
패키지 인스톨
  pip install flask werkzeug
'''

from FileSender import FileSender

fs = FileSender()

fs.send_file('./data/yee.png')
fs.send_file('./data/pikachu.jpg')
fs.send_file('./data/mask.jpg')

fs.send_file('./data/plain_text.txt')


fs.send_object('Let\'s send a str')
# fs.send_object(['hello', 1, 2, 3.0, True, 'world'])