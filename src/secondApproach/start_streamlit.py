import streamlit as st
import zmq
import sys
import numpy as np
import cv2

#Use the package subprocess to start streamlit in the background and receive data from the clients

def start_streamlit():
    #Arguments given when calling "streamlit run start_streamlit.py x y " in script.py
    videoInputPort = sys.argv[1]
    audioInputPort = sys.argv[2]

    context = zmq.Context()

    #SUBSCRIBER socket for video with corresponding port
    socket_video_sub = context.socket(zmq.SUB)
    socket_video_sub.connect(f"tcp://localhost:{videoInputPort}")
    socket_video_sub.setsockopt(zmq.SUBSCRIBE, b'')

    #SUBSCRIBER socket for audio with corresponding port
    socket_audio_sub = context.socket(zmq.SUB)
    socket_audio_sub.connect(f"tcp://localhost:{audioInputPort}")
    socket_audio_sub.setsockopt(zmq.SUBSCRIBE, b'')

    st.title("Remote exam surveillance")
    placeholder_video = st.empty()
    placeholder_audio = st.empty()
    oldAudioInput = np.zeros(100)
    while True:
        #topic = socket_video_sub.recv_string()

        videoDataInputBytes = socket_video_sub.recv()
        videoDataInputNumpyArray = cv2.imdecode(np.frombuffer(videoDataInputBytes, np.uint8), cv2.IMREAD_COLOR)

        #videoData = socket_video_sub.recv_pyobj()
        audioData = socket_audio_sub.recv_pyobj()

        #print(videoData)
        placeholder_video.image(videoDataInputNumpyArray, channels="BGR")

        audioNpArray = np.frombuffer(audioData, dtype=np.int16).astype(np.float32)

        audioMeanAbs = float(np.mean(np.abs(audioNpArray)))
        oldAudioInput = np.roll(oldAudioInput, -1)
        oldAudioInput[-1] = audioMeanAbs
        placeholder_audio.line_chart(oldAudioInput)

        #TODO find a better way to display audio

def main():
    start_streamlit()

if __name__ == "__main__":
    main()
