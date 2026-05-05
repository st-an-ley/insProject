import zmq
import cv2

context = zmq.Context()
socket_pub = context.socket(zmq.PUB)
socket_pub.bind("tcp://*:5555")
cameraInput = cv2.VideoCapture(0)

while True:
    active, frameData = cameraInput.read()
    socket_pub.send_string()