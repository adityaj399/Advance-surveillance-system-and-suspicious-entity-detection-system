import cv2
import numpy as np
import time

# Initialize Webcam
cap = cv2.VideoCapture(0)

# Function to update trackbar values
def nothing(x):
    pass

# Create a window
cv2.namedWindow("HSV Trackbars")

# Create trackbars for lower and upper HSV values
cv2.createTrackbar("Lower H", "HSV Trackbars", 83, 179, nothing)
cv2.createTrackbar("Lower S", "HSV Trackbars", 7, 255, nothing)
cv2.createTrackbar("Lower V", "HSV Trackbars", 0, 255, nothing)
cv2.createTrackbar("Upper H", "HSV Trackbars", 137, 179, nothing)
cv2.createTrackbar("Upper S", "HSV Trackbars", 178, 255, nothing)
cv2.createTrackbar("Upper V", "HSV Trackbars", 255, 255, nothing)

while True:
    ret, frame = cap.read()
    time.sleep(1)
    if not ret:
        break

    # Convert frame to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Get current trackbar positions
    lower_h = cv2.getTrackbarPos("Lower H", "HSV Trackbars")
    lower_s = cv2.getTrackbarPos("Lower S", "HSV Trackbars")
    lower_v = cv2.getTrackbarPos("Lower V", "HSV Trackbars")
    upper_h = cv2.getTrackbarPos("Upper H", "HSV Trackbars")
    upper_s = cv2.getTrackbarPos("Upper S", "HSV Trackbars")
    upper_v = cv2.getTrackbarPos("Upper V", "HSV Trackbars")

    # Define HSV range based on trackbar positions
    lower_blue = np.array([lower_h, lower_s, lower_v])
    upper_blue = np.array([upper_h, upper_s, upper_v])

    # Create a mask
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Apply mask on original frame
    result = cv2.bitwise_and(frame, frame, mask=mask)

    # Show output
    cv2.imshow("Original", frame)
    cv2.imshow("Mask", mask)  # Shows detected blue regions
    cv2.imshow("Result", result)  # Shows only detected blue-colored areas

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
