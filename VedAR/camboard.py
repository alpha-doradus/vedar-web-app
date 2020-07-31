import numpy as np
import cv2
from collections import deque


# VideoCameraBoard object that controls all the recognition and board changes
class VideoCameraBoard(object):
    def __init__(self):
        # Capturing video
        self.video = cv2.VideoCapture(0)

        # Define the upper and lower boundaries for a color to be considered "Blue".
        self.blueLower = np.array([100, 60, 60])
        self.blueUpper = np.array([140, 255, 255])

        # Define a 5x5 kernel for erosion and dilation.
        self.kernel = np.ones((5, 5), np.uint8)

        # Setup deques to store separate colors in separate arrays.
        self.bpoints = [deque(maxlen=512)]
        self.gpoints = [deque(maxlen=512)]
        self.rpoints = [deque(maxlen=512)]
        self.bindex = 0
        self.gindex = 0
        self.rindex = 0
        self.colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
        self.colorIndex = 0

        # Setup the paint interface.
        self.paintWindow = np.zeros((471, 636, 3)) + 255
        self.paintWindow = cv2.rectangle(self.paintWindow, (40, 1), (140, 65), (0, 0, 0), 2)
        self.paintWindow = cv2.rectangle(self.paintWindow, (160, 1), (255, 65), self.colors[0], -1)
        self.paintWindow = cv2.rectangle(self.paintWindow, (275, 1), (370, 65), self.colors[1], -1)
        self.paintWindow = cv2.rectangle(self.paintWindow, (390, 1), (485, 65), self.colors[2], -1)
        cv2.putText(self.paintWindow, "Limpiar", (49, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(self.paintWindow, "Azul", (185, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(self.paintWindow, "Verde", (298, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(self.paintWindow, "Rojo", (420, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

    def __del__(self):
        # Releasing camera
        self.video.release()

    def get_frame(self):
        # Extracting frames
        ret, frame = self.video.read()
        frame = cv2.flip(frame, 1)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Add the coloring options to the frame.
        frame = cv2.rectangle(frame, (40, 1), (140, 65), (0, 0, 0), 2)
        frame = cv2.rectangle(frame, (160, 1), (255, 65), self.colors[0], -1)
        frame = cv2.rectangle(frame, (275, 1), (370, 65), self.colors[1], -1)
        frame = cv2.rectangle(frame, (390, 1), (485, 65), self.colors[2], -1)
        cv2.putText(frame, "Limpiar", (49, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "Azul", (185, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "Verde", (298, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "Rojo", (420, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

        # Determine which pixels fall within the blue boundaries and then blur the binary image.
        blueMask = cv2.inRange(hsv, self.blueLower, self.blueUpper)
        blueMask = cv2.erode(blueMask, self.kernel, iterations=2)
        blueMask = cv2.morphologyEx(blueMask, cv2.MORPH_OPEN, self.kernel)
        blueMask = cv2.dilate(blueMask, self.kernel, iterations=1)
        # Find contours in the image.
        (cnts, _) = cv2.findContours(blueMask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        center = None

        # Check to see if any contours were found.
        if len(cnts) > 0:
            # Sort the contours and find the largest one -- we
            #   will assume this contour correspondes to the area of the bottle cap.
            cnt = sorted(cnts, key=cv2.contourArea, reverse=True)[0]
            # Get the radius of the enclosing circle around the found contour.
            ((x, y), radius) = cv2.minEnclosingCircle(cnt)
            # Draw the circle around the contour.
            cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
            # Get the moments to calculate the center of the contour (in this case Circle).
            M = cv2.moments(cnt)
            center = (int(M['m10'] / M['m00']), int(M['m01'] / M['m00']))
            if center[1] <= 65:
                if 40 <= center[0] <= 140:  # Clear All.
                    self.bpoints = [deque(maxlen=512)]
                    self.gpoints = [deque(maxlen=512)]
                    self.rpoints = [deque(maxlen=512)]
                    ypoints = [deque(maxlen=512)]
                    self.bindex = 0
                    self.gindex = 0
                    self.rindex = 0
                    yindex = 0
                    self.paintWindow[67:, :, :] = 255
                elif 160 <= center[0] <= 255:
                    self.colorIndex = 0  # Blue.
                elif 275 <= center[0] <= 370:
                    self.colorIndex = 1  # Green.
                elif 390 <= center[0] <= 485:
                    self.colorIndex = 2  # Red.
                elif 505 <= center[0] <= 600:
                    self.colorIndex = 3  # Yellow.
            else:
                if self.colorIndex == 0:
                    self.bpoints[self.bindex].appendleft(center)
                elif self.colorIndex == 1:
                    self.gpoints[self.gindex].appendleft(center)
                elif self.colorIndex == 2:
                    self.rpoints[self.rindex].appendleft(center)
        # Append the next deque when no contours are detected (i.e., pencil reversed).
        else:
            self.bpoints.append(deque(maxlen=512))
            self.bindex += 1
            self.gpoints.append(deque(maxlen=512))
            self.gindex += 1
            self.rpoints.append(deque(maxlen=512))
            self.rindex += 1
        # Draw lines of all the colors.
        points = [self.bpoints, self.gpoints, self.rpoints]
        for i in range(len(points)):
            for j in range(len(points[i])):
                for k in range(1, len(points[i][j])):
                    if points[i][j][k - 1] is None or points[i][j][k] is None:
                        continue
                    cv2.line(frame, points[i][j][k - 1], points[i][j][k], self.colors[i], 2)
                    cv2.line(self.paintWindow, points[i][j][k - 1], points[i][j][k], self.colors[i], 2)

        # Encode OpenCV raw frame and processed image to jpg
        ret, jpeg = cv2.imencode('.jpg', frame)
        ret, paint = cv2.imencode('.jpg', self.paintWindow)

        # Return the encoded images in byte format
        return jpeg.tobytes(), paint.tobytes()

