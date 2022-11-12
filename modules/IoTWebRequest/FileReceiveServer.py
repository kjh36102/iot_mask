# ===== 서버 환경설정 ==============================
'''
host: 서버 주소
port: 서버 포트
receive_dir: 파일 저장 경로
debug: 디버그 모드
'''
host = '127.0.0.1'
port = '5000'
receive_dir = './received'
debug = True
#==================================================

from flask import Flask, request
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)

@app.route('/__file_send__', methods=['POST'])
def save_image():
  global last_object
  if request.is_json:
    myjson = request.get_json()

    #임시파일로 값 저장
    with open('./.last_received.json', 'w') as outfile:
      json.dump(myjson, outfile, indent=4)

    if debug: print('\033[96m' + 'Object 수신: ' + str(type(myjson['data'])) + '\033[0m')
  else:
    f = request.files['file']
    f.save(receive_dir + '/' + secure_filename(f.filename))

    if debug: print( '\033[96m' + f.filename + ' 이(가) 저장됨' + '\033[0m')
      
  return 'done!'

if __name__=="__main__":
  app.run(host=host, port=port, debug=debug)

def get_last_object():
  try:
    with open('./.last_received.json', 'r') as json_file:
      json_data = json.load(json_file)
      open('./.last_received.json', 'w').write('')
      
    return json_data['data']
  except FileNotFoundError:
    print('\033[95m' + 'last_received.json 파일이 없습니다!' + '\033[0m')
    return None
  except json.JSONDecodeError:
    print('\033[95m' + '이미 값을 읽었습니다!' + '\033[0m')
    return None