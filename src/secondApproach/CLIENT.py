import zmq
import streamlit as st

#defining what every client has in common
class Client:
    ID = 0 #Number of created Clients
    def __init__(self, useCase, SUBport, PUBport, messagingType="SUB", protocol="tcp"):
        #Set the attributes to determine the type of client
        self.useCase = useCase
        self.messagingType = messagingType
        self.protocol = protocol
        self.SUBport = SUBport
        self.PUBport = PUBport
        self.ID = Client.ID
        print(f"Created Client for {self.useCase} with ID {self.ID}")
        Client.ID = Client.ID+1


        self.context = zmq.Context()
        
        #Create SUBSCRIBER socket to receive data from the Server
        self.socket_sub = self.context.socket(zmq.SUB)   
        self.socket_sub.connect(f"{self.protocol}://localhost:{self.SUBport}")
        self.socket_sub.setsockopt(zmq.SUBSCRIBE, b"Test") # encode() turns data into it's binary form
        #f"{self.useCase}.encode('utf-8')"
        self.socket_sub = self.context.socket(zmq.PUB)   
        self.socket_sub.bind(f"{self.protocol}://*:{self.PUBport}")

    def run(self):
        while True:
            topic = self.socket_sub.recv_string()
            data = self.socket_sub.recv_pyobj()



class checkVideoFeedCheating_client(Client):
    def __init__(self, useCase, SUBport, PUBport, messagingType="SUB", protocol="tcp"):
        Client.__init__(self, useCase, SUBport, PUBport, messagingType="SUB", protocol="tcp")

    def checkVideoFeedCheating(videoInput):
        #TODO
        print("Checking video for cheating. Need further implementation")



class checkAudioFeedCheating_client(Client):
    def __init__(self, useCase, SUBport, PUBport, messagingType="SUB", protocol="tcp"):
        Client.__init__(self, useCase, SUBport, PUBport, messagingType="SUB", protocol="tcp")

    def checkVideoFeedCheating(audioInput):
        #TODO
        print("Checking audio for cheating. Need further implementation")

#TODO add further client types