import streamlit as st
import zmq
import numpy as np
import base64
import msgpack
import time
import altair as alt
import pandas as pd


#FILEINFO : This file only handles incoming data and displays it on the GUI. No processing, no sending data to google sheets
def start_streamlit():

    if "initialized" not in st.session_state:
        context = zmq.Context()

        st.session_state.socket_video_sub = context.socket(zmq.SUB)
        st.session_state.socket_video_sub.setsockopt(zmq.RCVHWM, 1)
        st.session_state.socket_video_sub.bind("tcp://*:6001")
        st.session_state.socket_video_sub.setsockopt_string(zmq.SUBSCRIBE, "cheated")

        st.session_state.socket_audio_sub = context.socket(zmq.SUB)
        #TODO Check if next line makes sense
        st.session_state.socket_audio_sub.setsockopt(zmq.RCVHWM, 1)
        st.session_state.socket_audio_sub.bind("tcp://*:6002")
        st.session_state.socket_audio_sub.setsockopt_string(zmq.SUBSCRIBE, "cheated")

        st.session_state.poller = zmq.Poller()
        st.session_state.poller.register(st.session_state.socket_video_sub, zmq.POLLIN)
        st.session_state.poller.register(st.session_state.socket_audio_sub, zmq.POLLIN)

        st.session_state.oldAudioInput = np.zeros(100)
        st.session_state.currentVideoTopic = None
        st.session_state.currentAudioTopic = None
        st.session_state.lastTimeVideo = time.time() 
        st.session_state.lastTimeAudio = time.time()  
        st.session_state.initialized = True

        st.session_state.videoSelectionOptions = ["cameraFeed", "faceRecognition", "severalPeople", "deviceDetection", "cameraOff"]
        st.session_state.audioSelectionOptions = ["microphoneSignal", "volume", "whispering", "spokenWords", "microphoneOff"]


    socket_video_sub = st.session_state.socket_video_sub
    socket_audio_sub = st.session_state.socket_audio_sub
###########################################################################################
    st.title("Remote exam surveillance")
    placeholder_cheatedStatus = st.empty()
    #TODO change infos to real data
    placeholder_studentInfo = st.header("firstName, lastName, matNr, nameOfExam")
    placeholder_cheatedStatus.success("No cheating detected.")
    
###########################################################################################
    #IMPORTANT st.fragment() makes it possible to run code only when a streamlit widget inside of it has changed 

    #IMPORTANT Only runs, when user has chosen a different video pill
    @st.fragment()
    def videoPillsTopicReaction():
            videoSelectionUser = st.pills("Video:",st.session_state.videoSelectionOptions,selection_mode="single",key="video_selection_fragment")
            if videoSelectionUser is None:
                unsubscribeVideoTopic()
            else:
                match videoSelectionUser:
                    case "cameraFeed": switchTopicVideo("rawVideo")
                    case "faceRecognition": switchTopicVideo("diffPerson")
                    case "severalPeople": switchTopicVideo("sevPeople")
                    case "deviceDetection": switchTopicVideo("findDevice")
                    case "cameraOff": switchTopicVideo("cameraOff")

    videoPillsTopicReaction()
###########################################################################################
    placeholder_video=st.empty()
###########################################################################################

    #IMPORTANT Only runs, when user has chosen a different video pill
    @st.fragment()
    def audioPillsTopicReaction():
            audioSelectionUser = st.pills("Audio:",st.session_state.audioSelectionOptions,selection_mode="single",key="audio_selection_fragment")
            if audioSelectionUser is None:
                unsubscribeAudioTopic()
            else:
                match audioSelectionUser:
                    case "microphoneSignal": switchTopicAudio("rawAudio")
                    case "volume":           switchTopicAudio("loud")
                    case "whispering":       switchTopicAudio("whisper")
                    case "spokenWords":      switchTopicAudio("getWords")
                    case "microphoneOff":    switchTopicAudio("microphoneOff")

    audioPillsTopicReaction()
###########################################################################################
    placeholder_audio=st.empty()
###########################################################################################


###########################################################################################
    #st.fragment makes only this part rerun at rate of run_every
    @st.fragment(run_every=0.033) #1/30 
    def streamVideo():
        #IMPORTANT Check if no Pill for video was chosen; Then the poller should not even poll from the socket 
        if st.session_state.currentVideoTopic is None:
            placeholder_video.empty()
            return

        #Check if data was published to video socket by polling the poller 
        #IMPORTANT timeout determines who many milliseconds the poller waits for new data to come in; 
        # During this time the whole process stops, so for real time apps it should be zero
        pollerSockets = dict(st.session_state.poller.poll(timeout=0))

        if socket_video_sub in pollerSockets:
            topicReceived = socket_video_sub.recv_string()
            metaData = msgpack.unpackb(socket_video_sub.recv(), raw=False)
            

            if topicReceived == "cheated":
                placeholder_cheatedStatus.warning(
                    f"CHEATING DETECTED: Type: {metaData[1]}, "
                    f"Time: {metaData[2]}, MatNr: {metaData[3]}, Infos: {metaData[4]}"
                )
            else:
                #IMPORTANT If topic is "cheated", client only sends 2 values, otherwise 3. So one more has to be received
                videoBytes = socket_video_sub.recv()
                #timeEncodeAndMarkdownBefore = time.time()
                b64 = base64.b64encode(videoBytes).decode()
                #placeholder_video.image(videoBytes)
                placeholder_video.markdown(
                    f'<img src="data:image/jpeg;base64,{b64}" style="width:100%">',
                    unsafe_allow_html=True
                )
                timeEncodeAndMarkdownAfter = time.time()


                #currentTime = time.time()
                #print("VIDEO insgesamt hat", currentTime - st.session_state.lastTimeVideo, "s gebraucht")
                #print("VIDEO encodeMarkdown hat", timeEncodeAndMarkdownAfter - timeEncodeAndMarkdownBefore, "s gebraucht")
                #st.session_state.lastTimeVideo = currentTime

    @st.fragment(run_every=0.1) #1/10
    def streamAudio():
        #IMPORTANT Check if no Pill for audio was chosen; Then the poller should not even poll from the socket 
        if st.session_state.currentAudioTopic is None:
            placeholder_audio.empty()
            return
        #IMPORTANT timeout determines who many milliseconds the poller waits for new data to come in; 
        # During this time the whole process stops, so for real time apps it should be zero
        pollerSockets = dict(st.session_state.poller.poll(timeout=0))
        if socket_audio_sub in pollerSockets:
            topicReceived = socket_audio_sub.recv_string()
            metaData = msgpack.unpackb(socket_audio_sub.recv(), raw=False)

            if topicReceived == "cheated":
                placeholder_cheatedStatus.warning(
                    f"CHEATING DETECTED: Type: {metaData[1]}, "
                    f"Time: {metaData[2]}, MatNr: {metaData[3]}, Infos: {metaData[4]}"
                )

            else:
                #IMPORTANT If topic is "cheated", client only sends 2 values, otherwise 3. So one more has to be received
                proofData = socket_audio_sub.recv()
                match topicReceived:
                    case "rawAudio":
                        placeholder_audio.text(proofData)
                    case "loud":
                        st.session_state.oldAudioInput = np.roll(st.session_state.oldAudioInput, -1)
                        st.session_state.oldAudioInput[-1] = metaData[4][0]

                        placeholder_audio.bar_chart(st.session_state.oldAudioInput)



                    case "whisper" | "getWords" | "microphoneOff":
                        placeholder_audio.text(metaData[4][0])
            
            #currentTime = time.time()
            #print("AUDIO hat", currentTime - st.session_state.lastTimeAudio, "s gebraucht")
            #st.session_state.lastTimeAudio = currentTime

    streamVideo()   #starting the video fragment
    streamAudio()   #starting the audio fragment
###########################################################################################
#IMPORTANT Change between topics when chosing a different pill

def switchTopicVideo(newTopic):
    if st.session_state.currentVideoTopic == newTopic:
        return
    if st.session_state.currentVideoTopic is not None:
        st.session_state.socket_video_sub.setsockopt_string(zmq.UNSUBSCRIBE, st.session_state.currentVideoTopic)
    st.session_state.socket_video_sub.setsockopt_string(zmq.SUBSCRIBE, newTopic)
    st.session_state.currentVideoTopic = newTopic

def switchTopicAudio(newTopic):
    if st.session_state.currentAudioTopic == newTopic:
        return
    if st.session_state.currentAudioTopic is not None:
        st.session_state.socket_audio_sub.setsockopt_string(zmq.UNSUBSCRIBE, st.session_state.currentAudioTopic)
    st.session_state.socket_audio_sub.setsockopt_string(zmq.SUBSCRIBE, newTopic)
    st.session_state.currentAudioTopic = newTopic
###########################################################################################
#IMPORTANT Displaying nothing when same pill gets pressed when already activated
def unsubscribeVideoTopic():
    if st.session_state.currentVideoTopic != None:
        st.session_state.socket_video_sub.setsockopt_string(zmq.UNSUBSCRIBE, st.session_state.currentVideoTopic)
        st.session_state.currentVideoTopic = None

def unsubscribeAudioTopic():
    if st.session_state.currentAudioTopic != None:
        st.session_state.socket_audio_sub.setsockopt_string(zmq.UNSUBSCRIBE, st.session_state.currentAudioTopic)
        st.session_state.currentAudioTopic = None    

###########################################################################################



def getMatNr():
    #TODO Use info from Group1 to get the actual MatNr
    return "123456789"

def main():
    start_streamlit()

if __name__ == "__main__":
    main()