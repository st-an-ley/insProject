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

def start_streamlit():
##########################################################################################
    #Arguments given when calling "streamlit run start_streamlit.py x y " in script.py
    if "initialized" not in st.session_state:
        context = zmq.Context()

        st.session_state.socket_video_sub = context.socket(zmq.SUB)
        st.session_state.socket_video_sub.setsockopt(zmq.RCVHWM, 1)
        st.session_state.socket_video_sub.bind("tcp://*:6001")
        st.session_state.socket_video_sub.setsockopt_string(zmq.SUBSCRIBE, "cheated")

        st.session_state.socket_audio_sub = context.socket(zmq.SUB)
        st.session_state.socket_audio_sub.bind("tcp://*:6002")
        st.session_state.socket_audio_sub.setsockopt_string(zmq.SUBSCRIBE, "cheated")

        st.session_state.poller = zmq.Poller()
        st.session_state.poller.register(st.session_state.socket_video_sub, zmq.POLLIN)
        st.session_state.poller.register(st.session_state.socket_audio_sub, zmq.POLLIN)

        st.session_state.oldAudioInput = np.zeros(100)

        #IMPORTANT Must use two topics because the user can chose topic for video and audio
        st.session_state.currentVideoTopic = None
        st.session_state.currentAudioTopic = None

        #IMPORTANT End the initialization and ensure that the upper code only runs once
        st.session_state.initialized = True

##########################################################################################
    #Not only store sockets in session_state but also make them accessible in further code
    socket_video_sub = st.session_state.socket_video_sub
    socket_audio_sub = st.session_state.socket_audio_sub
    poller = st.session_state.poller



    poller = zmq.Poller()
    poller.register(socket_video_sub, zmq.POLLIN)
    poller.register(socket_audio_sub, zmq.POLLIN)

##########################################################################################
    #IMPORTANT Streamlit GUI
    st.title("Remote exam surveillance")

    #-------------------------------------------------
    videoSelectionOptions = ["cameraFeed", "faceRecognition", "severalPeople", "deviceDetection" ,"cameraOff"]
    videoSelectionUser = st.pills("Video:", videoSelectionOptions, selection_mode="single", key="video_selection")

    #TODO remove following line
    st.markdown(f"Your selected option: {videoSelectionUser}.")

    placeholder_video = st.empty()
    #-------------------------------------------------



    #-------------------------------------------------
    audioSelectionOptions = ["microphoneSignal", "volume", "whispering", "spokenWords" ,"microphoneOff"]
    audioSelectionUser = st.pills("Audio:", audioSelectionOptions, selection_mode="single", key="audio_selection")

    #TODO remove following line
    st.markdown(f"Your selected option: {audioSelectionUser}.")

    placeholder_audio = st.empty()
    #-------------------------------------------------



    placeholder_cheatedStatus = st.empty()

##########################################################################################

    lastTime = time.time()

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

    #TODO Check if other numbers for timeout are better
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


        #IMPORTANT Check if cheating was detected
        if topicReceived == "cheated":
            placeholder_cheatedStatus.warning(f"CHEATING DETECTED : Type: {metaData[0]}, Name: {metaData[1]}{metaData[2]}, MatNr: {metaData[3]}, Infos:{metaData[4]}")
            #TODO Add uploading of metadata to Google Sheets

##########################################################################################
        #IMPORTANT Converting image to base64 to be able to use it in html-tag in markdown  
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
        topicReceived = socket_audio_sub.recv_string()            
        #-------------------------------------------------

        #Get the metaData for further processing
        #IMPORTANT msgpack.unpackb() already converts Bytes back to "normal" data
        metaData = msgpack.unpackb(socket_audio_sub.recv(), raw=False)

        #IMPORTANT The audio clients always send the chunk of raw bytes as the actual data. The data for display is stored in specialInfo[]
        proofData = socket_audio_sub.recv()

        #IMPORTANT Check if cheating was detected
        if topicReceived == "cheated":
            #Set topic specific cheating status in streamlit
            placeholder_cheatedStatus.warning(f"CHEATING DETECTED : Type: {metaData[0]}, Name: {metaData[1]}{metaData[2]}, MatNr: {metaData[3]}, Infos:{metaData[4]}")
            #TODO Add uploading of metadata to Google Sheets
        
        #IMPORTANT Different than with the video data, we have to separate which audio topic was used, because the 
        # data and with that also the form of displaying it differs

        #TODO Determine how the specific data should be displayed in streamlit
        #TODO For testing reason, displayed as text
        match topicReceived:
            case "rawAudio":
                #TODO For testing reason, displayed as text
                placeholder_audio.text(proofData)

            case "loud":
                st.session_state.oldAudioInput = np.roll(oldAudioInput, -1)
                st.session_state.oldAudioInput[-1] = metaData[4][0]
                placeholder_audio.bar_chart(st.session_state.oldAudioInput)

            case "whisper":
                    #TODO For testing reason, displayed as text
                    placeholder_audio.text(metaData[4][0])

            case "getWords":
                #TODO For testing reason, displayed as text
                placeholder_audio.text(metaData[4][0])

            case "microphoneOff":
                #TODO For testing reason, displayed as text
                placeholder_audio.text(metaData[4][0])

    time.sleep(0.016)
    st.rerun()
#Functions to make it possible for streamlit to change between different topics
#-------------------------------------------------
def switch_topic_video(newTopic):
    #Avoid subscription to active topic
    if st.session_state.currentVideoTopic == newTopic:
        return
    if st.session_state.currentVideoTopic is not None:
        st.session_state.socket_video_sub.setsockopt_string(zmq.UNSUBSCRIBE, st.session_state.currentVideoTopic)
    st.session_state.socket_video_sub.setsockopt_string(zmq.SUBSCRIBE, newTopic)
    st.session_state.currentVideoTopic = newTopic

def switch_topic_audio(newTopic):
    #Avoid subscription to active topic
    if st.session_state.currentAudioTopic == newTopic:
        return
    if st.session_state.currentAudioTopic is not None:
        st.session_state.socket_audio_sub.setsockopt_string(zmq.UNSUBSCRIBE, st.session_state.currentAudioTopic)
    st.session_state.socket_audio_sub.setsockopt_string(zmq.SUBSCRIBE, newTopic)
    st.session_state.currentAudioTopic = newTopic

#-------------------------------------------------
def sendCheatingToGoogleSheets(metaData):
    pass
#-------------------------------------------------


def main():
    start_streamlit()

if __name__ == "__main__":
    main()
