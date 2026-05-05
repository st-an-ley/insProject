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
        self.ID = ID
        print(f"Client for {self.useCase} with ID {self.ID} was created")
        ID = ID+1


        context = zmq.Context()
        
        #Create SUBSCRIBER socket to receive data from the Server
        socket_sub = context.socket(zmq.SUB)   
        socket_sub.connect(f"{self.protocol}://localhost:{self.SUBport}")
        socket_sub.setsockopt(zmq.SUBSCRIBE, f"{self.useCase}.encode()") # encode() turns data into it's binary form
    
        socket_sub = context.socket(zmq.PUB)   
        socket_sub.bind(f"{self.protocol}://*:{self.PUBport}")


        while True:
            topic = socket_sub.recv_string()
            data = socket_sub.recv_pyobj()



class checkVideoFeedCheating_client(Client):
    def __init__(self, useCase, SUBport, PUBport, messagingType="SUB", protocol="tcp"):
        Client.__init__(self, useCase, SUBport, PUBport, messagingType="SUB", protocol="tcp")

    def checkVideoFeedCheating(videoInput):
        print("Checking video for cheating. Need further implementation")



class checkAudioFeedCheating_client(Client):
    def __init__(self, useCase, SUBport, PUBport, messagingType="SUB", protocol="tcp"):
        Client.__init__(self, useCase, SUBport, PUBport, messagingType="SUB", protocol="tcp")

    def checkVideoFeedCheating(audioInput):
        print("Checking audio for cheating. Need further implementation")

#TODO add further client types