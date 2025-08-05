import socket
import threading
import os
import time


#Tracker details and the format used
trackerIP = "127.0.0.1"
trackerPortNum = 6000
format = 'utf-8'

def handlingClient(connectionSock, addr):
    """
    handles requests from leechers:
     -receives file request
     -fetches the requested file chunk
     -sends the requested chunk back to the leecher
    """
    try:
        print(f"[CONNECTED] {addr} is connected! :)")

        #receive file request from the leecher
        fileRequest = connectionSock.recv(3000).decode(format)

        if fileRequest.startswith("REQUEST"):
            data = fileRequest.split(" ")   #parse request details
            print(f"Leecher {addr} requested the file {data[1]}")
            file_name = data[1]
            chunk_id = int(data[2])  #the chunk/part being requested

            #now open the file and read the requested chunk
            with open(file_name, "rb") as f:
                chunk_size = 1024   #each chunk == 1024 bytes
                f.seek(chunk_id * chunk_size)   #move to the requested chunk position
                chunk_data = f.read(chunk_size)

            #send the chunk to the requesting leecher
            connectionSock.send(chunk_data)
            print(connectionSock.recv(1024).decode(format))
            print(f"{data[1]} is sent to {addr}")

    except Exception as e:
        print(f"Error {e}")

    finally:
        connectionSock.close()  #close the connection with leecher


def start(seederIP, seederPort):
    """
    starts the seeder, allowing incoming connections from leechers
    """
    seederSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    seederSock.bind((seederIP, seederPort))
    #print(seederPort)

    seederSock.listen(10)   #allows up to 10 simultaneous connections
    print(f"[LISTENING] the Seeder is listening on {seederPort}")

    while True:
        connectionSock, addr = seederSock.accept()
        thread = threading.Thread(target=handlingClient, args=(connectionSock, addr))
        thread.start()      #each leecher==thread requesting is handled in a separate thread

def register(trackerSock, trackerAddr, seederIP, seederPort):
    """
    seeder registers with the tracker, and informs it of available files
    """
    try:
        fileStr = fileAvailable()
        if not fileStr:
            return False    #no files available, so won't register

        print(f"Sending Register message to Tracker at {trackerAddr} : {trackerIP}")

        message = f"REGISTER_FILES {seederIP} {seederPort} {fileStr}"
        trackerSock.sendto(message.encode(format), trackerAddr)

        #registration confirmation from the tracker
        data, addr = trackerSock.recvfrom(1024)
        print(f"[TRACKER RESPONSE]: {data.decode(format)}")
        return True

    except ConnectionResetError:
        print("Error: The tracker is not responding. Make sure it's running.")
        return False

    except Exception as e:
        print(f"An error occurred {e}")
        return False


def fileAvailable():
    """
    prompt the user for files to register and checks their availability
    return a formatted string containing file names and their sizes
    """
    fileToReg = input("[ENTER] file(s) you want to register(separated by a comma):\n")
    fileToReg = fileToReg.split(",")

    counter = 0
    fileArray = []
    for file in fileToReg:
        # Verify if the file exists
        if os.path.exists(file):
            fileSize = os.path.getsize(file)
            fileArray.append(f"{file}:{fileSize}")  #stores file name and size
        else:
            print(f"[WARNING]: File {file} does not exist and will not be registered")

    if not fileArray:
        print("[ERROR]: No files available to share!")
        return ""

    fileStr = (",").join(fileArray)
    print(fileStr)
    return fileStr

def discoverable(trackerSock, trackerAddr, seederIP, seederPort):
    """
    sends periodic heartbeats to the tracker to indicate that the seeder is online
    """
    try:
        while True:
            trackerSock.sendto(f"HEARTBEAT {seederIP} {seederPort}".encode(), trackerAddr)
            data, addr = trackerSock.recvfrom(1024)
            print("[TRACKER RESPONSE]: ", data.decode(format))
            time.sleep(30)      #waits for 30sec before sending another hearthbeat

    except Exception as e:
        print(f"An error occurred {e}")

    finally:
        trackerSock.close()  #close socket when stopping heartbeats

def main():
    """
    initialises the seeder, registers it with the tracker, and starts listening for requests.
    """
    #creates a TCP socket for seeder, to get the IP address and port number
    seederSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    seederSock.bind(('0.0.0.0', 0)) #binds to available port
    seederIP = socket.gethostbyname(socket.gethostname())  #getS local IP
    seederPort = seederSock.getsockname()[1]   #gets assigned port by os

    #print(f"Seeder is:{seederIP}:{seederPort}")

    #creates UDP socket to communicate with the tracker
    trackerSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # created the UDP connection
    trackerAddr = (trackerIP, trackerPortNum)

    #attempts to register with the tracker
    if register(trackerSock, trackerAddr, seederIP, seederPort):
        # Start heartbeat thread
        time.sleep(5)
        heartBeatThread = threading.Thread(target=discoverable, args=(trackerSock, trackerAddr, seederIP, seederPort), daemon=True)
        heartBeatThread.start()

        print("[STARTING] the Seeder is starting....")
        start(seederIP, seederPort)

    else:
        print("[REGISTRATION FAILED]: Seeder will not start.")
        trackerSock.close()

if __name__ == "__main__":
    main()