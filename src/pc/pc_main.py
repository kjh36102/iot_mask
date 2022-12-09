#pc에서 실행될 코드

# USAGE
# python detect_mask_video.py

import sys

#필요한 모듈 불러오기
sys.path.append('./modules/Logger')
sys.path.append('./modules/StopableThread')
sys.path.append('./modules/SocketConnection')

#카메라 설정페이지 주소 http://192.168.1.5:8080/
#webrtc 들어가서 call, hang up 한번씩 눌러주기 (스트리밍 보는장치 다 끄고)

#주소
SENSOR_PI = '192.168.1.2'
CAMERA_PI = '192.168.1.5'

# import the necessary packages\
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from imutils.video import VideoStream
import numpy as np
import argparse
import imutils
import time
import cv2
from SocketConnection import SocketServer, local_ip

print('장치 IP:', local_ip())
def detect_and_predict_mask(frame, faceNet, maskNet):
   (h, w) = frame.shape[:2]
   blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300),
      (104.0, 177.0, 123.0))

   faceNet.setInput(blob)
   detections = faceNet.forward()

   faces = []
   locs = []
   preds = []

   for i in range(0, detections.shape[2]):
      confidence = detections[0, 0, i, 2]

      if confidence > args["confidence"]:
         box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
         (startX, startY, endX, endY) = box.astype("int")
         (startX, startY) = (max(0, startX), max(0, startY))
         (endX, endY) = (min(w - 1, endX), min(h - 1, endY))

         face = frame[startY:endY, startX:endX]
         if face.any():
            face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            face = cv2.resize(face, (224, 224))
            face = img_to_array(face)
            face = preprocess_input(face)

            faces.append(face)
            locs.append((startX, startY, endX, endY))

   if len(faces) > 0:
      faces = np.array(faces, dtype="float32")
      preds = maskNet.predict(faces, batch_size=32)

   return (locs, preds)

#실행에 필요한 argument들 마련하는 부분 인듯
ap = argparse.ArgumentParser()
ap.add_argument("-f", "--face", type=str,
   default="face_detector",
   help="path to face detector model directory")
ap.add_argument("-m", "--model", type=str,
   default="mask_detector.model",
   help="path to trained face mask detector model")
ap.add_argument("-c", "--confidence", type=float, default=0.5,
   help="minimum probability to filter weak detections")
args = vars(ap.parse_args())

print("[INFO] loading face detector model...")

#새롭게 모델파일 경로 지정해주기
prototxtPath = './src/pc/deploy.prototxt'
weightsPath = './src/pc/res10_300x300_ssd_iter_140000.caffemodel'
model_path = './src/pc/mask_detector.model'
faceNet = cv2.dnn.readNet(prototxtPath, weightsPath)

#모델 불러오기
print("[INFO] loading face mask detector model...")
maskNet = load_model(model_path)

#스트리밍 시작하기
print("[INFO] starting video stream...")
vs = VideoStream("http://" + CAMERA_PI + ":8080/stream/video.mjpeg").start()
#vs = VideoStream(src=0).start() #PC웹캠으로 테스트

#메인 시작 -------------------------------------------
time.sleep(2.0)

#소켓통신 서버 시작
my_server = SocketServer(port=20000, debug=True)
my_server.start()

#전송 루프
try:
   while True:
      # 초음파로 인식되었을 때 여기서부터 시작
      label = "NO_PERSON:0"
      
      #데이터 읽기
      text = my_server.next(SENSOR_PI)
      time.sleep(0.1)

      if text == None: continue

      frame = vs.read()
      try:
         frame = imutils.resize(frame, width=400)
      except AttributeError:
         continue

      (locs, preds) = detect_and_predict_mask(frame, faceNet, maskNet)

      for (box, pred) in zip(locs, preds):
         (startX, startY, endX, endY) = box
         (mask, withoutMask) = pred

         #결과값 구성하기
         label = "MASK" if mask > withoutMask else "NO_MASK"
         color = (0, 255, 0) if label == "MASK" else (0, 0, 255)
               
         label = "{}:{:.2f}".format(label, max(mask, withoutMask) * 100)

         cv2.putText(frame, label, (startX, startY - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
         cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)
         #print(startX, startY, color)
         break

      #출력 프레임 보여주기
      cv2.imshow("Frame", frame)
      key = cv2.waitKey(1) & 0xFF

      #소켓통신으로 결과값 보내기
      my_server.send(label, SENSOR_PI)

      # if the `q` key was pressed, break from the loop
      print(label)
      if key == ord("q"):
         break
except KeyboardInterrupt:
   pass

# 마무리 정리
cv2.destroyAllWindows()
vs.stop()