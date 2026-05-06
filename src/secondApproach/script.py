import start_streamlit
import CLIENT
import SERVER
import subprocess
import sys
import multiprocessing
import os 


#main script to start the app
#Create the server and clients and run them by using the package multiprocessing
#Start streamlit in the background by using the package Subprocess to run a python script from within another python script

def main():

    #Create the Objects which will send and receive data
    server= SERVER.Server()
    client_video = CLIENT.checkVideoFeedCheating_client()
    client_audio = CLIENT.checkAudioFeedCheating_client()


    #Use package multiprocessing to run the run-method of each object in a different process
    #Like this, they can all run at the same time and asynchronous
    #target and args as arguments for Process()
    server_process = multiprocessing.Process(target=server.run)
    client_video_process = multiprocessing.Process(target=client_video.run)
    client_audio_process = multiprocessing.Process(target=client_audio.run)


    #Starting each process
    server_process.start()
    client_video_process.start()
    client_audio_process.start()


    streamlit = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "src/secondApproach/start_streamlit.py", "5555", "5556"], stdout = sys.stdout, stderr = sys.stderr)
    print("main process id", os.getpid())
    print("Server Process id", server_process.pid)
    print("Server Process id", server_process.pid)
    print("Server Process id", server_process.pid)
    
    streamlit.wait()
if __name__ == "__main__":
    main()