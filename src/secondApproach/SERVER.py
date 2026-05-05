from time import sleep
import zmq
import cv2
import pyaudio
import wave


class Server:
    def __init__():
        # Server which captures the data and sends it to clients who request it


        chunk = 2048  # Record in chunks of 1024 samples
        sample_format = pyaudio.paInt32  # 16 bits per sample
        channels = 2
        fs = 44100  # Record at 44100 samples per second
        seconds = 3
        filename = "output.wav"



        
        context = zmq.Context()

        socket_pub_video = context.socket(zmq.PUB)
        socket_pub_video.bind("tcp://*:5555")
        camera = cv2.VideoCapture(0)

        socket_pub_audio = context.socket(zmq.PUB)
        socket_pub_audio.bind("tcp://*:5556")
        audio = pyaudio.PyAudio()

        stream = audio.open(format=sample_format,
                        channels=channels,
                        rate=fs,
                        frames_per_buffer=chunk,
                        input=True)


        topic_video = "videoInput"
        topic_audio = "audioInput"



        i = 0
        while True:
            #Read status and data from camera
            active, frameData = camera.read()
            audioInput = stream.read(chunk)


            #Display camera input with opencv
            cv2.imshow("CameraInput", frameData)
            #Check for keyboard input 'q' = 113 in ASCII
            if cv2.waitKey(1) == 113:
                break


            #Publishing the data over a specified topic to all the clients
            #Name of Topic is the first bytes of the message
            #zmq.SNDMORE signals that more data will come (and not only the name of the topic)
            socket_pub_video.send_string(topic_video, zmq.SNDMORE)
            socket_pub_video.send_pyobj(frameData)
            print(f"Sent frame {i}")

            socket_pub_audio.send_string(topic_audio, zmq.SNDMORE)
            socket_pub_audio.send_pyobj(audioInput)
            print(f"Sent audio data {i}")
            print(audioInput)

            i=i+1

        camera.release()
        cv2.destroyAllWindows()

