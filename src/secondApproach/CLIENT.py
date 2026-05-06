import zmq
import streamlit as st

#defining what every client has in common
class Client:
    ID = 0 #Number of created Clients
    def __init__(self, useCase, messagingType="SUB", protocol="tcp"):
        #Set the attributes to determine the type of client
        self.useCase = useCase
        self.messagingType = messagingType
        self.protocol = protocol
        self.SUBport = 6000 + Client.ID*1000 + 1 #5001, 6001, 7001, etc. 
        self.PUBport = 6000 + Client.ID*1000 + 2 #5002, 6002, 7002, etc. 
        self.ID = Client.ID
        print(f"Created Client for {self.useCase} with ID {self.ID}")
        Client.ID = Client.ID+1

 

    def run(self):
        self.context = zmq.Context()
        
        #Create SUBSCRIBER socket to receive data from the Server
        self.socket_sub = self.context.socket(zmq.SUB)   
        self.socket_sub.setsockopt(zmq.SUBSCRIBE, b"Test") # encode() turns data into it's binary form
        #f"{self.useCase}.encode('utf-8')"
        self.socket_sub.connect(f"{self.protocol}://localhost:{self.SUBport}")

        
        self.socket_pub = self.context.socket(zmq.PUB)  
        self.socket_pub.bind(f"{self.protocol}://*:{self.PUBport}")

        while True:
            topic = self.socket_sub.recv_string()
            data = self.socket_sub.recv_pyobj()


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