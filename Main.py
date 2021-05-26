'''
Project : One-Meter-Clip
language : python
Created On : 16-02-2021
2nd Year Final Project
*Run On Raspberry pi
'''

#import required libraries
import RPi.GPIO as GPIO
import time
import pyrebase
from datetime import datetime
from datetime import timedelta 
import cv2
import sys
import numpy
import os
from firebase_admin import credentials, initialize_app, storage
import face_recognition 

# Init firebase with your credentials
cred = credentials.Certificate("one-meter-clip-08d29e2b9d31.json")
initialize_app(cred, {'storageBucket': "one-meter-clip-default-rtdb.firebaseio.com"})

#firebase configs
config = {
  "apiKey": "rafeFeNHofRgUm///////LYymZzI9qpoX3i0HDh4V",
  "authDomain": "one-meter-clip.firebaseapp.com",
  "databaseURL": "https://one-meter-clip-default-rtdb.firebaseio.com",
  "storageBucket": "one-meter-clip.appspot.com"
}

#firbase initialization
firebase = pyrebase.initialize_app(config)
db = firebase.database()

# local file path for last person
fileName = "result.jpg"

#cloud bucket 
bucket = storage.bucket("one-meter-clip.appspot.com")
blob = bucket.blob(fileName)

#opencv camera fase xml file
cascPath = "haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascPath)

#capture video
video_capture = cv2.VideoCapture(0)

#pin config
TRIG=21
ECHO=20
BUZ=16

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZ, GPIO.OUT)
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

    #CALCULATE DISTANCE    (17150 is a constant)
    distance = pulse_duration * 17150
    distance = round(distance,2)
    
    #If some one less than 1m
    if(distance < 100):
        print("Distance : ", distance, " cm")
        
        now = datetime.now()
        
        #images name making
        imgName = now.strftime("%M%S")

        #for for loops (calculate index using time)
        index = int(imgName)

        #befor 15 seconds time
        time1 = datetime.now() - timedelta(seconds=15)

        #before 30 seconds time for detect followers
        time2 = datetime.now() - timedelta(seconds=30)

        #time before 2 minitues for delete images to avoid storage filling
        time3 = datetime.now() - timedelta(seconds=120)

        #for for loops (calculate index using time)
        index1 = int(time1.strftime("%M%S"))
        index2 = int(time2.strftime("%M%S"))
        index3 = int(time3.strftime("%M%S"))

        #file name for known image
        fName = imgName+".jpg"

        #make renamed file name
        dt_string = now.strftime("%d:%m:%Y-%H:%M:%S")
        fName1 = dt_string+".jpg"        

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
            GPIO.output(BUZ, 0)
            print ("No faces found")
            db.child("/distance").set(distance)
            db.child("/faces").set(str(0))
            db.child("/match").set(0)
     
        else:     #if face detected
            GPIO.output(BUZ, 1)
            time.sleep(0.1)
            GPIO.output(BUZ, 0)
            print (faces)
            print ("Number of faces detected: " + str(faces.shape[0]))

            # Draw a rectangle around the faces
            for (x, y, w, h) in faces:
                #cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.imwrite('result.jpg',frame)
                cv2.imwrite(fName,gray)

            #set known image
            try : 
                known_image = face_recognition.load_image_file(fName) 
                biden_encoding = face_recognition.face_encodings(known_image)[0] 
            except : 
                print("error")

            #match faces on first 15 sec
            for i in range(index,index1,-1) :
                try : 
                    #unknown image matching with known image
                    unknown_image = face_recognition.load_image_file(str(i)+".jpg")  
                    unknown_encoding = face_recognition.face_encodings(unknown_image)[0] 
                    results = face_recognition.compare_faces([biden_encoding], unknown_encoding) 

                    if (results == [True]) : #if match found
                        #match faces on second 15 sec
                        for x in range(index1,index2,-1) :
                            try : 
                                unknown_image = face_recognition.load_image_file(str(x)+".jpg")  
                                unknown_encoding = face_recognition.face_encodings(unknown_image)[0] 
                                results = face_recognition.compare_faces([biden_encoding], unknown_encoding)

                                #if match found
                                if (results == [True]) : 
                                    print("Found Match!! " + str(x)+ ".jpg")    
                                    #upload image
                                    blob.upload_from_filename(str(x)+".jpg")
                                    bucket.rename_blob(blob , "match"+str(x)+".jpg")
                                    # public access from the URL
                                    bucket.blob("match"+str(x)+".jpg").make_public()

                                    #set as found follower
                                    db.child("/match").set(1)
                                    #last follower image url
                                    db.child("/last_follower").set(bucket.blob("match"+str(x)+".jpg").public_url)
                            except : 
                                continue
                except : 
                     continue             
                    
            #upload image
            blob.upload_from_filename(fileName)
            bucket.rename_blob(blob , fName1)
            # public access from the URL
            bucket.blob(fName1).make_public()

            #upload data to firebase
            data = {
                "distance": distance,
                "faces" : str(faces.shape[0]),
                "last person" : bucket.blob(fName1).public_url
            }
            
            db.update(data)
    
    #if not ayone near less than 1m
    else :
        print("Distance : ", distance, " cm")
        db.child("/distance").set(distance)
        db.child("/faces").set(str(0))
        db.child("/match").set(0)
        
    #delete unwanted images
    try :
        #run for loop to delete images on last 2 minitues
        for z in range(index2,index3,-1) : 
            #check if image exist or not with file name
                if os.path.exists(str(z)+".jpg"):
                    #remove unwanted images
                    os.remove(str(z)+".jpg")
                    print("file deleted!!")
    except :
        print("Error")
