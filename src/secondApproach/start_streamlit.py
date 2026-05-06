import streamlit as st
import zmq
import sys
import numpy as np

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
    #empty: This part of streamlit is allowed to change during runtime
    placeholder_video = st.empty()
    placeholder_audio = st.empty()

    #Poller watches all sockets assigned to him for new incoming data
    poller = zmq.Poller()
    poller.register(socket_video_sub, zmq.POLLIN)
    poller.register(socket_audio_sub, zmq.POLLIN)

    #storing the last 100 values
    oldAudioInput = np.zeros(100)
    while True:

        #topic = socket_video_sub.recv_string()
        
        events = dict(poller.poll())

        if socket_video_sub in events:
            videoData = socket_video_sub.recv_pyobj()
            placeholder_video.image(videoData, channels="BGR")

        if socket_audio_sub in events:
            audioData = socket_audio_sub.recv_pyobj()

            audioDataNumpyArray = np.frombuffer(audioData, dtype=np.int16).astype(np.float32)

            #mean of abs because mean of normal values would be close to 0
            audioDataMean = float(np.mean(np.abs(audioDataNumpyArray)))

            #Shifting all values in the numpy array one place to the left to add the new value at the end
            oldAudioInput = np.roll(oldAudioInput, -1)

            #Changing the last value to the calculated mean value of the data coming in with the last chunk
            oldAudioInput[-1] = audioDataMean 

            placeholder_audio.line_chart(oldAudioInput)

    





        #TODO find a way to display audio

def main():
    start_streamlit()

if __name__ == "__main__":
    main()
