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
    client_video = CLIENT.checkVideoDiffPerson_client("videoAnalysis")
    client_audio = CLIENT.checkAudioLoud_client("audioAnalysis")


    #Use package multiprocessing to run the run-method of each object in a different process
    #Like this, they can all run at the same time and asynchronous
    #target and args as arguments for Process()

    #target=x.run determines that in each process the run method of the object is executed after being started
    server_process = multiprocessing.Process(target=server.run)
    client_video_process = multiprocessing.Process(target=client_video.run)
    client_audio_process = multiprocessing.Process(target=client_audio.run)


    #Starting each process, so executing the run method of each object
    server_process.start()
    client_video_process.start()
    client_audio_process.start()

    #Starting streamlit as a program by using the package subprocess
    print("video client output port", client_video.portPUB)
    print("audio client output port", client_audio.portPUB)
    streamlit = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "src/secondApproach/start_streamlit.py"], stdout = sys.stdout, stderr = sys.stderr)
    
    
    print("main process id", os.getpid())
    print("Server Process id", server_process.pid)
    print("Client Video Process id", client_video_process.pid)
    print("Client Audio Process id", client_audio_process.pid)
    #print("Streamlit process id", subprocess.check_output(["pidof","streamlit"]))

    streamlit.wait()
if __name__ == "__main__":
    main()