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

# Initialize Firebase writing function
def writeFirebase_async(data):
    Thread(target=writeFirebase, args=(data,)).start()

ALARM_ON = False

def sound_alarm(path):
    playsound.playsound(path)

# Load YOLO model
model = YOLO('yolov8n.pt')

# Load class names
classnames = []
with open('classes.txt', 'r') as f:
    classnames = f.read().splitlines()

# Trackbar function (does nothing, just a placeholder)
def nothing(x):
    pass

# Create a window for trackbars
cv2.namedWindow("HSV Trackbars")

# Initialize trackbars for Lower and Upper HSV range
# cv2.createTrackbar("Lower H", "HSV Trackbars", 83, 179, nothing)
# cv2.createTrackbar("Lower S", "HSV Trackbars", 7, 255, nothing)
# cv2.createTrackbar("Lower V", "HSV Trackbars", 0, 255, nothing)
# cv2.createTrackbar("Upper H", "HSV Trackbars", 137, 179, nothing)
# cv2.createTrackbar("Upper S", "HSV Trackbars", 178, 255, nothing)
# cv2.createTrackbar("Upper V", "HSV Trackbars", 255, 255, nothing)

cv2.createTrackbar("Lower H", "HSV Trackbars", 40, 179, nothing)
cv2.createTrackbar("Lower S", "HSV Trackbars", 17, 255, nothing)
cv2.createTrackbar("Lower V", "HSV Trackbars", 100, 255, nothing)
cv2.createTrackbar("Upper H", "HSV Trackbars", 179, 179, nothing)
cv2.createTrackbar("Upper S", "HSV Trackbars", 255, 255, nothing)
cv2.createTrackbar("Upper V", "HSV Trackbars", 255, 255, nothing)


def is_soldier_shirt_color(frame, x1, y1, x2, y2):
    """
    Check if the detected person's shirt is light blue based on HSV values.
    Focuses only on the torso (neck to waist).
    """
    torso_start = int(y1 + (y2 - y1) / 6.1)  # Exclude head 6
    torso_end = int(y1 + (y2 - y1) / 2)  # Up to waist region1.8

    shirt_region = frame[torso_start:torso_end, x1:x2]  # Extract torso

    if shirt_region.size == 0:
        return False  # Avoid errors if region is empty

    # Convert to HSV
    hsv = cv2.cvtColor(shirt_region, cv2.COLOR_BGR2HSV)

    # Get trackbar values for dynamic blue range
    lower_blue = np.array([
        cv2.getTrackbarPos("Lower H", "HSV Trackbars"),
        cv2.getTrackbarPos("Lower S", "HSV Trackbars"),
        cv2.getTrackbarPos("Lower V", "HSV Trackbars")
    ])
    upper_blue = np.array([
        cv2.getTrackbarPos("Upper H", "HSV Trackbars"),
        cv2.getTrackbarPos("Upper S", "HSV Trackbars"),
        cv2.getTrackbarPos("Upper V", "HSV Trackbars")
    ])

    # Create a mask
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Display the mask
    cv2.imshow("Shirt Color Mask", mask)

    # Calculate the ratio of detected blue pixels
    blue_ratio = cv2.countNonZero(mask) / mask.size

    return blue_ratio > 0.5  # If at least 30% of pixels are blue, classify as soldier


def video_feed(name):
    global ALARM_ON
    person_status = 0
    fall_status = 0
    soldiers = 0
    patrolling = 'False'
    cap = cv2.VideoCapture(0)  # Use webcam; replace with 'videos/2.mp4' if needed

    while True:
        # Read mode.txt for patrolling mode and number of soldiers
        with open('mode.txt', 'r') as file:
            patrolling_mode = file.read()
            patrolling = patrolling_mode.split(',')[0]   
            soldiers = int(patrolling_mode.split(',')[1]) 

        soldier_count = 0
        enemy_count = 0
        person = 0
        enemy_detected = False

        ret, frame = cap.read()
        if not ret:
            break

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
                    cvzone.cornerRect(frame, [x1, y1, x2 - x1, y2 - y1], l=30, rt=6)
                    cvzone.putTextRect(frame, f'{class_detect}', [x1 + 8, y1 - 12], thickness=2, scale=2)

                    is_soldier = is_soldier_shirt_color(frame, x1, y1, x2, y2)

                    person = person+1
                    if is_soldier:
                        soldier_count += 1
                    else:
                        enemy_count += 1

        if patrolling == 'False' and person > 0:
            enemy_detected = True
        elif patrolling == 'True' and person > soldiers:
            enemy_detected = True
        elif enemy_count > 0:
            enemy_detected = True
        else:
            enemy_detected = False

        # Display soldier & enemy count
        cv2.putText(frame, f"Soldiers: {soldier_count} | Enemies: {enemy_count}", 
                    (20, 30), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)

        # Handle Firebase and alarm based on detected enemies
        if enemy_detected:
            print(f'Enemy Soldiers Detected: {enemy_count}')
            writeFirebase_async(1)

            if not ALARM_ON:
                ALARM_ON = True
                t = Thread(target=sound_alarm, args=('alarm.wav',))
                t.daemon = True
                t.start()
        else:
            ALARM_ON = False
            writeFirebase_async(0)

        # Display the output frame
        #cv2.imshow("Detection Feed", frame)

        imgencode = cv2.imencode('.jpg', frame)[1]
        stringData = imgencode.tobytes()  # .tostring() is deprecated
        yield (b'--frame\r\n'
               b'Content-Type: text/plain\r\n\r\n' + stringData + b'\r\n')

        if cv2.waitKey(1) & 0xFF == ord('t'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Run the detection
#video_feed("SecurityCam")
