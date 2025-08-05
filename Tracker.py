# This is the code for the Tracker. The Tracker will use a Client/Server socket interaction with the Seeder and Leecher via UDP.
import socket
import time
import threading

# Define the Trackers' IP and Ports
tracker_IP = "127.0.0.1"  # Use actual IP, not "127.0.0.1" if running on different laptops
tracker_port = 6000  # Port for Tracker

# Create separate UDP sockets for leechers and seeders
tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind sockets to respective ports
tracker_socket.bind((tracker_IP, tracker_port))

# Set sockets to non-blocking mode
tracker_socket.setblocking(False)

print("The server is ready to receive and is listening on " + tracker_IP)

seeders = {}

# Dictionary to store Leecher information
leechers = {}

# Counters for generating IDs
next_seeder_id = 1
next_file_id = 1
next_leecher_id = 1

# Define a timeout (how long to wait before removing inactive seeders)
SEEDER_TIMEOUT = 45  # 45 seconds


def leecher_msg(message, clientAddress):
    global next_leecher_id
    # Decode the message
    IP_address, Port = clientAddress  # Extract IP and Port
    message_str = message.decode()  # Decode from bytes to string

    # Expected format: REQUEST filename
    parts = message_str.split()  # Split into two parts
    if len(parts) >= 2 and parts[0] == "REQUEST":
        file_name = parts[1]  # Extract the filename

        # Only generate a new leecher_id if the request is valid
        leecher_id = f"L{next_leecher_id}"
        next_leecher_id += 1  # Increment only when a valid request is received

    if leecher_id not in leechers:
        # Add the leecher to the dictionary
        leechers[leecher_id] = {
            "Leecher_IP": clientAddress[0],  # Leecher's IP Address
            "Leecher_Port": clientAddress[1],  # Leecher's Port
            "RequestedFile": file_name  # The file the leecher wants to download
        }
    else:
        # Update the existing leecher information
        leechers[leecher_id]["RequestedFile"] = file_name

    # Find seeders who have the requested file
    available_seeders = []
    total_chunks = None  # Store total chunks separately
    for seeder_id, seeder_info in seeders.items():  # Iterating over seeders
        for file_id, file_info in seeder_info["Files"].items():  # Iterating over the seeder's files
            if file_info["FileName"] == file_name:  # Match filename
                total_chunks = file_info["TotalChunks"]
                available_seeders.append(f"{seeder_info['IP']},{seeder_info['Port']}")

    if total_chunks is not None:
        available_seeders.append(str(total_chunks))  # Append total chunks at the end

    # Log the update
    print(f"Leecher {leecher_id} at {clientAddress} requested file: {file_name}")

    # Return response in the format: PEERS seeder1,ip,port seeder2,ip,port
    if available_seeders:
        return f"{' '.join(available_seeders)}".encode()
    else:
        return f"No Seeders with the specified file {file_name}.".encode()


# Method to handle the seeder message
def seeder_msg(message, clientAddress):
    global next_seeder_id, next_file_id
    # Decode the message
    #IP_address, Port = clientAddress  # Extract IP and Port
    message_str = message.decode()  # Decode from bytes to string

    parts = message_str.split()
    IP_address = parts[1]
    Port = parts[2]
    # Expected format: REGISTER_FILES IP Port filename:filesize,filename:filesize
    #                  REGISTER_FILEs 127.0.0.1 6000 dataFile.txt:2049,Bfile.txt:906,Afile.txt:1303
    if len(parts) >= 4 and parts[0] == "REGISTER_FILES":
        available_files_size = parts[3].split(',')

        # Separate filenames and sizes into two lists
        available_files = []
        available_sizes = []

        for item in available_files_size:
            filename, filesize = item.split(':')  # Split each pair by ':'
            available_files.append(filename)
            available_sizes.append(filesize)

        seeder_id = f"S{next_seeder_id}"
        next_seeder_id += 1

        # Register a file that does not exist in the seeders dictionary
        if seeder_id not in seeders:
            seeders[seeder_id] = {
                "IP": IP_address,
                "Port": Port,
                "Files": {}
            }

        chunk_size = 1024  # 1 chunk = 1024 bytes

        for file_info, file_size in zip(available_files, available_sizes):
            current_time = int(time.time())  # Unix timestamp
            file_id = f"F{next_file_id}"
            next_file_id += 1
            # Adding the file to seeder
            
            if int(file_size) < chunk_size:
                seeders[seeder_id]["Files"][file_id] = {
                    "FileName": file_info,
                    "FileSize": file_size,
                    "TotalChunks": 1,
                    "LastSeen": current_time
                }
                
            if int(file_size) % chunk_size == 0:
                seeders[seeder_id]["Files"][file_id] = {
                    "FileName": file_info,
                    "FileSize": file_size,
                    "TotalChunks": int(file_size) // chunk_size,
                    "LastSeen": current_time
                }
            else:
                seeders[seeder_id]["Files"][file_id] = {
                    "FileName": file_info,
                    "FileSize": file_size,
                    "TotalChunks": int(file_size) // chunk_size + 1,
                    "LastSeen": current_time
                }

        # Log the update
        print(f"Registered new seeder as {seeder_id} at {clientAddress}")
        print(f"Files available from {seeder_id}: {available_files}")

        # Return the assigned seeder ID to the client
        return f"REGISTERED {seeder_id} : {clientAddress}".encode()

    # Heartbeat message to update the LastSeen field periodically to track active seeders
    # Expected format: HEARTBEAT IP Port
    elif len(parts) == 3 and parts[0] == "HEARTBEAT":
        seeder_id = None
        for sid, data in seeders.items():
            if data["IP"] == IP_address and data["Port"] == Port:
                seeder_id = sid
                break

        if seeder_id:
            # Update the LastSeen timestamp
            current_time = int(time.time())  # Unix timestamp
            # Update LastSeen for all files of this seeder
            for file_id in seeders[seeder_id]["Files"]:
                seeders[seeder_id]["Files"][file_id]["LastSeen"] = current_time

            print(f"Heartbeat received from {seeder_id} at {clientAddress} and Processed!")
            # Return acknowledgment message
            return f"HEARTBEAT RECEIVED {seeder_id} : {clientAddress}".encode()
        else:
            print(f"Heartbeat received from unregistered seeder at {clientAddress}")
            return "ERROR: Seeder not registered.".encode()

    # Handle unknown message types
    else:
        print(f"Unknown message type received: {message_str}")
        return "ERROR: Invalid message format.".encode()


def remove_inactive_seeders():
    while True:
        current_time = int(time.time())  # Get current Unix timestamp
        inactive_seeders = []

        # Identify inactive seeders
        for seeder_id, seeder_info in list(seeders.items()):
            # Skip the hardcoded seeder S1 if you want to keep it
            if seeder_id == "S1":
                continue

            for file_id, file_info in list(seeder_info["Files"].items()):
                if current_time - file_info["LastSeen"] > SEEDER_TIMEOUT:
                    inactive_seeders.append(seeder_id)
                    break  # No need to check more files, mark seeder for removal

        # Remove inactive seeders
        for seeder_id in inactive_seeders:
            print(f"Removing inactive seeder: {seeder_id}... ")
            del seeders[seeder_id]

        time.sleep(10)  # Run check every 10 seconds


# Start the background thread for removing inactive seeders
threading.Thread(target=remove_inactive_seeders, daemon=True).start()

# Main loop to receive messages
while True:
    try:
        # Receive a message (could be from seeder or leecher)
        message, clientAddress = tracker_socket.recvfrom(2048)

        # Decode the message to determine its type
        message_str = message.decode()
        parts = message_str.split()

        # Process based on message type
        if parts and parts[0] == "REQUEST":
            print(f"Received request from leecher at {clientAddress}")
            response = leecher_msg(message, clientAddress)
        elif parts and (parts[0] == "REGISTER_FILES" or parts[0] == "HEARTBEAT"):
            print(f"Received request from seeder at {clientAddress}")
            response = seeder_msg(message, clientAddress)
        else:
            print(f"Received unknown message type: {message_str}")
            response = "ERROR: Unknown message type".encode()

        # Send the response
        tracker_socket.sendto(response, clientAddress)

    except BlockingIOError:
        # No message available from any client
        pass
    except Exception as e:
        print(f"Error in main loop: {e}")