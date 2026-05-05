import CLIENT
import start_streamlit
import SERVER

#main script to start the app
#Create the server and clients and run them by using the package multiprocessing
#Start streamlit in the background by using the package Subprocess to run a python script from within another python script

def main():
    server = SERVER.Server()
    

if __name__ == "__main__":
    main()