import zmq
import streamlit as st
from abc import ABC, abstractmethod

#Abstract Class Client
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
        self.audioSUBport = 5002

        self.PUBport = 6000 + Client.ID*1000 + 1 #5002, 6002, 7002, etc. 
        self.ID = Client.ID
        print(f"Created Client for {self.useCase} with ID {self.ID}")
        Client.ID = Client.ID+1

 

#Define each client with its specific tasks

#General client for analyzing the video input in any kind of way
#Subclass of Client
class videoProcessing_client(Client):
    def __init__(self, useCase, messagingType="SUB", protocol="tcp"):
        Client.__init__(self, useCase, messagingType="SUB", protocol="tcp")
    
    #run method for this client only uses data from port 5001, so only video, no audio

    def run(self):
        #Everything related to zmq must be initialized outside the __init__ method because
        #zmq-Objects cant be passed to pickle which is used by multiprocess 
        #TODO add socket for audio input, currently only socket for video input 
        self.context = zmq.Context()
        
        #Create SUBSCRIBER socket to receive data from the Server
        self.socket_video_sub = self.context.socket(zmq.SUB)   
        #TODO Look if topic name must be specified since different ports are used
        self.socket_video_sub.setsockopt(zmq.SUBSCRIBE, b"Test") # encode() turns data into it's binary form
        #f"{self.useCase}.encode('utf-8')"
        self.socket_video_sub.connect(f"{self.protocol}://localhost:{self.videoSUBport}")

        #Create PUBLISHER socket to send data to Streamlit
        self.socket_pub = self.context.socket(zmq.PUB)  
        self.socket_pub.bind(f"{self.protocol}://*:{self.PUBport}")

        while True:
            topicInput = self.socket_sub.recv_string()
            dataInput = self.socket_sub.recv_pyobj()
            #TODO change dataInput to the processed data
            dataOutput = self.processVideo(dataInput)
            self.socket_pub.send_pyobj(dataInput)
        
    #Method to process a video input in any kind of way
    @abstractmethod
    def processVideo(self, videoInput):
        pass



#Abstract class for analyzing the audio input in any kind of way
class audioProcessing_client(Client):
    def __init__(self, useCase, messagingType="SUB", protocol="tcp"):
        Client.__init__(self, useCase, messagingType="SUB", protocol="tcp")

    #run method for this client only uses data from port 5002, so only audio, no video
    
    def run(self):
                #Everything related to zmq must be initialized outside the __init__ method because
        #zmq-Objects cant be passed to pickle which is used by multiprocess 
        #TODO add socket for audio input, currently only socket for video input 
        self.context = zmq.Context()
        
        #Create SUBSCRIBER socket to receive data from the Server
        self.socket_audio_sub = self.context.socket(zmq.SUB)   
        #TODO Look if topic name must be specified since different ports are used
        self.socket_audio_sub.setsockopt(zmq.SUBSCRIBE, b"Test") # encode() turns data into it's binary form
        #f"{self.useCase}.encode('utf-8')"
        self.socket_audio_sub.connect(f"{self.protocol}://localhost:{self.audioSUBport}")

        #Create PUBLISHER socket to send data to Streamlit
        self.socket_pub = self.context.socket(zmq.PUB)  
        self.socket_pub.bind(f"{self.protocol}://*:{self.PUBport}")

        while True:
            topicInput = self.socket_audio_sub.recv_string()
            dataInput = self.socket_audio_sub.recv_pyobj()
            #TODO change dataInput to the processed data
            dataOutput = self.processVideo(dataInput)
            self.socket_pub.send_pyobj(dataInput)
        
    @abstractmethod
    def processAudio(self, audioInput):
        pass





#Specifif use case for processing the video input, in this case for checking video input for cheating
class checkVideoFeedCheating_client(videoProcessing_client):
    def __init__(self, useCase, messagingType="SUB", protocol="tcp"):
        videoProcessing_client.__init__(self, useCase, messagingType="SUB", protocol="tcp")

    def run(self):
        videoProcessing_client.run(self)


    #Overrites the methods from the parent class; Will be automatically called when executed on child class
    def processVideo():
        print("Running processVideo() from checkVideoFeedCheating_client")
        #TODO Implement methods to check for cheating 


#Specifif use case for processing the video input, in this case for checking video input for cheating
class checkAudioFeedCheating_client(audioProcessing_client):
    def __init__(self, useCase, messagingType="SUB", protocol="tcp"):
        audioProcessing_client.__init__(self, useCase, messagingType="SUB", protocol="tcp")
    
    def run(self):
        audioProcessing_client.run(self)
    
    #Overrites the methods from the parent class; Will be automatically called when executed on child class
    def processAudio():
        print("Running processAudio() from checkAudioFeedCheating_client")
        #TODO Implement methods to check for cheating 

#TODO add further client types