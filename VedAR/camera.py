import cv2
import numpy as np

# Function to display the avatar with the corresponding icon
def display_icon(icon_file):
    # Background color
    bb = np.zeros((icon_height, icon_width, 3), np.uint8)
    bb[:] = [blue, green, red]

    if icon_file is None:
        icon_img[0:icon_height, 0:icon_width] = bb
    else:
        icon = cv2.imread(icon_file)
        icon = cv2.resize(icon, (icon_width, icon_height))
        # Overlap the background with the icon
        icon = cv2.addWeighted(icon, 0.7, bb, 0.3, 0)
        # Replace icon in the avatar coordinates [y:y+h, x:x+w]
        icon_img[0:icon_height, 0:icon_width] = icon

    return icon_img


# Defining all variables

# Defining face, smile, palm and fist detectors
face_cascade = cv2.CascadeClassifier("haarcascades/haarcascade_frontalface_default.xml")
smile_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_smile.xml')
open_palm_cascade = cv2.CascadeClassifier('haarcascades/open_palm.xml')
closed_palm_cascade = cv2.CascadeClassifier('haarcascades/closed_palm.xml')

# Frame resize factor
ds_factor = 0.6

# Defining the image variables
icon_width = 85
icon_height = 75
sleep = 'images/sleep.png'
hand = 'images/hand.png'
thumbUp = 'images/thumb-up.png'
thumbDown = 'images/thumb-down.png'

# Icon image and color streams
icon_img = cv2.imread('images/animal-icon-cat.jpg')
img = cv2.imread('images/animal-icon-cat.jpg')
blue = icon_img[0, 0, 0]
green = icon_img[0, 0, 1]
red = icon_img[0, 0, 2]


# VideoCamera object that controls all the recognition and avatar changes
class VideoCamera(object):
    def __init__(self):
        # Capturing Video
        self.video = cv2.VideoCapture(0)

        # Count of frames with each gesture
        self.sleep_frames = 0
        self.slp = False
        self.fist_frames = 0
        self.no_fist_frames = 0
        self.palm_frames = 0
        self.no_palm_frames = 0
        self.smile_frames = 0
        self.no_smile_frames = 0
        self.wait_frames = 15

    def __del__(self):
        # Releasing camera
        self.video.release()

    def get_frame(self):
        # Extracting frames
        ret, frame = self.video.read()
        frame = cv2.resize(frame, None, fx=ds_factor, fy=ds_factor,
        interpolation=cv2.INTER_AREA)
        # Extracting the same frame in gray scale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Defining the avatar variable
        avatar = icon_img

        # Detects faces in the actual frame
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)
        if len(faces) > 0:
            # Restores the count of sleep frames
            self.sleep_frames = 0
            # If the avatar was in sleep mode, shows the active avatar again
            if self.slp:
                self.slp = False
                avatar = display_icon(None)

            # For each face detected
            for (x, y, w, h) in faces:
                # Draws a green rectangle around the face
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # Region of Interests (face)
                roi_gray = gray[y:y + h, x:x + w]

                # Smile Detections in the face region
                # Detects smiles and change the state of the avatar with a thumb up
                smiles = smile_cascade.detectMultiScale(roi_gray, 3.5, 20)
                if len(smiles) > 0:
                    for (sx, sy, sw, sh) in smiles:
                        # Draws a red rectangle around the smile
                        cv2.rectangle(frame, (x + sx, y + sy), (x + sx + sw, y + sy + sh), (0, 0, 255), 3)
                        # Adds one to the smile frames count
                        self.smile_frames += 1
                        # If the total smile frames reaches the wait frames, display the avatar with a thumb up
                        if self.smile_frames == self.wait_frames:
                            self.smile_frames = 0
                            avatar = display_icon(thumbUp)
                        # Allows just one smile
                        break
                else:
                    # Adds one to the no smile frames count
                    self.no_smile_frames += 1
                    # If the total no smile frames count reaches the wait frames, restores the smile counts
                    if self.no_smile_frames == self.wait_frames:
                        self.smile_frames = 0
                        self.no_smile_frames = 0
                # Allows just one face
                break
        else:
            # Adds one to the sleep frames count
            self.sleep_frames += 1
            # If the sleep frames reaches 150, enters the sleep mode and display the avatar with the sleep icon
            if self.sleep_frames == 150:
                self.slp = True
                avatar = display_icon(sleep)

        # Detects palms in the current frame and change the state of the avatar with a raised hand
        palms = open_palm_cascade.detectMultiScale(gray, 1.1, 12)
        if len(palms) > 0:
            # For each palm detected
            for (x, y, w, h) in palms:
                # Draws a black rectangle around the palm
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 0), 3)
                # Adds one to the palm frames count
                self.palm_frames += 1
                # If the total palm frames reaches the wait frames, display the avatar with a raised hand
                if self.palm_frames == self.wait_frames:
                    self.palm_frames = 0
                    avatar = display_icon(hand)
                # Allows just one palm
                break
        else:
            # Adds one to the no palm frames count
            self.no_palm_frames += 1
            # If the total no palm frames count reaches the wait frames, restores the palm counts
            if self.no_palm_frames == self.wait_frames:
                self.palm_frames = 0
                self.no_palm_frames = 0

        # Detects fists and change the state of the avatar with a thumb down
        fists = closed_palm_cascade.detectMultiScale(gray, 1.1, 10)
        if len(fists) > 0:
            # For each fist detected
            for (x, y, w, h) in fists:
                # Draws a white rectangle around the fist
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 3)
                # Adds one to the fist frames count
                self.fist_frames += 1
                # If the total fist frames reaches the wait frames, display the avatar with a thumb down
                if self.fist_frames == self.wait_frames:
                    self.fist_frames = 0
                    avatar = display_icon(thumbDown)
                # Allows just one fist
                break
        else:
            # Adds one to the no fist frames count
            self.no_fist_frames += 1
            # If the total no fist frames count reaches the wait frames, restores the fist counts
            if self.no_fist_frames == self.wait_frames:
                self.fist_frames = 0
                self.no_fist_frames = 0

        # Encode OpenCV raw frame and avatar image to jpg
        ret, jpeg = cv2.imencode('.jpg', frame)
        if avatar is not None:
            ret2, ava = cv2.imencode('.jpg', avatar)
        else:
            ret2, ava = cv2.imencode('.jpg', img)

        # Return the encoded images in byte format
        return jpeg.tobytes(), ava.tobytes()
