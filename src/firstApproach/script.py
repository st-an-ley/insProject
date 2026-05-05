import subprocess
import sys


def main():
    #Using subprocess to run all the scripts asynchron (not waiting for the other to end)
    SERVER = subprocess.Popen([sys.executable, "src/firstApproach/SERVER.py"], stdout = sys.stdout, stderr = sys.stderr)
    CLIENT_STREAM = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "src/firstApproach/CLIENT_STREAM.py"], stdout = sys.stdout, stderr = sys.stderr)
    

    SERVER.wait()
    CLIENT_STREAM.wait()
if __name__ == "__main__":
    main()


    