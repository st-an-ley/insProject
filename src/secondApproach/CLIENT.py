import zmq
import streamlit as st
from abc import ABC, abstractmethod
import time
import cv2
import numpy as np 
import struct
import whisper 
import msgpack

#Abstract Class Client enherited from Abstract Base Class 
class Client(ABC):
    ID = 0 #Number of created Clients
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):

        #Set the attributes to determine the type of client
        #Attributes are not allowed to include zeromq
        self.useCase = useCase
        self.messagingType = messagingType
        self.protocol = protocol

        #EVERY CLIENT RECEIVES THE VIDEO AND AUDIO INPUT OVER THOSE PORTS
        self.videoSUBport = 5001  #Port that the server sends the video data from 
        self.audioSUBport = 5002  #Port that the server sends the audio data from
        self.topic =""
        #Store current class ID as object ID
        self.ID = Client.ID

        print(f"Created Client for {self.useCase} with ID {self.ID}")
        Client.ID = Client.ID+1
    
    @abstractmethod
    def run(self):
        pass

    def getMatNr(self):
        #TODO Get the actual MatNr from Group1
        return "123456789"
        

############################################################################################################
#Subclass of Client
#General client for analyzing the video input in any kind of way
class videoCheck_client(Client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        Client.__init__(self, useCase=useCase, messagingType=messagingType, protocol=protocol)
        self.portPUB = 6001
        self.videoSendRate = 30 #Amount of frames sent per second 

        #IMPORTANT Standard values for the buffer size of sending and receiving socket
        #Are the same for every video client but could be changed depending on output of new clients
        self.recvHWM = 1
        self.sendHWM = 1


    #run method for this client only uses data from port 5001, so only video, no audio
    #Every client processing video will need to receive data from port 5001
    def run(self):
        #Everything related to zmq must be initialized outside the __init__ method because
        #zmq-Objects cant be passed to pickle which is used by multiprocess 
        self.context = zmq.Context()
        
        #Create SUBSCRIBER socket to receive data from the Server
        self.socket_video_sub = self.context.socket(zmq.SUB)   
        self.socket_video_sub.setsockopt(zmq.SUBSCRIBE, b"") # encode() turns data into it's binary form
        #f"{self.useCase}.encode('utf-8')"
        self.socket_video_sub.setsockopt(zmq.RCVHWM, self.recvHWM)        
        self.socket_video_sub.connect(f"{self.protocol}://localhost:{self.videoSUBport}") #5001

        #Create PUBLISHER socket to send data to Streamlit
        self.socket_video_pub = self.context.socket(zmq.PUB)  
        self.socket_video_pub.setsockopt(zmq.SNDHWM, self.sendHWM)  
        self.socket_video_pub.connect(f"{self.protocol}://localhost:{self.portPUB}") #6001

        lastTimeVideo = time.time()
        while True:
            # Data should be received and processed as quick as possible; Only the rate of sending should be restricted
            
            #RECEIVE BYTES
            #-----------------------------------------------
            #Receive data as raw bytes
            videoDataInputBytes = self.socket_video_sub.recv()
            #-----------------------------------------------

            #BYTES TO DATA 
            #-----------------------------------------------
            #Turn bytes into numpy array as image with color to be able to work with the data
            #-----------------------------------------------


            if time.time() - lastTimeVideo > 1/self.videoSendRate:
                #Decode image from Bytes to numpyArray
                videoDataInputNumpyArray = cv2.imdecode(np.frombuffer(videoDataInputBytes, np.uint8), cv2.IMREAD_COLOR)


                #PROCESS DATA 
                #-----------------------------------------------
                #Image will be processed in any kind of way
                #IMPORTANT Every client has output of the structure: 
                #[0]=true/false if cheated
                #[1]=clientName to specify message in streamlit
                #[2]=timeStamp to know the time when cheating was detected
                #[3]=matNr to find person in google sheets
                #[4]=specialInfo[] for some clients to save additional data like i.e. number of faces

                #SPLIT PROCESSED OUTPUT IN META DATA AND VIDEO DATA
                #IMPORTANT processVideo() returns two values: The metadata and the actual frame
                videoMetaData, videoFrame = self.processVideo(videoDataInputNumpyArray)
                #-----------------------------------------------

                #DATA TO BYTES
                #-----------------------------------------------
                #Convert image for proof from numpyArray to Bytes
                success, videoDataOutputNumpyJpgBytes = cv2.imencode('.jpg', videoFrame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                
                #Converts bytes numpyArray to the raw bytes 
                #-----------------------------------------------


                #SEND BYTES TO SPECIFIC TOPIC
                #-----------------------------------------------
                #Convert numpy array back to bytes to send the data

                #Every video client sends his image to his specifif topic (st.pills in streamlit)

                #IMPORTANT Send topic as String
                self.socket_video_pub.send_string(f"{self.topic}", zmq.SNDMORE)

                #IMPORTANT SEND META DATA AS BYTES
                #IMPORTANT use packb() and not pack() 
                self.socket_video_pub.send(msgpack.packb(videoMetaData), zmq.SNDMORE)

                #IMPORTANT Send actual image as Bytes
                self.socket_video_pub.send(videoDataOutputNumpyJpgBytes.tobytes()) #SEND IMAGE
                #-----------------------------------------------

                #SEND BYTES TO "cheated" TOPIC IF CHEATING WAS DETECTED
                #-----------------------------------------------
                #IMPORTANT If cheating was detected, send data also to topic "cheated" 
                if videoMetaData[0] == True:
                    #Send to topic "cheated"
                    self.socket_video_pub.send_string("cheated", zmq.SNDMORE)
                    self.socket_video_pub.send(msgpack.packb(videoMetaData), zmq.SNDMORE)
                    self.socket_video_pub.send(videoDataOutputNumpyJpgBytes.tobytes()) #SEND IMAGE

                #-----------------------------------------------

                lastTimeVideo = time.time()
        
    #Method to process a video input in any kind of way
    @abstractmethod
    def processVideo(self, videoInput):
        pass

############################################################################################################
#Specifif use case for processing the video input, in this case to 
#check if the person is same as the embedding from group1
class checkVideoRaw_client(videoCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        videoCheck_client.__init__(self, useCase=useCase, messagingType=messagingType, protocol=protocol)
        self.topic = "rawVideo"
    def run(self):
        videoCheck_client.run(self)


    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processVideo(self, videoInput):
        dataOutput = videoInput
        #The name of the topic will show if cheating was detected 
        #TODO get the correct matrikel number
        cheated = False #No if structure beause this client only copies the input frame
        metaData = [cheated, self.topic, time.time(), "123456789", []]
        videoOutput = videoInput #This client doesnt change the input frame
        return metaData, videoOutput
        #TODO change name and matnum to real values -> from group1

############################################################################################################        
#Specifif use case for processing the video input, in this case to 
#check if the person is same as the embedding from group1
class checkVideoDiffPerson_client(videoCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        videoCheck_client.__init__(self, useCase=useCase, messagingType=messagingType, protocol=protocol)
        self.topic = "diffPerson"

    def run(self):
        videoCheck_client.run(self)


    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processVideo(self, videoInput):
        #TODO change dataOutput to correct data
        cheated = False
        #TODO if cheated == true: cheated = True --> Make it variable and depending on the processing
        metaData = [cheated, self.topic, time.time(), "123456789", []]
        #TODO Draw rectangle at detected face
        dataOutput = cv2.rectangle(videoInput, (100,100), (200,200), (255,0,0) ,1)
        return metaData, dataOutput
        #TODO Implement methods to check for cheating in video

############################################################################################################

#Specifif use case for processing the video input, in this case to check if more than one 
#person is seen in the video feed
class checkVideoSevPeople_client(videoCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        videoCheck_client.__init__(self, useCase=useCase, messagingType=messagingType, protocol=protocol)
        self.topic = "sevPeople"

    def run(self):
        videoCheck_client.run(self)


    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processVideo(self, videoInput):
        #TODO change dataOutput to correct data
        dataOutput = videoInput
        return dataOutput
        #TODO Implement methods to check for cheating in video

############################################################################################################

#Specifif use case for processing the video input, in this case for checking video input for cheating
class checkVideoDevices_client(videoCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        videoCheck_client.__init__(self, useCase=useCase, messagingType=messagingType, protocol=protocol)
        self.topic = "findDevice"

    def run(self):
        videoCheck_client.run(self)


    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processVideo(self, videoInput):
        #TODO change dataOutput to correct data
        dataOutput = videoInput
        return dataOutput
        #TODO Implement methods to check for cheating in video

############################################################################################################
#Specifif use case for processing the video input, in this case for checking video input for cheating
class checkVideoCameraOff_client(videoCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        videoCheck_client.__init__(self, useCase=useCase, messagingType=messagingType, protocol=protocol)
        self.topic = "cameraOff"

    def run(self):
        videoCheck_client.run(self)


    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processVideo(self, videoInput):
        #TODO change dataOutput to correct data
        #TODO Find a way to access camera status without opening the camera in every run
        #camera = cv2.VideoCapture(0)

        #Function to check if camera is available
        #True if available, False if not available
        #cameraOpen = camera.isOpened()
        
        #IMPORTANT False = camera is not off
        #IMPORTANT True = camera is off -> possible cheating
        #if cameraOpen: metaData = [False, self.topic, time.time(), "123456789", ["Camera is available."]]
        #else: metaData = [True, self.topic, time.time(), "123456789", ["Camera not available."]]
        #TODO delete following line
        metaData = [True, self.topic, time.time(), "123456789", ["Camera not available."]]
        dataOutput = videoInput
        return metaData, dataOutput
        #TODO Implement methods to check for cheating in video

############################################################################################################

#Specifif use case for processing the video input, in this case to check if person is going without giving handsign
class checkVideoGoWithoutHandsign_client(videoCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        videoCheck_client.__init__(self, useCase=useCase, messagingType=messagingType, protocol=protocol)
        self.topic = "withoutHandsign"

    def run(self):
        videoCheck_client.run(self)


    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processVideo(self, videoInput):
        #TODO change dataOutput to correct data
        dataOutput = videoInput
        return dataOutput
        #TODO Implement methods to check for cheating in video

############################################################################################################
#Abstract class for analyzing the audio input in any kind of way
class audioCheck_client(Client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        Client.__init__(self, useCase=useCase, messagingType=messagingType, protocol=protocol)
        self.portPUB = 6002
        self.audioSendRate = 10 #Amount of data samples sent per second

        #IMPORTANT Standard values for the buffer size of sending and receiving socket
        #Are different depending on subclass but should be higher than 1 for most use cases since audio is connected over time (different than to frames, atleast for our usercases)
        self.recvHWM = 1
        self.sendHWM = 1 

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
        self.socket_audio_sub.setsockopt(zmq.RCVHWM, self.recvHWM)
        self.socket_audio_sub.connect(f"{self.protocol}://localhost:{self.audioSUBport}") #5002

        #Create PUBLISHER socket to send data to Streamlit
        self.socket_audio_pub = self.context.socket(zmq.PUB)  
        #self.socket_audio_pub.setsockopt(zmq.SNDHWM, self.sendHWM)
        self.socket_audio_pub.connect(f"{self.protocol}://localhost:{self.portPUB}") #6002

        lastTimeAudio = time.time()
        while True:
            # Data should be received and processed as quick as possible; Only the rate of sending should be restricted
            
            
            #RECEIVE BYTES
            #-----------------------------------------------
            # audio is received as raw bytes
            audioDataInputBytes = self.socket_audio_sub.recv()
            #-----------------------------------------------


            #BYTES TO DATA 
            #-----------------------------------------------
            # Nothing to do since we can work with bytes directly for audio
            #-----------------------------------------------


            #PROCESS DATA 
            #-----------------------------------------------
            #Process data (bytes because of audio)
            #-----------------------------------------------


            #DATA TO BYTES
            #-----------------------------------------------
            #-----------------------------------------------


            if time.time() - lastTimeAudio > 1/self.audioSendRate:
                
                #AUdio will be processed in any kind of way
                #IMPORTANT Every client has output of the structure: 
                #[0]=true/false if cheated
                #[1]=clientName to specify message in streamlit
                #[2]=timeStamp to know the time when cheating was detected
                #[3]=matNr to find person in google sheets
                #[4]=specialInfo[] for some clients to save additional data like i.e. number of faces

                audioMetaData, audioChunk = self.processAudio(audioDataInputBytes) 


                #SEND BYTES TO SPECIFIF TOPIC WHICH CAN BE CHOSEN IN STREAMLIT
                #-----------------------------------------------
                #IMPORTANT Send topic as string
                self.socket_audio_pub.send_string(f"{self.topic}", zmq.SNDMORE)
                #IMPORTANT Send meta data for audio
                self.socket_audio_pub.send(msgpack.packb(audioMetaData), zmq.SNDMORE)
                #IMPORTANT Send audio chunk
                self.socket_audio_pub.send(audioChunk)
                #-----------------------------------------------

                #SEND TO TOPIC "cheated" IF CHEATING WAS DETECTED
                #-----------------------------------------------
                #IMPORTANT If cheating was detected, send data also to topic "cheated"
                if audioMetaData[0] == True:
                    #Send to topic "cheated"
                    self.socket_audio_pub.send_string("cheated", zmq.SNDMORE)
                    self.socket_audio_pub.send(msgpack.packb(audioMetaData), zmq.SNDMORE)
                    self.socket_audio_pub.send(audioChunk)

                #-----------------------------------------------

                lastTimeAudio = time.time()
        
    @abstractmethod
    def processAudio(self, audioInput):
        pass

############################################################################################################
#Specifif use case for processing the audio input, in this case to check if the person is whispering
class checkAudioRaw_client(audioCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        audioCheck_client.__init__(self, useCase=useCase, messagingType=messagingType, protocol=protocol)
        self.topic = "rawAudio"

        #Can stay at 1 because data should be as realtime as possible; Helps for performance
        self.sendHWM = 1
        self.recvHWM = 1
        

    def run(self):
        audioCheck_client.run(self)
    
    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processAudio(self, audioInput):
        cheated = False
        audioOutput = audioInput
        #IMPORTANT Change the matNr to the number sent by Group1
        metaData = [cheated, self.topic, time.time(), "123456789", []]
        return metaData, audioOutput

############################################################################################################
#Specifif use case for processing the audio input, in this case to check if volume threshold in dB is breached
class checkAudioLoud_client(audioCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        audioCheck_client.__init__(self, useCase=useCase, messagingType=messagingType, protocol=protocol)
        self.topic = "loud"
        
        #Can stay at 1 because volume is independent on past data; Helps for performance
        self.sendHWM = 1
        self.recvHWM = 1

        # #Using OpenAIs Neural Network whisper to extract words from recorded samples
        # #Loading model; Chosing "base" because it is small enough to run without GPU
        # self.whisper_model = whisper.load_model("base")
        # #Time in seconds in which whisper can search for words
        # self.secondsForWhisper = 5

        # #fs=20000 : values per second; values/second * seconds = values over all seconds
        # self.storageForWhisper = np.zeros(20000*self.secondsForWhisper)


    def run(self):
        audioCheck_client.run(self)
    
    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processAudio(self, audioInput):
        #audioInput is received as raw bytes
        #The input is the size of parameter CHUNK in Server, here 1024

        #Turn Bytes into NumpyArray with data of type float32
        #Every float represents the position of the membran at the specific time
        #Float only because np.mean and np.abs only work with float
        audioNpArray = np.frombuffer(audioInput, dtype=np.int16).astype(np.float32)
        audioNpArrayMeanAbs = np.mean(np.abs(audioNpArray))

        #Normalize to range from -1 to 1, to get same value for every data format (Int16 less values than Int32 but same range)
        audioNpArrayMeanAbsNormalized = audioNpArrayMeanAbs / 32768

        #smallest reference possible with 16 bits, positive because np.abs() was applied before
        referenceValueForLog = 1.0 / 32768.0 

        #To avoid log(0)
        audioNpArrayMeanAbsNormalized = max(audioNpArrayMeanAbsNormalized, 1e-10)  
        audioIndB = 20 * np.log10(audioNpArrayMeanAbsNormalized / referenceValueForLog)

        cheated = False
        dBThreshold = 50

        #Check for cheating by using a simple threshold
        #TODO Change method from threshold to actual detection of talking
        if audioIndB > dBThreshold:
            cheated = True

            #TODO Find a way of how to store the audio input 

        metaData = [bool(cheated), self.topic, time.time(), "123456789", [float(audioIndB)]]
        return metaData, audioInput   # audioInput as chunk for proof, data for display in specialInfo[]

############################################################################################################
#Specifif use case for processing the audio input, in this case to check if the person is whispering
class checkAudioWhisper_client(audioCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        audioCheck_client.__init__(self, useCase=useCase, messagingType=messagingType, protocol=protocol)
        self.topic = "whisper"

        # [ 20.000 f/s : 512 f/call = 39,0625 call/s ] would have to be completed
        # [39,0625 call/s * 10s = 390,625 call ] 10s as an estimation for time of processing
        # 110 more for safety
        self.recvHWM = 500
        self.sendHWM = 500

    def run(self):
        audioCheck_client.run(self)
    
    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processAudio(self, audioInput):
        pass 

############################################################################################################
#Specifif use case for processing the audio input, in this case to check if microphone is turned off/muted
class checkAudioMicOff_client(audioCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        audioCheck_client.__init__(self, useCase=useCase, messagingType=messagingType, protocol=protocol)
        self.topic = "microphoneOff"

        #IMPORTANT Should be as realtime as possible to see changes as quick as possible
        self.recvHWM = 1 
        self.sendHWM = 1 

    def run(self):
        audioCheck_client.run(self)
    
    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processAudio(self, audioInput):
        pass 

############################################################################################################
#Specifif use case for processing the audio input, in this case for extracting spoken words from audio sequence
class checkAudioGetWords_client(audioCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        audioCheck_client.__init__(self, useCase=useCase, messagingType=messagingType, protocol=protocol)
        self.topic = "getWords"

        # [ 20.000 f/s : 512 f/call = 39,0625 call/s ] would have to be completed
        # [39,0625 call/s * 10s = 390,625 call ] 10s as an estimation for time of processing
        # 110 more for safety
        self.recvHWM = 500
        self.sendHWM = 500

    def run(self):
        audioCheck_client.run(self)
    
    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processAudio(self, audioInput):
        pass 

############################################################################################################
#TODO add further client types
