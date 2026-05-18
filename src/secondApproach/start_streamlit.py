import streamlit as st
import zmq
import sys
import numpy as np
import cv2
import time
import base64
import struct
import msgpack

#Use the package subprocess to start streamlit in the background and receive data from the clients

currentTopicSubscribedTo = None 


def start_streamlit():
##########################################################################################
    #Arguments given when calling "streamlit run start_streamlit.py x y " in script.py
    videoInputPort = 6001
    audioInputPort = 6002

    context = zmq.Context()


    #SUBSCRIBER socket for video with corresponding port
    socket_video_sub = context.socket(zmq.SUB)
    socket_video_sub.setsockopt(zmq.RCVHWM, 1)        
    socket_video_sub.bind(f"tcp://*:{videoInputPort}")
    socket_video_sub.setsockopt(zmq.SUBSCRIBE, b'')


    #SUBSCRIBER socket for audio with corresponding port
    socket_audio_sub = context.socket(zmq.SUB)
    socket_audio_sub.bind(f"tcp://*:{audioInputPort}")
    socket_audio_sub.setsockopt(zmq.SUBSCRIBE, b'')

##########################################################################################
    #IMPORTANT
    #ALWAYS LISTENING TO MESSAGES WITH TOPIC "cheated" on video socket
    #Specific topics follow down below
    socket_video_sub.setsockopt_string(zmq.SUBSCRIBE, "cheated")


    #IMPORTANT
    #ALWAYS LISTENING TO MESSAGES WITH TOPIC "cheated" on audio socket
    #Specific topics follow down below
    socket_audio_sub.setsockopt_string(zmq.SUBSCRIBE, "cheated")



    poller = zmq.Poller()
    poller.register(socket_video_sub, zmq.POLLIN)
    poller.register(socket_audio_sub, zmq.POLLIN)

##########################################################################################
    #IMPORTANT Streamlit GUI
    st.title("Remote exam surveillance")

    #-------------------------------------------------
    videoSelectionOptions = ["cameraFeed", "faceRecognition", "severalPeople", "deviceDetection" ,"cameraOff"]
    videoSelectionUser = st.pills("Video Selection Options: ", videoSelectionOptions, selection_mode="single")
    #TODO remove following line
    st.markdown(f"Your selected options: {videoSelectionUser}.")

    placeholder_video = st.empty()
    #-------------------------------------------------



    #-------------------------------------------------
    audioSelectionOptions = ["microphoneSignal", "volume", "whispering", "spokenWords" ,"microphoneOff"]
    audioSelectionUser = st.pills("Audio Selection Options: ", audioSelectionOptions, selection_mode="single")
    #TODO remove following line
    st.markdown(f"Your selected options: {audioSelectionUser}.")

    placeholder_audio = st.empty()
    #-------------------------------------------------



    placeholder_cheatedStatus = st.empty()

##########################################################################################
    oldAudioInput = np.zeros(100)

    lastTime = time.time()

    while True:
##########################################################################################
        #IMPORTANT Change video topic depending on choice in GUI
        #---------------------------------------------------------------------------------
        #Check current video menu in streamlit GUI
        match videoSelectionUser:
            case "cameraFeed":
                switch_topic_video("rawVideo")
                #socket_video_sub.setsockopt_string(zmq.SUBSCRIBE, "rawVideo")
                
            case "faceRecognition":
                switch_topic_video("diffPerson")
                #socket_video_sub.setsockopt_string(zmq.SUBSCRIBE, "diffPerson")
                
            case "severalPeople":
                switch_topic_video("sevPeople")
                #socket_video_sub.setsockopt_string(zmq.SUBSCRIBE, "sevPeople")
                
            case "deviceDetection":
                switch_topic_video("findDevice")
                #socket_video_sub.setsockopt_string(zmq.SUBSCRIBE, "findDevice")
                
            case "cameraOff":
                switch_topic_video("cameraOff")
                #socket_video_sub.setsockopt_string(zmq.SUBSCRIBE, "cameraOff")
                
        #---------------------------------------------------------------------------------

        #IMPORTANT Change audio topic depending on choice in GUI
        #---------------------------------------------------------------------------------
        #Check current video menu in streamlit GUI
        match audioSelectionUser:
            case "microphoneSignal":
                switch_topic_audio("rawAudio")
                #socket_audio_sub.setsockopt_string(zmq.SUBSCRIBE, "rawAudio")
                
            case "volume":
                switch_topic_audio("loud")
                #socket_audio_sub.setsockopt_string(zmq.SUBSCRIBE, "loud")
                
            case "whispering":
                switch_topic_audio("whisper")
                #socket_audio_sub.setsockopt_string(zmq.SUBSCRIBE, "whisper")
                
            case "spokenWords":
                switch_topic_audio("getWords")
                #socket_audio_sub.setsockopt_string(zmq.SUBSCRIBE, "getWords")
                
            case "microphoneOff":
                switch_topic_audio("microphoneOff")
                #socket_audio_sub.setsockopt_string(zmq.SUBSCRIBE, "microphoneOff")
                
        #---------------------------------------------------------------------------------
 ##########################################################################################           

        pollerSockets = dict(poller.poll(timeout=16))

##########################################################################################
        #IMPORTANT Check if data was sent on socket_video_sub
        if socket_video_sub in pollerSockets: #check the port 6001

            #Get the Topic, "cheated" or specific topic
            topicReceived = socket_video_sub.recv_string()

            #Get the metaData for further processing
            #IMPORTANT msgpack.unpackb() already converts Bytes back to "normal" data
            metaData = msgpack.unpackb(socket_video_sub.recv(), raw=False)

            #Get the actual frame as Bytes
            videoFrameBytes = socket_video_sub.recv()

            #Frame from Bytes to (H,W,C)
            videoFrame = cv2.imdecode(np.frombuffer(videoFrameBytes, np.uint8), cv2.IMREAD_COLOR)


            #IMPORTANT Check if cheating was detected
            if topicReceived == "cheated":
                placeholder_cheatedStatus.warning(f"CHEATING DETECTED : Type: {metaData[1]}, Name: {metaData[2]}{metaData[3]}, MatNr: {metaData[4]}, Infos:{metaData[5]}")
                #TODO Add uploading of metadata to Google Sheets



            #videoDataInputNumpyArray = cv2.imdecode(np.frombuffer(videoDataInputBytes, np.uint8), cv2.IMREAD_COLOR)
            #placeholder_video.image(videoDataInputNumpyArray, channels="BGR")

            #base64 can only display 64 signs: A-Z, a-z, 0-9, +, /
            #Browsers/HTML can convert base64 back to bytes and display the image; No need to convert bytes to numpyArray
            imageInb64 = base64.b64encode(videoFrameBytes).decode()
            #Use of markdown avoids creation of react component
            placeholder_video.markdown(
                f'<img src="data:image/jpeg;base64,{imageInb64}" style="width:100%">',
                unsafe_allow_html=True
            )

            currentTime = time.time()
            timePassed = currentTime-lastTime

            print("Streamlit hat ", timePassed, "s gebraucht für frame Rendering")
            lastTime = currentTime
##########################################################################################

        #IMPORTANT Check if data was sent on socket_audio_sub
        if socket_audio_sub in pollerSockets: #Check the port 6002
            #Audio data is of type int16 and represents the position of the membran of the microphone
            #Every value is represented as 16 bits = 2 Bytes
            #16 bits : 65536 values from -32768 to +32767 


            #READ DATA AND SEPARATE IT INTO AUDIO AND CHEATING DATA
            #-------------------------------------------------
            #Get the Topic, "cheated" or specific topic
            topicReceived = socket_video_sub.recv_string()            
            #-------------------------------------------------

            #Get the metaData for further processing
            #IMPORTANT msgpack.unpackb() already converts Bytes back to "normal" data
            metaData = msgpack.unpackb(socket_video_sub.recv(), raw=False)

            #IMPORTANT The audio clients always send the chunk of raw bytes as the actual data. The data for display is stored in specialInfo[]
            proofData = socket_audio_sub.recv()

            #IMPORTANT Data for display is always the same for the video clients, but different for the audio clients
            displayDataAudio = None

            #IMPORTANT Check if cheating was detected
            if topicReceived == "cheated":
                #Set topic specific cheating status in streamlit
                placeholder_cheatedStatus.warning(f"CHEATING DETECTED : Type: {metaData[1]}, Name: {metaData[2]}{metaData[3]}, MatNr: {metaData[4]}, Infos:{metaData[5]}")
                #TODO Add uploading of metadata to Google Sheets
            
            elif topicReceived == "rawAudio":
                #Its the same as the proofData in this case
                displayDataAudio = proofData
            else:
                #IMPORTANT Every client except "rawAudio" sends the data for display in the specialInfo[] of the metaData
                displayDataAudio = metaData[4]


            #TODO Determine how the specific data should be displayed in streamlit
            #TODO For testing reason, display as text
            match topicReceived:
                case "rawAudio":
                    #TODO For testing reason, display as text
                    placeholder_audio.text(displayDataAudio)

                case "loud":
                    oldAudioInput = np.roll(oldAudioInput, -1)
                    oldAudioInput[-1] = displayDataAudio
                    placeholder_audio.bar_chart(oldAudioInput)

                case "whisper":
                     #TODO For testing reason, display as text
                     placeholder_audio.text(displayDataAudio)

                case "getWords":
                    #TODO For testing reason, display as text
                    placeholder_audio.text(displayDataAudio)

                case "microphoneOff":
                    #TODO For testing reason, display as text
                    placeholder_audio.text(displayDataAudio)


#Functions to make it possible for streamlit to change between different topics
#-------------------------------------------------
def switch_topic_video(newTopic):
    global currentTopicSubscribedTo
    global socket_video_sub
    #To avoid issues at first topic
    if currentTopicSubscribedTo != None:
        socket_video_sub.setsockopt_string(zmq.UNSUBSCRIBE, currentTopicSubscribedTo)
    socket_video_sub.setsockopt_string(zmq.SUBSCRIBE, newTopic)
    currentTopicSubscribedTo = newTopic

def switch_topic_audio(newTopic):
    global currentTopicSubscribedTo
    global socket_audio_sub
    #To avoid issues at first topic
    if currentTopicSubscribedTo != None:
        socket_audio_sub.setsockopt_string(zmq.UNSUBSCRIBE, currentTopicSubscribedTo)
    socket_audio_sub.setsockopt_string(zmq.SUBSCRIBE, newTopic)
    currentTopicSubscribedTo = newTopic

#-------------------------------------------------
def sendCheatingToGoogleSheets(metaData):
    pass
#-------------------------------------------------


def main():
    start_streamlit()

if __name__ == "__main__":
    main()
