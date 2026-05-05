import zmq
import streamlit as st

#defining what every client has in common
class Client:
    ID = 0 #Number of created Clients
    def __init__(self, useCase, port, messagingType="SUB", protocol="tcp"):
        #Set the attributes to determine the type of client
        self.useCase = useCase
        self.messagingType = messagingType
        self.protocol = protocol
        self.port = port
        print(f"Client for {self.useCase} with ID {self.ID} was created")
        ID = ID+1

        #Create socket for each Client-object
        context = zmq.Context()
        if self.messagingType == "SUB":
            socket_sub = context.socket(zmq.SUB)
  #TODO #else...    
        socket_sub.connect(f"{self.protocol}://localhost:{self.port}")
        socket_sub.setsockopt(zmq.SUBSCRIBE, f"{self.useCase}.encode()") # encode() turns data into it's binary form
    
        while True:
            topic = socket_sub.recv_string()
            data = socket_sub.recv_pyobj()



class streamlitClient(Client):
    def __init__(self, useCase, port,  messagingType="SUB", protocol="tcp"):
                #Set the attributes to determine the type of client
        self.useCase = useCase
        self.messagingType = messagingType
        self.protocol = protocol
        self.port = port
        print(f"Client for {self.useCase} with ID {self.ID} was created")
        ID = ID+1

        #Create socket for each Client-object
        context = zmq.Context()
        if self.messagingType == "SUB":
            socket_sub = context.socket(zmq.SUB)
  #TODO #else...    
        socket_sub.connect(f"{self.protocol}://localhost:{self.port}")
        socket_sub.setsockopt(zmq.SUBSCRIBE, f"{self.useCase}.encode()") # encode() turns data into it's binary form
    
        st.title("Remote exam surveillance")
        placeholder = st.empty()

        while True:
            topic = socket_sub.recv_string()
            data = socket_sub.recv_pyobj()
            placeholder.image(data, channels="BGR")



def main():
    #Create client for each use case like the live stream to streamlit, the video analyzing, the audio analyzing, etc.
    client_stream = Client("STREAM", "5555")
    client_audio = Client("AUDIO", "5556")
    client_video = Client("VIDEO", "5557")
    client_sup = Client("SUP", "5558")
    #...

if __name__ == "__main__":
    main()