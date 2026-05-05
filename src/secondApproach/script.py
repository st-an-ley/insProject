import start_streamlit
import CLIENT
import SERVER
import subprocess
import sys


#main script to start the app
#Create the server and clients and run them by using the package multiprocessing
#Start streamlit in the background by using the package Subprocess to run a python script from within another python script

def main():
    #server = SERVER.Server()
    #videoCheatingClient = CLIENT.checkAudioFeedCheating_client()
    #audioCheatingClient = CLIENT.checkAudioFeedCheating_client()

    streamlit = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "src/secondApproach/start_streamlit.py", "5555", "5556"], stdout = sys.stdout, stderr = sys.stderr)

    streamlit.wait()
if __name__ == "__main__":
    main()