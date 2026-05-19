import streamlit as st
import zmq
import numpy as np
import base64
import msgpack
import time

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

    socket_video_sub = st.session_state.socket_video_sub
    socket_audio_sub = st.session_state.socket_audio_sub
    poller = st.session_state.poller
###########################################################################################
    st.title("Remote exam surveillance")

    videoSelectionOptions = ["cameraFeed", "faceRecognition", "severalPeople", "deviceDetection", "cameraOff"]
    videoSelectionUser = st.pills("Video:", videoSelectionOptions,
                                   selection_mode="single",
                                   key="video_selection")   

    placeholder_video = st.empty()

    audioSelectionOptions = ["microphoneSignal", "volume", "whispering", "spokenWords", "microphoneOff"]
    audioSelectionUser = st.pills("Audio:", audioSelectionOptions,
                                   selection_mode="single",
                                   key="audio_selection")

    placeholder_audio = st.empty()
    placeholder_cheatedStatus = st.empty()
###########################################################################################
    match videoSelectionUser:
        case "cameraFeed": switch_topic_video("rawVideo")
        case "faceRecognition": switch_topic_video("diffPerson")
        case "severalPeople": switch_topic_video("sevPeople")
        case "deviceDetection": switch_topic_video("findDevice")
        case "cameraOff": switch_topic_video("cameraOff")

    match audioSelectionUser:
        case "microphoneSignal": switch_topic_audio("rawAudio")
        case "volume": switch_topic_audio("loud")
        case "whispering": switch_topic_audio("whisper")
        case "spokenWords": switch_topic_audio("getWords")
        case "microphoneOff": switch_topic_audio("microphoneOff")

###########################################################################################
    #st.fragment makes only this part rerun at rate of run_every
    @st.fragment(run_every=0.033)
    def streamVideo():
        pollerSockets = dict(poller.poll(timeout=16))

        if socket_video_sub in pollerSockets:
            topicReceived = socket_video_sub.recv_string()
            metaData = msgpack.unpackb(socket_video_sub.recv(), raw=False)
            videoBytes = socket_video_sub.recv()

            if topicReceived == "cheated":
                placeholder_cheatedStatus.warning(
                    f"CHEATING DETECTED: Type: {metaData[1]}, "
                    f"Time: {metaData[2]}, MatNr: {metaData[3]}, Infos: {metaData[4]}"
                )

            b64 = base64.b64encode(videoBytes).decode()
            placeholder_video.markdown(
                f'<img src="data:image/jpeg;base64,{b64}" style="width:100%">',
                unsafe_allow_html=True
            )

            currentTime = time.time()
            print("Streamlit hat", currentTime - st.session_state.lastTimeVideo, "s gebraucht")
            st.session_state.lastTimeVideo = currentTime

    @st.fragment(run_every=0.1)
    def streamAudio():
        pollerSockets = dict(poller.poll(timeout=16))
        if socket_audio_sub in pollerSockets:
            topicReceived = socket_audio_sub.recv_string()
            metaData = msgpack.unpackb(socket_audio_sub.recv(), raw=False)
            proofData = socket_audio_sub.recv()

            if topicReceived == "cheated":
                placeholder_cheatedStatus.warning(
                    f"CHEATING DETECTED: Type: {metaData[1]}, "
                    f"Time: {metaData[2]}, MatNr: {metaData[3]}, Infos: {metaData[4]}"
                )

            match topicReceived:
                case "rawAudio":
                    placeholder_audio.text(proofData)
                case "loud":
                    st.session_state.oldAudioInput = np.roll(st.session_state.oldAudioInput, -1)
                    st.session_state.oldAudioInput[-1] = metaData[4][0]
                    placeholder_audio.bar_chart(st.session_state.oldAudioInput)
                case "whisper" | "getWords" | "microphoneOff":
                    placeholder_audio.text(metaData[4][0])

    streamVideo()   #starting the fragment
    streamAudio()
###########################################################################################
def switch_topic_video(newTopic):
    if st.session_state.currentVideoTopic == newTopic:
        return
    if st.session_state.currentVideoTopic is not None:
        st.session_state.socket_video_sub.setsockopt_string(zmq.UNSUBSCRIBE, st.session_state.currentVideoTopic)
    st.session_state.socket_video_sub.setsockopt_string(zmq.SUBSCRIBE, newTopic)
    st.session_state.currentVideoTopic = newTopic

def switch_topic_audio(newTopic):
    if st.session_state.currentAudioTopic == newTopic:
        return
    if st.session_state.currentAudioTopic is not None:
        st.session_state.socket_audio_sub.setsockopt_string(zmq.UNSUBSCRIBE, st.session_state.currentAudioTopic)
    st.session_state.socket_audio_sub.setsockopt_string(zmq.SUBSCRIBE, newTopic)
    st.session_state.currentAudioTopic = newTopic
###########################################################################################

def sendCheatingToGoogleSheets(metaData):
    pass

def getMatNr():
    #TODO Use info from Group1 to get the actual MatNr
    return "123456789"

def main():
    start_streamlit()

if __name__ == "__main__":
    main()