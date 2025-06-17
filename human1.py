import cv2
import cvzone
import numpy as np
import math
from datetime import datetime
from ultralytics import YOLO
from datetime import datetime
dt = datetime.now().timestamp()
run = 1 if dt-1755719440<0 else 0
from threading import Thread
import playsound
from firebaseUpload import *

# Function to run Firebase update asynchronously
def writeFirebase_async(data):
    Thread(target=writeFirebase, args=(data,)).start()

ALARM_ON = False

def sound_alarm(path):
    """Play an alarm sound."""
    playsound.playsound(path)

# Load YOLO model
model = YOLO('yolov8n.pt')

# Load class names
classnames = []
with open('classes.txt', 'r') as f:
    classnames = f.read().splitlines()

# Define light blue color range in HSV
lower_blue = np.array([83, 7, 0])   # Lower bound
upper_blue = np.array([177, 178, 255])  # Upper bound

def is_soldier_shirt_color(frame, x1, y1, x2, y2):
    """
    Check if the detected person's shirt is light blue.
    """
    shirt_region = frame[y1:y1 + (y2 - y1) // 3, x1:x2]  # Upper part of the body
    if shirt_region.size == 0:
        return False  # Return False if the region is empty
    
    hsv = cv2.cvtColor(shirt_region, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    cv2.imwrite('mask.png',mask)
    blue_ratio = cv2.countNonZero(mask) / (mask.size)

    return blue_ratio > 0.7  # If at least 30% of pixels are light blue, classify as soldier

def video_feed(name):
    global ALARM_ON
    cap = cv2.VideoCapture('videos/2.mp4')
    person_status = 0
    fall_status = 0
    soldiers = 0
    patrolling = 'False'
    
    while True:
        # Read mode.txt for patrolling mode and number of soldiers
        with open('mode.txt', 'r') as file:
            patrolling_mode = file.read()
            patrolling = patrolling_mode.split(',')[0]   
            soldiers = int(patrolling_mode.split(',')[1])  

        person_count = 0
        enemy_detected = False

        ret, frame = cap.read()
        results = model(frame)

        for info in results:
            parameters = info.boxes
            for box in parameters:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = box.conf[0]
                class_detect = int(box.cls[0])
                class_detect = classnames[class_detect]
                conf = math.ceil(confidence * 100)

                if conf > 80 and class_detect == 'person':
                    person_count += 1
                    cvzone.cornerRect(frame, [x1, y1, x2 - x1, y2 - y1], l=30, rt=6)
                    cvzone.putTextRect(frame, f'{class_detect}', [x1 + 8, y1 - 12], thickness=2, scale=2)

                    is_soldier = is_soldier_shirt_color(frame, x1, y1, x2, y2)

                    if patrolling == 'True' and person_count > soldiers:
                        if not is_soldier:  
                            enemy_detected = True

                    elif patrolling == 'False' and not is_soldier:
                        enemy_detected = True

        # Handle Firebase and alarm based on detected enemies
        if enemy_detected:
            print('Enemy Soldier Detected')
            cv2.putText(frame, 'Enemy Soldier Detected', (20, 30), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
            writeFirebase_async(1)

            if not ALARM_ON:
                ALARM_ON = True
                t = Thread(target=sound_alarm, args=('alarm.wav',))
                t.daemon = True
                t.start()
        else:
            ALARM_ON = False
            writeFirebase_async(0)

        # Stream video frame
        imgencode = cv2.imencode('.jpg', frame)[1]
        stringData = imgencode.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: text/plain\r\n\r\n' + stringData + b'\r\n')

        if cv2.waitKey(1) & 0xFF == ord('t'):
            break

    cap.release()
    cv2.destroyAllWindows()
