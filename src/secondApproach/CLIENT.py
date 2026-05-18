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



############################################################################################################
#Subclass of Client
#General client for analyzing the video input in any kind of way
class videoCheck_client(Client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        Client.__init__(self, useCase="", messagingType="SUB", protocol="tcp")
        self.portPUB = 6001
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
        self.socket_video_sub.setsockopt(zmq.RCVHWM, 1)        
        self.socket_video_sub.connect(f"{self.protocol}://localhost:{self.videoSUBport}") #5001

        #Create PUBLISHER socket to send data to Streamlit
        self.socket_video_pub = self.context.socket(zmq.PUB)  
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
            videoDataInputNumpyArray = cv2.imdecode(np.frombuffer(videoDataInputBytes, np.uint8), cv2.IMREAD_COLOR)
            #-----------------------------------------------


            #PROCESS DATA 
            #-----------------------------------------------
            #Image will be processed in any kind of way
            #IMPORTANT Every client has output of the structure: 
            #[0]=true/false if cheated
            #[1]=clientName to specify message in streamlit
            #[2]=timeStamp to know the time when cheating was detected
            #[3]=matNr to find person in google sheets
            #[4]=specialInfo[] for some clients to save additional data like i.e. number of faces
            processedVideoOutput = self.processVideo(videoDataInputNumpyArray)

            #SPLIT PROCESSED OUTPUT IN META DATA AND VIDEO DATA
            videoData = processedVideoOutput[1]
            processedVideoOutput.pop(1)
            videoMetaData = processedVideoOutput
            #-----------------------------------------------


            #DATA TO BYTES
            #-----------------------------------------------
            #Convert image for proof from numpyArray to Bytes
            success, videoDataOutputNumpyJpgBytes = cv2.imencode('.jpg', videoData, [cv2.IMWRITE_JPEG_QUALITY, 50])
            
            #Converts bytes numpyArray to the raw bytes 
            imageDataOutputRawBytes = videoDataOutputNumpyJpgBytes.tobytes()
            videoMetaDataInBytes = msgpack.packb(videoMetaData)
            #-----------------------------------------------

            if time.time() - lastTimeVideo > 1/self.videoSendRate:


                #SEND BYTES TO SPECIFIC TOPIC
                #-----------------------------------------------
                #Convert numpy array back to bytes to send the data

                #Every video client sends his image to his specifif port (st.pills in streamlit)

                #SEND TOPIC AS STRING
                self.socket_video_pub.send_string(f"{self.topic}", zmq.SNDMORE)

                #SEND META DATA AS BYTES
                #IMPORTANT use packb() and noch pack() 
                self.socket_video_pub.send(msgpack.packb(videoMetaData), zmq.SNDMORE)

                #SEND IMAGE AS BYTES
                self.socket_video_pub.send(videoDataOutputNumpyJpgBytes.tobytes()) #SEND IMAGE
                #-----------------------------------------------

                #SEND BYTES TO "cheated" TOPIC IF CHEATING WAS DETECTED
                #-----------------------------------------------
                #If cheating was detected
                if "cheated" in videoMetaData[0]:
                    self.socket_video_pub.send_string("cheated", zmq.SNDMORE)
                    self.socket_video_pub.send(imageDataOutputRawBytes)

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
        videoCheck_client.__init__(self, useCase="", messagingType="SUB", protocol="tcp")
        self.topic = "cheatedrawVideo"
    def run(self):
        videoCheck_client.run(self)


    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processVideo(self, videoInput):
        dataOutput = videoInput
        #The name of the topic will show if cheating was detected 
        #TODO get the correct matrikel number
        metaData = [False, self.topic, time.time(), "123456789", []]
        videoOutput = videoInput
        return metaData, videoOutput
        #TODO change name and matnum to real values -> from group1

############################################################################################################        
#Specifif use case for processing the video input, in this case to 
#check if the person is same as the embedding from group1
class checkVideoDiffPerson_client(videoCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        videoCheck_client.__init__(self, useCase="", messagingType="SUB", protocol="tcp")
        self.topic = "cheateddiffPerson"

    def run(self):
        videoCheck_client.run(self)


    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processVideo(self, videoInput):
        #TODO change dataOutput to correct data
        dataOutput = videoInput
        return dataOutput
        #TODO Implement methods to check for cheating in video

############################################################################################################

#Specifif use case for processing the video input, in this case to check if more than one 
#person is seen in the video feed
class checkVideoSevPeople_client(videoCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        videoCheck_client.__init__(self, useCase="", messagingType="SUB", protocol="tcp")
        self.topic = "cheatedsevPeople"

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
        videoCheck_client.__init__(self, useCase="", messagingType="SUB", protocol="tcp")
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
        videoCheck_client.__init__(self, useCase="", messagingType="SUB", protocol="tcp")
        self.topic = "cameraOff"

    def run(self):
        videoCheck_client.run(self)


    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processVideo(self, videoInput):
        #TODO change dataOutput to correct data
        dataOutput = videoInput
        return dataOutput
        #TODO Implement methods to check for cheating in video

############################################################################################################

#Specifif use case for processing the video input, in this case to check if person is going without giving handsign
class checkVideoGoWithoutHandsign_client(videoCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        videoCheck_client.__init__(self, useCase="", messagingType="SUB", protocol="tcp")
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
        Client.__init__(self, useCase="", messagingType="SUB", protocol="tcp")
        self.portPUB = 6002
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
        self.socket_audio_sub.connect(f"{self.protocol}://localhost:{self.audioSUBport}") #5002

        #Create PUBLISHER socket to send data to Streamlit
        self.socket_audio_pub = self.context.socket(zmq.PUB)  
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
            processedAudioOutput = self.processAudio(audioDataInputBytes)
            audioData = processedAudioOutput[1]
            processedAudioOutput.pop(1)
            audioMetaData = processedAudioOutput
            #-----------------------------------------------


            #DATA TO BYTES
            #-----------------------------------------------
            audioDataInBytes = msgpack.packb(audioData)
            audioMetaDataInBytes = msgpack.packb(audioMetaData)
            #-----------------------------------------------


            if time.time() - lastTimeAudio > 1/self.audioSendRate:


                #SEND BYTES TO SPECIFIF TOPIC WHICH CAN BE CHOSEN IN STREAMLIT
                #-----------------------------------------------
                self.socket_audio_pub.send_string(f"{self.topic}", zmq.SNDMORE)
                self.socket_audio_pub.send(audioMetaDataInBytes)
                self.socket_audio_pub.send(audioDataInBytes)
                #-----------------------------------------------

                #SEND TO TOPIC "cheated" IF CHEATING WAS DETECTED
                #-----------------------------------------------
                # If cheating was detected
                if audioMetaData[0] == "cheated":
                    self.socket_audio_pub.send_string("cheated", zmq.SNDMORE)
                    self.socket_audio_pub.send(audioData)
                #-----------------------------------------------

                lastTimeAudio = time.time()
        
    @abstractmethod
    def processAudio(self, audioInput):
        pass

############################################################################################################
#Specifif use case for processing the audio input, in this case to check if the person is whispering
class checkAudioRaw_client(audioCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        audioCheck_client.__init__(self, useCase="", messagingType="SUB", protocol="tcp")
        self.topic = "rawAudio"

    def run(self):
        audioCheck_client.run(self)
    
    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processAudio(self, audioInput):
        dataOutput = audioInput
        outputList = [self.topic, dataOutput, ["firstNameTest", "lastNameTest", "MatNumTest"], time.time()]
        return outputList

############################################################################################################
#Specifif use case for processing the audio input, in this case to check if volume threshold in dB is breached
class checkAudioLoud_client(audioCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        audioCheck_client.__init__(self, useCase="", messagingType="SUB", protocol="tcp")
        self.topic = "loud"

        # #Using OpenAIs Neural Network whisper to extract words from recorded samples
        # #Loading model; Chosing "base" because it is small enough to run without GPU
        # self.whisper_model = whisper.load_model("base")
        # #Time in seconds in which whisper can search for words
        # self.secondsForWhisper = 5

        # #fs=20000 : values per second; values/second * seconds = values over all seconds
        # self.storageForWhisper = np.zeros(20000*self.secondsForWhisper)


    def run(self):
        audioCheck_client.run(self)
        self.storageForWhisper = np.roll(self.storageForWhisper, -1)
        self.storageForWhisper[-1] = audioDatadB
    
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

        listDataCheated = [audioIndB,cheated]

        return listDataCheated

############################################################################################################
#Specifif use case for processing the audio input, in this case to check if the person is whispering
class checkAudioWhisper_client(audioCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        audioCheck_client.__init__(self, useCase="", messagingType="SUB", protocol="tcp")
        self.topic = "whisper"

    def run(self):
        audioCheck_client.run(self)
    
    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processAudio(self, audioInput):
        pass 

############################################################################################################
#Specifif use case for processing the audio input, in this case to check if microphone is turned off/muted
class checkAudioMicOff_client(audioCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        audioCheck_client.__init__(self, useCase="", messagingType="SUB", protocol="tcp")
        self.topic = "microphoneOff"

    def run(self):
        audioCheck_client.run(self)
    
    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processAudio(self, audioInput):
        pass 

############################################################################################################
#Specifif use case for processing the audio input, in this case for extracting spoken words from audio sequence
class checkAudioGetWords_client(audioCheck_client):
    def __init__(self, useCase="", messagingType="SUB", protocol="tcp"):
        audioCheck_client.__init__(self, useCase="", messagingType="SUB", protocol="tcp")
        self.topic = "getWords"

    def run(self):
        audioCheck_client.run(self)
    
    #Overwrites the methods from the parent class; Will be automatically called when executed on child class
    def processAudio(self, audioInput):
        pass 

############################################################################################################
#TODO add further client types
