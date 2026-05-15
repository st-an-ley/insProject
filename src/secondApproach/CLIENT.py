import zmq
import streamlit as st
from abc import ABC, abstractmethod
import time
import cv2
import numpy as np 

#Abstract Class Client enherited from Abstract Base Class 
class Client(ABC):
    ID = 0 #Number of created Clients
    def __init__(self, useCase, messagingType="SUB", protocol="tcp"):

        #Set the attributes to determine the type of client
        #Attributes are not allowed to include zeromq
        self.useCase = useCase
        self.messagingType = messagingType
        self.protocol = protocol

        #EVERY CLIENT RECEIVES THE VIDEO AND AUDIO INPUT OVER THOSE PORTS
        self.videoSUBport = 5001  #Port that the server sends the video data from 
        self.audioSUBport = 5002  #Port that the server sends the audio data from

        #Store current class ID as object ID
        self.ID = Client.ID

        #Port that the client sends its outpot from 
        self.PUBport = 10000 + self.ID*1000 + 1 #10001, 11001, 12001, etc.
        print(f"Created Client for {self.useCase} with ID {self.ID}")
        Client.ID = Client.ID+1
    
    @abstractmethod
    def run(self):
        pass



 ############################################################################################################

#Define each client with its specific tasks

#General client for analyzing the video input in any kind of way
#Subclass of Client
class videoProcessing_client(Client):
    def __init__(self, useCase, messagingType="SUB", protocol="tcp"):
        Client.__init__(self, useCase, messagingType="SUB", protocol="tcp")

        self.videoSendRate = 30 #Amount of frames sent per second 


    #run method for this client only uses data from port 5001, so only video, no audio
    #Every client processing video will need to receive data from port 5001
    def run(self):
        #Everything related to zmq must be initialized outside the __init__ method because
        #zmq-Objects cant be passed to pickle which is used by multiprocess 
        self.context = zmq.Context()
        
        #Create SUBSCRIBER socket to receive data from the Server
        self.socket_video_sub = self.context.socket(zmq.SUB)   
        #TODO Look if topic name must be specified since different ports are used
        self.socket_video_sub.setsockopt(zmq.SUBSCRIBE, b"") # encode() turns data into it's binary form
        #f"{self.useCase}.encode('utf-8')"
        self.socket_video_sub.connect(f"{self.protocol}://localhost:{self.videoSUBport}")

        #Create PUBLISHER socket to send data to Streamlit
        self.socket_video_pub = self.context.socket(zmq.PUB)  
        self.socket_video_pub.bind(f"{self.protocol}://*:{self.PUBport}")

        lastTimeVideo = time.time()
        while True:
            # Data should be received and processed as quick as possible; Only the rate of sending should be restricted
            #dataInput = self.socket_video_sub.recv_pyobj()

            #Receive data as raw bytes
            videoDataInputBytes = self.socket_video_sub.recv()

            #Turn bytes into numpy array as image with color to be able to work with the data
            videoDataInputNumpyArray = cv2.imdecode(np.frombuffer(videoDataInputBytes, np.uint8), cv2.IMREAD_COLOR)

            #Use numpy array and process the data
            videoDataOutputNumpyArray = self.processVideo(videoDataInputNumpyArray)

            #Convert numpy array back to raw bytes 

            success, videoDataOutputNumpyJpgBytes = cv2.imencode('.jpg', videoDataOutputNumpyArray, [cv2.IMWRITE_JPEG_QUALITY, 50])
            
            #Converts bytes numpyArray to the raw bytes 
            imageRawBytes = videoDataOutputNumpyJpgBytes.tobytes()

            if time.time() - lastTimeVideo > 1/self.videoSendRate:
                #TODO change dataInput to dataOutput; Right now because of test reasons
                #self.socket_pub.send_pyobj(dataInput)

                #Convert numpy array back to bytes to send the data
                self.socket_video_pub.send(imageRawBytes)

                lastTimeVideo = time.time()
        
    #Method to process a video input in any kind of way
    @abstractmethod
    def processVideo(self, videoInput):
        pass

############################################################################################################

#Abstract class for analyzing the audio input in any kind of way
class audioProcessing_client(Client):
    def __init__(self, useCase, messagingType="SUB", protocol="tcp"):
        Client.__init__(self, useCase, messagingType="SUB", protocol="tcp")

        self.audioSendRate = 10 #Amount of data samples sent per second

    #run method for this client only uses data from port 5002, so only audio, no video
    #Every client processing audio will need to receive data from port 5002
    def run(self):
        #Everything related to zmq must be initialized outside the __init__ method because
        #zmq-Objects cant be passed to pickle which is used by multiprocess 
        #TODO add socket for audio input, currently only socket for video input 
        self.context = zmq.Context()
        
        #Create SUBSCRIBER socket to receive data from the Server
        self.socket_audio_sub = self.context.socket(zmq.SUB)   
        #TODO Look if topic name must be specified since different ports are used
        self.socket_audio_sub.setsockopt(zmq.SUBSCRIBE, b"") # encode() turns data into it's binary form
        self.socket_audio_sub.connect(f"{self.protocol}://localhost:{self.audioSUBport}")

        #Create PUBLISHER socket to send data to Streamlit
        self.socket_pub = self.context.socket(zmq.PUB)  
        self.socket_pub.bind(f"{self.protocol}://*:{self.PUBport}")

        lastTimeAudio = time.time()
        while True:
            # Data should be received and processed as quick as possible; Only the rate of sending should be restricted
            dataInput = self.socket_audio_sub.recv_pyobj()
            dataOutput = self.processAudio(dataInput)
            if time.time() - lastTimeAudio > 1/self.audioSendRate:
                #topicInput = self.socket_audio_sub.recv_string()

                #TODO change dataInput to dataOuput; right now for test reasons
                self.socket_pub.send_pyobj(dataInput)
                lastTimeAudio = time.time()
        
    @abstractmethod
    def processAudio(self, audioInput):
        pass

############################################################################################################

#Specifif use case for processing the video input, in this case for checking video input for cheating
class checkVideoFeedCheating_client(videoProcessing_client):
    def __init__(self, useCase, messagingType="SUB", protocol="tcp"):
        videoProcessing_client.__init__(self, useCase, messagingType="SUB", protocol="tcp")

    def run(self):
        videoProcessing_client.run(self)


    #Overrites the methods from the parent class; Will be automatically called when executed on child class
    def processVideo(self, videoInput):
        print("Running processVideo() from checkVideoFeedCheating_client")
        #TODO change dataOutput to correct data
        dataOutput = videoInput
        return dataOutput
        #TODO Implement methods to check for cheating in video

############################################################################################################

#Specifif use case for processing the video input, in this case for checking video input for cheating
class checkAudioFeedCheating_client(audioProcessing_client):
    def __init__(self, useCase, messagingType="SUB", protocol="tcp"):
        audioProcessing_client.__init__(self, useCase, messagingType="SUB", protocol="tcp")
    
    def run(self):
        audioProcessing_client.run(self)
    
    #Overrites the methods from the parent class; Will be automatically called when executed on child class
    def processAudio(self, audioInput):
        print("Running processAudio() from checkAudioFeedCheating_client")
        #TODO Implement methods to check for cheating in audio

############################################################################################################

#TODO add further client types

