import cv2
import paho.mqtt.client as mqtt
import time


def on_log(client, userdata, level, buf):
    print('log: ' + buf)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print('connected OK')
    else:
        print('Bad connection returned code=', rc)


def on_disconnect(client, userdata, flags, rc=0):
    print('Disconnected result code '+str(rc))


def on_message(client, userdata, msg):
    topic = msg.topic
    m_decode = str(msg.payload.decode('utf-8', 'ignore msg'))
    print('msg = ', m_decode)


def on_publish(client, userdata, mid):
    print('published : ', str(mid))



def update(frame, frameCenter, detector):
		# convert the frame to grayscale
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

		# detect all faces in the input frame
		rects = detector.detectMultiScale(gray, scaleFactor=1.05,
			minNeighbors=9, minSize=(30, 30),
			flags=cv2.CASCADE_SCALE_IMAGE)

		# check to see if a face was found
		if len(rects) > 0:
			# extract the bounding box coordinates of the face and
			# use the coordinates to determine the center of the
			# face
			(x, y, w, h) = rects[0]
			faceX = int(x + (w / 2.0))
			faceY = int(y + (h / 2.0))

			# return the center (x, y)-coordinates of the face
			return (faceX, faceY)

		# otherwise no faces were found, so return the center of the
		# frame
        # returns sensor to original angle
		return (frameCenter, None)


if __name__ == "__main__":
	# construct the argument parser and parse the arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-c", "--cascade", type=str, required=True,
		help="path to input Haar cascade for face detection")
    ap.add_argument("-v", "--video", type=str, default="somevideo.mp4"
        help="path to input video for face detection")
	args = vars(ap.parse_args())

    # Loading Detector
    detector = cv2.CascadeClassifier(args["cascade"])

    # Setup mqtt
    print('Connecting to broker ', broker)
    pubtop = '/pan-tilt/coordinates'
    broker = '127.0.0.1'
    port = 1883
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_log = on_log
    client.on_message = on_message
    client.on_publish = on_publish
    client.connect(broker, port)
    time.sleep(1)


    video = cv2.videoCapture(args["video"])
    ret, frame = video.read()
    client.loop_start() 

    while ret:
		# grab the frame from the threaded video stream and flip it
		# vertically (since our camera was upside down)
		frame = cv2.flip(frame, 0)

		# calculate the center of the frame as this is where we will
		# try to keep the object
		(H, W) = frame.shape[:2]
		centerX = W // 2
		centerY = H // 2

		# find the object's location
		objectLoc = update(frame, (centerX, centerY), detector)
		(objX, objY) = objectLoc

        # Publish coordinates  to mqtt
        client.publish(pubtop, '{},{},{},{}'.format(objX, objY, centerX, centerY))


		ret, frame = video.read()

    client.loop_stop()
    client.disconnect
