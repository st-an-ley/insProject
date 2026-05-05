import zmq
from PIL import Image
import streamlit as st


def start_client_audio():
    
    context = zmq.Context()
    socket_sub = context.socket(zmq.SUB)
    socket_sub.connect("tcp://localhost:5556")
    socket_sub.setsockopt(zmq.SUBSCRIBE, b'videoInput')

    st.title("Remote exam surveillance")
    placeholder = st.empty()

    while True:
        topic = socket_sub.recv_string()
        frameData = socket_sub.recv_pyobj()
        placeholder.image(frameData, channels="BGR")

def main():
    start_client_audio()


if __name__ == "__main__":
    main()