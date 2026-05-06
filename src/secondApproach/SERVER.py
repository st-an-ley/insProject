from time import sleep
import zmq
import cv2
import pyaudio
import wave

# Server which captures the data and sends it to clients who request it
class Server:
    def __init__(self):

        self.chunk = 2048  # Record in chunks of 1024 samples
        self.sample_format = pyaudio.paInt32  # 16 bits per sample
        self.channels = 2
        self.fs = 44100  # Record at 44100 samples per second
        self.seconds = 3
        self.filename = "output.wav"


        self.context = zmq.Context()

        #PUBLISHER socket for sending video feed
        self.socket_pub_video = self.context.socket(zmq.PUB)
        self.socket_pub_video.bind("tcp://*:5001")
        self.camera = cv2.VideoCapture(0)


        #PUBLISHER socket for sending audio feed
        self.socket_pub_audio = self.context.socket(zmq.PUB)
        self.socket_pub_audio.bind("tcp://*:5002")
        self.audio = pyaudio.PyAudio()

        stream = self.audio.open(format=self.sample_format,
                        channels=self.channels,
                        rate=self.fs,
                        frames_per_buffer=self.chunk,
                        input=True)


        topic_video = "videoInput"
        topic_audio = "audioInput"

    def run(self):
        i = 0
        while True:
            #Read status and data from camera
            active, frameData = self.camera.read()
            audioInput = self.stream.read(self.chunk)


            #Display camera input with opencv
            cv2.imshow("CameraInput", frameData)
            #Check for keyboard input 'q' = 113 in ASCII
            if cv2.waitKey(1) == 113:
                break


            #Publishing the data over a specified topic to all the clients
            #Name of Topic is the first bytes of the message
            #zmq.SNDMORE signals that more data will come (and not only the name of the topic)
            self.socket_pub_video.send_string(self.topic_video, zmq.SNDMORE)
            self.socket_pub_video.send_pyobj(frameData)
            print(f"Sent frame {i}")

            self.socket_pub_audio.send_string(self.topic_audio, zmq.SNDMORE)
            self.socket_pub_audio.send_pyobj(audioInput)
            print(f"Sent audio data {i}")
            print(audioInput)

            i=i+1

        self.camera.release()
        cv2.destroyAllWindows()

