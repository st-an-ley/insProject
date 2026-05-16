import streamlit as st
import zmq
import sys
import numpy as np
import cv2
import time
import base64
import struct

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
    placeholder_cheatedStatus = st.empty()
    oldAudioInput = np.zeros(100)

    lastTime = time.time()
    activated = False
    while True:
        #topic = socket_video_sub.recv_string()
        pollerSockets = dict(poller.poll(timeout=16))
        if socket_video_sub in pollerSockets:
            videoDataInputBytes = socket_video_sub.recv()


            #videoDataInputNumpyArray = cv2.imdecode(np.frombuffer(videoDataInputBytes, np.uint8), cv2.IMREAD_COLOR)
            #placeholder_video.image(videoDataInputNumpyArray, channels="BGR")

            #base64 can only display 64 signs: A-Z, a-z, 0-9, +, /
            #Browsers/HTML can convert base64 back to bytes and display the image; No need to convert bytes to numpyArray
            b64 = base64.b64encode(videoDataInputBytes).decode()
            #Use of markdown avoids creation of react component
            placeholder_video.markdown(
                f'<img src="data:image/jpeg;base64,{b64}" style="width:100%">',
                unsafe_allow_html=True
            )

            currentTime = time.time()
            timePassed = currentTime-lastTime
            print("Streamlit hat ", timePassed, "gebraucht")
            lastTime = currentTime

        if socket_audio_sub in pollerSockets:
            #Audio data is of type int16 and represents the position of the membran of the microphone
            #Every value is represented as 16 bits = 2 Bytes
            #16 bits : 65536 values from -32768 to +32767 


            #READ DATA AND SEPARATE IT INTO AUDIO AND CHEATING DATA
            #-------------------------------------------------
            audioDataBytes = socket_audio_sub.recv()
            audioDatadB, audioCheated= struct.unpack('f?', audioDataBytes)
            #-------------------------------------------------


            # CHECK ALL POSSIBLE REASONS WHICH CAN ACTIVATE THE CHEATING
            #-------------------------------------------------
            #CHECKING FOR BREACH OF THRESHOLD 
            if audioCheated == True: #TODO Add further reasons
                activated = True
            #-------------------------------------------------


            # UPDATE THE BAR-CHART BY SHIFTING EVERY VALUE BY ONE TO THE LEFT AND 
            # UPDATING THE LAST VALUE IN THE NUMPY ARRAY 
            #-------------------------------------------------
            oldAudioInput = np.roll(oldAudioInput, -1)
            oldAudioInput[-1] = audioDatadB
            placeholder_audio.bar_chart(oldAudioInput)
            #-------------------------------------------------


            #SEE FINAL RESULT OF ALL FORMER CHECKS AND UPDATE PLACEHOLDER ELEMENT
            #-------------------------------------------------
            if activated == False:
                placeholder_cheatedStatus.success("No cheating detected")
            elif activated == True:
                placeholder_cheatedStatus.warning("Cheating detected, supervisor was informed")
            #-------------------------------------------------
            
        

def main():
    start_streamlit()

if __name__ == "__main__":
    main()
