import RPi.GPIO as GPIO
import time
from datetime import datetime
import cv2
import sys
import numpy
from firebase_admin import credentials, initialize_app, storage

# Init firebase with your credentials
cred = credentials.Certificate("one-meter-clip-08d29e2b9d31.json")
initialize_app(cred, {'storageBucket': "one-meter-clip-default-rtdb.firebaseio.com"})


#faceimg
# Put your local file path 
fileName = "result.jpg"
bucket = storage.bucket("one-meter-clip.appspot.com")
blob = bucket.blob(fileName)

#opencv camera
cascPath = "haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascPath)

#capture video
video_capture = cv2.VideoCapture(0)

#pin config
TRIG=21
ECHO=20
LED=16

GPIO.setmode(GPIO.BCM)
GPIO.setup(LED, GPIO.OUT)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

while True:
    #ULTRASONIC
    GPIO.output(TRIG, False)
    time.sleep(0.5)
    GPIO.output(TRIG, True)
    time.sleep(0.001) #Wait for 10micro seconds
    GPIO.output(TRIG, False)
    while GPIO.input(ECHO)==0:
        pulse_start=time.time()
    while GPIO.input(ECHO)==1:
        pulse_end=time.time()
    pulse_duration = pulse_end-pulse_start
    #CALCULATE DISTANCE
    distance = pulse_duration * 17150
    distance = round(distance,2)
    
    #If some one less than 1m
    if(distance < 100):
        print("Distance : ", distance, " cm")
        
        now = datetime.now()
        # dd/mm/YY H:M:S
        dt_string = now.strftime("%d:%m:%Y-%H:%M:%S")
        fName = dt_string+".jpg"
        
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
        
         #check face count
        if len(faces) == 0: #if no face detected
            GPIO.output(LED, 0)
            print ("No faces found")
     
        else:     #if face detected
            GPIO.output(LED, 1)
            print (faces)
            print ("Number of faces detected: " + str(faces.shape[0]))



            # Draw a rectangle around the faces
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.imwrite('result.jpg',frame)
                
            #upload image
            blob.upload_from_filename(fileName)
            bucket.rename_blob(blob , fName)
            # public access from the URL
            bucket.blob(fName).make_public()

    
    #if not ayone near less than 1m
    else :
        GPIO.output(LED, 0)
        print("Distance : ", distance, " cm")
time.sleep(2)