import zmq
import streamlit as st

#defining what every client has in common
class Client:
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

        self.PUBport = 6000 + Client.ID*1000 + 2 #5002, 6002, 7002, etc. 
        self.ID = Client.ID
        print(f"Created Client for {self.useCase} with ID {self.ID}")
        Client.ID = Client.ID+1

 
    def run(self):
        #Everything related to zmq must be initialized outside the __init__ method because
        #zmq-Objects cant be passed to pickle which is used by multiprocess 
        #TODO add socket for audio input, currently only socket for video input 
        self.context = zmq.Context()
        
        #Create SUBSCRIBER socket to receive data from the Server
        self.socket_sub = self.context.socket(zmq.SUB)   
        self.socket_sub.setsockopt(zmq.SUBSCRIBE, b"Test") # encode() turns data into it's binary form
        #f"{self.useCase}.encode('utf-8')"
        self.socket_sub.connect(f"{self.protocol}://localhost:{self.SUBport}")

        #Create PUBLISHER socket to send data to Streamlit
        self.socket_pub = self.context.socket(zmq.PUB)  
        self.socket_pub.bind(f"{self.protocol}://*:{self.PUBport}")

        while True:
            topicInput = self.socket_sub.recv_string()
            dataInput = self.socket_sub.recv_pyobj()
            #TODO change dataInput to the processed data
            self.socket_pub.send_pyobj(dataInput)


#Define each client with its specific tasks

class checkVideoFeedCheating_client(Client):
    def __init__(self, useCase, messagingType="SUB", protocol="tcp"):
        Client.__init__(self, useCase, messagingType="SUB", protocol="tcp")

    def checkVideoFeedCheating(self, videoInput):
        #TODO
        print("Checking video for cheating. Need further implementation")



class checkAudioFeedCheating_client(Client):
    def __init__(self, useCase, messagingType="SUB", protocol="tcp"):
        Client.__init__(self, useCase, messagingType="SUB", protocol="tcp")

    def checkVideoFeedCheating(self, audioInput):
        #TODO
        print("Checking audio for cheating. Need further implementation")

#TODO add further client types