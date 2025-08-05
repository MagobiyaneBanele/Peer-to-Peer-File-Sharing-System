'''Leecher Class 
This class gets list of seeders from the tracker that has the specific file it has requested and it creates connection with those seeders to download chunks and assemble the chunks to the file then the file is checked if it is the same as the original if it is the same it transition to a Seeder immediately.
'''

import socket
import threading # To handle multiple downloads simultaneously
import os
import Seeder
import hashlib
import time

# Set tracker parameters for the connection
ip_address = "127.0.0.1"  
port_number = 6000
format = 'utf-8'
chunk_storage = {}  # Dictionary to store downloaded chunks

leecherIP = "127.0.0.1"
leecherPortNum = 6010

trackerIP = "127.0.0.1"
trackerPortNum = 6000

CHUNK_SIZE = 1024  # Size of each chunk to download

''' 
Function to calculate SHA-256 hash of a file to ensure integrity after downloading.
This function reads the file in chunks and calculates the hash progressively.
'''
def get_file_hash(file_path):
    hash_sha256 = hashlib.sha256()  
    with open(file_path, 'rb') as file:  
        
        while chunk := file.read(8192):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()  

''' 
Function to get a list of seeders from the tracker and the total number of chunks for a file.
The tracker will provide a list of available seeders and the total number of chunks for the file.
'''
def get_seeders_and_chunks(file_name):
    
    # Send a request to the tracker to get a list of seeders and chunks and it's using UDP for communication
    
    leecherSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = f"REQUEST {file_name}"
    leecherSocket.sendto(message.encode(), (ip_address, port_number))
    print("Request list of seeders")
    
    # Receive the response from the tracker
    response, _ = leecherSocket.recvfrom(1024)
    data = response.decode().strip().split(" ")
    
    # Extracting all elements which is the list of seeders except the last one are seeders and the last item is total chunks
    
    seeders = data[:-1]  
    total_chunks = int(data[-1])  
    print(f"List of seeders received: {seeders}")
    print(f"Total chunks: {total_chunks}")
    
    leecherSocket.close()  
    return seeders, total_chunks

''' 
Function to download a specific chunk from a seeder.
Each chunk creates its own TCP connection with the seeder to download the data.
'''
def download_chunk(seeder_ip, seeder_port, file_name, chunk_id):
    try:
        seederSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        seederSocket.connect((seeder_ip, seeder_port))
        
        message = f"REQUEST {file_name} {chunk_id}"  
        seederSocket.send(message.encode(format)) 
        
        # Receive the chunk of data and write it on a chunk file and all downloaded files are added on chunk storage
        data = seederSocket.recv(5048)
        if data:
            chunk_filename = f"chunk_{chunk_id}"  
            with open(chunk_filename, 'wb') as chunk_file:  
                chunk_file.write(data)
            chunk_storage[chunk_id] = chunk_filename
            
        
        seederSocket.close()  

    except Exception as e:
        print(f"Failed to connect to {seeder_ip}:{seeder_port}")

''' 
Function to download the full file by fetching its chunks from different seeders.
This function uses the download_chunk method to retrieve the chunks concurrently.
'''
def download_file(file_name):
    seeders, total_chunks = get_seeders_and_chunks(file_name)  
    if not seeders:
        print("No seeders available")
        return
    
    threads = []  # List to hold the threads for downloading chunks

    # Create a dictionary to store chunks for each seeder
    seeder_chunks = {seeder: [] for seeder in seeders} 
    print(f"Assigning chunks to available seeders")
    
    # Distribute the chunks to seeders available using round-robin manner
    for chunk_id in range(total_chunks):
        assigned_seeder = seeders[chunk_id % len(seeders)]  
        seeder_chunks[assigned_seeder].append(chunk_id)
    
    ''' 
    Loop through seeders and start threads for downloading their assigned chunks.
    Each thread will call the download_chunk method for the specific chunk.
    '''
    for seeder, chunks in seeder_chunks.items():
        seeder_ip, seeder_port = seeder.split(',')  
        seeder_port = int(seeder_port)  
    
        ''' 
        Start threads for downloading chunks.
        Each chunk will be downloaded by a separate thread to speed up the process.
        '''    
        for chunk_id in chunks:
            thread = threading.Thread(target=download_chunk, args=(seeder_ip, seeder_port, file_name, chunk_id))
            thread.start()  
            threads.append(thread) 

    # Wait for all threads to finish
    for thread in threads:
        thread.join()
    
    # Combine all downloaded chunks into the final file
    new_file = "New_" + file_name 
    with open(f"{new_file}", 'wb') as final_file:
        for chunk_id in range(total_chunks):
            chunk_filename = f"chunk_{chunk_id}"
            if os.path.exists(chunk_filename):
                with open(chunk_filename, 'rb') as chunk_file:
                    final_file.write(chunk_file.read())
    # Clean up the downloaded chunk files 
    for chunk_id in range(total_chunks):
        chunk_filename = f"chunk_{chunk_id}"
        if os.path.exists(chunk_filename):
            os.remove(chunk_filename)   
    print(f"All chunks are downloaded")
    
    # Compare the hashes of the original and downloaded files to verify integrity
    original_file_hash = get_file_hash(file_name)
    downloaded_file_hash = get_file_hash(new_file)
    
    if original_file_hash == downloaded_file_hash:
        print(f"File download and reconstruction successful. Hashes match.")
        print(f" Transitioning to a Seeder...")
        
        # Call the Seeder to transition Leecher to Seeder after downloading
        Seeder.main()  
       
    else:
        print("Hashes do not match. File might be corrupted. Please re-download.")

''' 
Main function to start the download process and prompt the user to enter the filename.
The function repeatedly asks for the filename until a valid file is provided.
'''
def main():
    while True:
        try:
            file_name = input("Enter the filename: \n")
            if not os.path.exists(file_name):
                raise FileNotFoundError(f"The file '{file_name}' does not exist.")        
            download_file(file_name)  
            break
        except FileNotFoundError :
                print(f"File not found.")        

if __name__ == "__main__":
    main()
