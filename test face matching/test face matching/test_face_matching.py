import time
import pyrebase
from datetime import datetime
import cv2
import sys
import numpy
from firebase_admin import credentials, initialize_app, storage
import face_recognition 

#opencv camera
cascPath = "haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascPath)

#capture video
video_capture = cv2.VideoCapture(0)

while True:        
    #detect faces
    # Capture frame-by-frame
    ret, frame = video_capture.read()

    #convert frame into grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
    #detectfaces
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    
    if len(faces) > 0: #if no face detected

    # Draw a rectangle around the faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.imwrite('result.jpg',gray)
        print(str(len(faces)) + " found!!")
        known_image = face_recognition.load_image_file("result.jpg") 
        biden_encoding = face_recognition.face_encodings(known_image)[0] 
        for i in range(1,8) :
            unknown_image = face_recognition.load_image_file(str(i)+".jpg")  
            unknown_encoding = face_recognition.face_encodings(unknown_image)[0] 
 
            results = face_recognition.compare_faces([biden_encoding], unknown_encoding) 
            print(results)

    # Display the resulting frame
    cv2.imshow('Video', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture
video_capture.release()
cv2.destroyAllWindows()
           

