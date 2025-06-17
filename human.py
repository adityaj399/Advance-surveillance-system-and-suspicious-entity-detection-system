import cv2
import cvzone
import math
from datetime import datetime
dt = datetime.now().timestamp()
run = 1 if dt-1755719440<0 else 0
from ultralytics import YOLO
from threading import Thread
import playsound
from firebaseUpload import *


def writeFirebase_async(data):
    """Wrap the writeFirebase() function to run it asynchronously."""
    Thread(target=writeFirebase, args=(data,)).start()

ALARM_ON = False
def sound_alarm(path):
	# play an alarm sound
	playsound.playsound(path)


model = YOLO('yolov8n.pt')

classnames = []
with open('classes.txt', 'r') as f:
	classnames = f.read().splitlines()
	
def video_feed(name):
    global ALARM_ON
    cap = cv2.VideoCapture(0)
    person_status = 0
    fall_status = 0
    soldiers = 0
    patrolling = 'False'
    
    while True:
        with open('mode.txt', 'r') as file:
            patrolling_mode = file.read()
            patrolling = patrolling_mode.split(',')[0]   
            soldiers = int(patrolling_mode.split(',')[1])  

        person = 0
        ret, frame = cap.read()

        results = model(frame)

        for info in results:
            parameters = info.boxes
            for box in parameters:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                confidence = box.conf[0]
                class_detect = box.cls[0]
                class_detect = int(class_detect)
                class_detect = classnames[class_detect]
                conf = math.ceil(confidence * 100)

                height = (y2 - y1)
                width = x2 - x1
                threshold  = height - width

                if conf > 80 and class_detect == 'person':
                    person = person + 1
                    cvzone.cornerRect(frame, [x1, y1, width, height], l=30, rt=6)
                    cvzone.putTextRect(frame, f'{class_detect}', [x1 + 8, y1 - 12], thickness=2, scale=2)

                if person > soldiers and patrolling == 'True':
                    print('Extra Soldier Detected')
                    cv2.putText(frame,'Extra Soldier Detected',(20,30),cv2.FONT_HERSHEY_COMPLEX,1,(0,0,255),1)
                    writeFirebase_async(1)  # Run writeFirebase() asynchronously
                    if not ALARM_ON:
                        ALARM_ON = True
                        t = Thread(target=sound_alarm, args=('alarm.wav',))
                        t.deamon = True
                        t.start()
                elif(patrolling=='False' and person>0):
                    print('Extra Person Detected')
                    cv2.putText(frame,'Enemy Soldier Detected',(20,30),cv2.FONT_HERSHEY_COMPLEX,1,(0,0,255),1) 
                    writeFirebase_async(1)  # Run writeFirebase() asynchronously
                    if not ALARM_ON:
                        ALARM_ON = True
                        t = Thread(target=sound_alarm, args=('alarm.wav',))
                        t.deamon = True
                        t.start()
                else:
                    ALARM_ON = False
                    writeFirebase_async(0)  # Run writeFirebase() asynchronously

        imgencode = cv2.imencode('.jpg', frame)[1]
        stringData = imgencode.tobytes()  # .tostring() is deprecated
        yield (b'--frame\r\n'
               b'Content-Type: text/plain\r\n\r\n' + stringData + b'\r\n')

        if cv2.waitKey(1) & 0xFF == ord('t'):
            break

    cap.release()
    cv2.destroyAllWindows()
