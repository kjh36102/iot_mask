#pc에서 실행될 코드

# USAGE
# python detect_mask_video.py

#http://192.168.1.5:8080/
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
import os
from SocketConnection import SocketServer, local_ip
my_server = SocketServer(port=20000, debug=True)
my_server.start()
print(local_ip())
def detect_and_predict_mask(frame, faceNet, maskNet):
   # grab the dimensions of the frame and then construct a blob
   # from it
   (h, w) = frame.shape[:2]
   blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300),
      (104.0, 177.0, 123.0))

   # pass the blob through the network and obtain the face detections
   faceNet.setInput(blob)
   detections = faceNet.forward()

   # initialize our list of faces, their corresponding locations,
   # and the list of predictions from our face mask network
   faces = []
   locs = []
   preds = []

   # loop over the detections
   for i in range(0, detections.shape[2]):
      # extract the confidence (i.e., probability) associated with
      # the detection
      confidence = detections[0, 0, i, 2]

      # filter out weak detections by ensuring the confidence is
      # greater than the minimum confidence
      if confidence > args["confidence"]:
         # compute the (x, y)-coordinates of the bounding box for
         # the object
         box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
         (startX, startY, endX, endY) = box.astype("int")

         # ensure the bounding boxes fall within the dimensions of
         # the frame
         (startX, startY) = (max(0, startX), max(0, startY))
         (endX, endY) = (min(w - 1, endX), min(h - 1, endY))

         # extract the face ROI, convert it from BGR to RGB channel
         # ordering, resize it to 224x224, and preprocess it
         face = frame[startY:endY, startX:endX]
         if face.any():
            face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            face = cv2.resize(face, (224, 224))
            face = img_to_array(face)
            face = preprocess_input(face)

            # add the face and bounding boxes to their respective
            # lists
            faces.append(face)
            locs.append((startX, startY, endX, endY))

   # only make a predictions if at least one face was detected
   if len(faces) > 0:
      # for faster inference we'll make batch predictions on *all*
      # faces at the same time rather than one-by-one predictions
      # in the above `for` loop
      faces = np.array(faces, dtype="float32")
      preds = maskNet.predict(faces, batch_size=32)

   # return a 2-tuple of the face locations and their corresponding
   # locations
   return (locs, preds)

# construct the argument parser and parse the arguments
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

# load our serialized face detector model from disk
print("[INFO] loading face detector model...")
prototxtPath = os.path.sep.join([args["face"], "deploy.prototxt"])
weightsPath = os.path.sep.join([args["face"],
   "res10_300x300_ssd_iter_140000.caffemodel"])
faceNet = cv2.dnn.readNet(prototxtPath, weightsPath)

# load the face mask detector model from disk
print("[INFO] loading face mask detector model...")
maskNet = load_model(args["model"])

# initialize the video stream and allow the camera sensor to warm up
print("[INFO] starting video stream...")
vs = VideoStream("http://" + CAMERA_PI + ":8080/stream/video.mjpeg").start()
#vs = VideoStream(src=0).start()
time.sleep(2.0)
# loop over the frames from the video stream

while True:
   label = "NO_PERSON:0"
   # grab the frame from the threaded video stream and resize it
   # to have a maximum width of 400 pixels
   # 여기에 초음파로 인식되었을 때 여기서부터 시작
   text = my_server.next(SENSOR_PI)
   time.sleep(0.1)
   if text != None :

      frame = vs.read()

      try:
         frame = imutils.resize(frame, width=400)
      except AttributeError:
         continue

         # detect faces in the frame and determine if they are wearing a
         # face mask or not
         
         
      (locs, preds) = detect_and_predict_mask(frame, faceNet, maskNet)

         # loop over the detected face locations and their corresponding
         # locations
      for (box, pred) in zip(locs, preds):
            # unpack the bounding box and predictions
         (startX, startY, endX, endY) = box
         (mask, withoutMask) = pred

            # determine the class label and color we'll use to draw
            # the bounding box and text
      
         label = "MASK" if mask > withoutMask else "NO_MASK"
         color = (0, 255, 0) if label == "MASK" else (0, 0, 255)
               
            # include the probability in the label
         label = "{}:{:.2f}".format(label, max(mask, withoutMask) * 100)

            # display the label and bounding box rectangle on the output
            # frame
            
         cv2.putText(frame, label, (startX, startY - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
         cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)
         #print(startX, startY, color)
         break
         # show the output frame
      cv2.imshow("Frame", frame)
      key = cv2.waitKey(1) & 0xFF
      my_server.send(label, SENSOR_PI)
         # if the `q` key was pressed, break from the loop
      
      print(label)
      if key == ord("q"):
         break
#else:
#   continue

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()