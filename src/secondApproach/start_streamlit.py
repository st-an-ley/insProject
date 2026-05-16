import streamlit as st
import zmq
import sys
import numpy as np
import cv2
import time
import base64

#Use the package subprocess to start streamlit in the background and receive data from the clients

def start_streamlit():
    #Arguments given when calling "streamlit run start_streamlit.py x y " in script.py
    videoInputPort = sys.argv[1]
    audioInputPort = sys.argv[2]

    context = zmq.Context()



    #SUBSCRIBER socket for video with corresponding port
    socket_video_sub = context.socket(zmq.SUB)
    socket_video_sub.setsockopt(zmq.RCVHWM, 1)        
    socket_video_sub.connect(f"tcp://localhost:{videoInputPort}")
    socket_video_sub.setsockopt(zmq.SUBSCRIBE, b'')

    #SUBSCRIBER socket for audio with corresponding port
    socket_audio_sub = context.socket(zmq.SUB)
    socket_audio_sub.connect(f"tcp://localhost:{audioInputPort}")
    socket_audio_sub.setsockopt(zmq.SUBSCRIBE, b'')

    poller = zmq.Poller()
    poller.register(socket_video_sub, zmq.POLLIN)
    poller.register(socket_audio_sub, zmq.POLLIN)

    st.title("Remote exam surveillance")
    placeholder_video = st.empty()
    placeholder_audio = st.empty()
    oldAudioInput = np.zeros(100)

    lastTime = time.time()
    while True:
        #topic = socket_video_sub.recv_string()
        pollerSockets = dict(poller.poll(timeout=16))
        if socket_video_sub in pollerSockets:
            videoDataInputBytes = socket_video_sub.recv()


            #videoDataInputNumpyArray = cv2.imdecode(np.frombuffer(videoDataInputBytes, np.uint8), cv2.IMREAD_COLOR)
            #placeholder_video.image(videoDataInputNumpyArray, channels="BGR")

            #Using base64 and markdown to avoid reloading the whole website when displaying a new image
            #base64 can only display 64 signs: A-Z, a-z, 0-9, +, /
            #Browsers/HTML can convert base64 back to bytes and display the image
            b64 = base64.b64encode(videoDataInputBytes).decode()
            placeholder_video.markdown(
                f'<img src="data:image/jpeg;base64,{b64}" style="width:100%">',
                unsafe_allow_html=True
            )

            currentTime = time.time()
            timePassed = currentTime-lastTime
            print("Streamlit hat ", timePassed, "gebraucht")
            lastTime = currentTime

        if socket_audio_sub in pollerSockets:
            #videoData = socket_video_sub.recv_pyobj()
            audioData = socket_audio_sub.recv()

            #print(videoData)

            audioNpArray = np.frombuffer(audioData, dtype=np.int16).astype(np.float32)

            audioMeanAbs = float(np.mean(np.abs(audioNpArray)))
            oldAudioInput = np.roll(oldAudioInput, -1)
            oldAudioInput[-1] = audioMeanAbs
            placeholder_audio.line_chart(oldAudioInput)
            pass
        #TODO find a better way to display audio

def main():
    start_streamlit()

if __name__ == "__main__":
    main()
