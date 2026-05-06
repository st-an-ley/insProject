from time import sleep
import zmq
import cv2
import pyaudio
import wave

# Server which captures the data and sends it to clients who request it
class Server:
    def __init__(self):


        print("Created Server")

    def run(self):
        #Settings for handling with pyAudio
        self.chunk = 512  # 512 samples sent per package, smaller latency but higher cpu usage
        self.sample_format = pyaudio.paInt16  # 16 bits per sample
        self.channels = 1 #1=mono, 2=stereo (left and right ear)
        self.fs = 16000  # Record at 16000 samples per second
        self.input_device_index=None
        self.output_device_index=None

        self.seconds = 3
        self.filename = "output.wav"

        #Source for camera Input
        self.camera = cv2.VideoCapture(0)

        #Source for audio Input
        self.audio = pyaudio.PyAudio()

        self.stream = self.audio.open(
                        format=self.sample_format,
                        channels=self.channels,
                        rate=self.fs,
                        frames_per_buffer=self.chunk,
                        input_device_index=self.input_device_index,
                        output_device_index=self.output_device_index,
                        input=True,
                        start=True
                        )

        #Topics for sending data 
        self.topic_video = "videoInput"
        self.topic_audio = "audioInput"

        #Create zmq Context to handle all the data transfers
        self.context = zmq.Context()


        #PUBLISHING VIDEO OVER PORT 5001 AND AUDIO OVER PORT 5002
        #EVERY CLIENT RECEIVES THE DATA OVER THOSE TOPICS
        #PUBLISHER socket for sending video feed
        self.socket_pub_video = self.context.socket(zmq.PUB)
        self.socket_pub_video.bind("tcp://*:5001")

        #PUBLISHER socket for sending audio feed
        self.socket_pub_audio = self.context.socket(zmq.PUB)
        self.socket_pub_audio.bind("tcp://*:5002")


        i = 0
        while True:
            #Read status and video input from camera
            active, videoInput = self.camera.read()

            #Read audio data from microphone
            audioInput = self.stream.read(self.chunk)


            #Display camera input with opencv
            #cv2.imshow("CameraInput", frameData)
            #Check for keyboard input 'q' = 113 in ASCII
            if cv2.waitKey(1) == 113:
                break


            #Publishing the data over a specified topic to all the clients
            #Name of Topic is the first bytes of the message
            #zmq.SNDMORE signals that more data will come (and not only the name of the topic)
            #self.socket_pub_video.send_string(self.topic_video, zmq.SNDMORE)
            self.socket_pub_video.send_pyobj(videoInput)
            #print(f"Sent frame {i}")

            #self.socket_pub_audio.send_string(self.topic_audio, zmq.SNDMORE)
            self.socket_pub_audio.send_pyobj(audioInput)
            #print(f"Sent audio data {i}")
            #print(audioInput)

            i=i+1

        self.camera.release()
        cv2.destroyAllWindows()

