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
    client_rawVideo = CLIENT.checkVideoRaw_client()
    client_rawAudio = CLIENT.checkAudioRaw_client()
    #TODO add all the other clients

    #Use package multiprocessing to run the run-method of each object in a different process
    #Like this, they can all run at the same time and asynchronous
    #target and args as arguments for Process()

    #target=x.run determines that in each process the run method of the object is executed after being started
    #CREATE A PROCESS FOR THE SERVER AND EVERY SEPARATE CLIENT 
    server_process = multiprocessing.Process(target=server.run)
    client_rawVideo_process = multiprocessing.Process(target=client_rawVideo.run)
    client_rawAudio_process = multiprocessing.Process(target=client_rawAudio.run)


    #Starting each process, so executing the run method of each object
    server_process.start()
    client_rawVideo_process.start()
    client_rawAudio_process.start()

    #Starting streamlit as a program by using the package subprocess
    print("video client output port", client_rawVideo.portPUB)
    print("audio client output port", client_rawAudio.portPUB)
    streamlit = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "src/secondApproach/start_streamlit.py"], stdout = sys.stdout, stderr = sys.stderr)
    
    
    print("main process id", os.getpid())
    print("Server Process id", server_process.pid)
    print("Client Video Process id", client_rawVideo_process.pid)
    print("Client Audio Process id", client_rawAudio_process.pid)
    #print("Streamlit process id", subprocess.check_output(["pidof","streamlit"]))

    streamlit.wait()
if __name__ == "__main__":
    main()