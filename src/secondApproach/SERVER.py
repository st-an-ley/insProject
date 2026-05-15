from time import sleep
import zmq
import cv2
import pyaudio
import wave
import time

# Server which captures the data and sends it to clients who request it
class Server:
    def __init__(self):


        print("Created Server")

    def run(self):
        #Settings for handling with pyAudio
        self.chunk = 2048  # Record in chunks of 1024 samples
        self.sample_format = pyaudio.paInt32  # 16 bits per sample
        self.channels = 2
        self.fs = 44100  # Record at 44100 samples per second

        #Settings for controlling the amount of input
        self.videoInputRate = 30 # Number of video inputs per second
        self.audioInputRate = 10 # Number of audio inputs per second


        #Settings for controlling the amount of output
        self.videoOutputRate = 10 # Number of video outputs per second
        self.audioOutputRate = 10 # Number of audio outputs per second

        #Source for camera Input
        self.camera = cv2.VideoCapture(0)

        #Source for audio Input
        self.audio = pyaudio.PyAudio()

        self.stream = self.audio.open(format=self.sample_format,
                        channels=self.channels,
                        rate=self.fs,
                        frames_per_buffer=self.chunk,
                        input=True)

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

        #Counter to check number of send data
        i = 0

        #Variable to store when the last execution happened 
        lastTimeVideo = time.time()
        lastTimeAudio = time.time()

        while True:

            #Passed time since last execution 
            passedTimeVideo = time.time() - lastTimeVideo
            passedTimeAudio = time.time() - lastTimeAudio

            if passedTimeVideo > 1/self.videoInputRate:
                #Read status and video input from camera
                active, videoInput = self.camera.read()

                #imencode converts image numpyArray to bytes numpyArray, containing all the bytes as a list 
                success, imageNumpyJpgBytes = cv2.imencode('.jpg', videoInput, [cv2.IMWRITE_JPEG_QUALITY, 50])
                
                #Converts bytes numpyArray to the raw bytes 
                self.socket_pub_video.send(imageNumpyJpgBytes.tobytes())  

                #self.socket_pub_video.send_pyobj(videoInput)
                lastTimeVideo=time.time()


            if passedTimeAudio > 1/self.audioInputRate:
                #Read audio data from microphone
                audioInput = self.stream.read(self.chunk)
                self.socket_pub_audio.send_pyobj(audioInput)
                lastTimeAudio=time.time()



            #Display camera input with opencv
            #cv2.imshow("CameraInput", frameData)
            #Check for keyboard input 'q' = 113 in ASCII
            if cv2.waitKey(1) == 113:
                break


            #Publishing the data over a specified topic to all the clients
            #Name of Topic is the first bytes of the message
            #zmq.SNDMORE signals that more data will come (and not only the name of the topic)
            #self.socket_pub_video.send_string(self.topic_video, zmq.SNDMORE)
            #print(f"Sent frame {i}")

            #self.socket_pub_audio.send_string(self.topic_audio, zmq.SNDMORE)
            #print(f"Sent audio data {i}")
            #print(audioInput)

            i=i+1

        self.camera.release()
        cv2.destroyAllWindows()

