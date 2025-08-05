# Peer-to-Peer-File-Sharing-System

A simple file sharing system based on BitTorrent Protocol, it allows users to share and download files in a decentralised way, both using TCP and UDP communication.

Classes

Tracker
  
- Allows seeeders to register with the tracker via UDP, also responsible for listening to incoming messages and processing them based on their message types.
- Tracker can handle multiple types of requests, including file requests from leechers and registration of seeders.
- Steps to Start the Tracker: 

 1. Open a terminal and navigate to the project directory. 

 2. Run the Tracker script: 

        python Tracker.py 

 3. The Tracker will now listen for Seeder and Leecher requests.

Seeder

- Seeder contains files that can be requested by leechers
- Seeder binds to an available port, allows parallel connections for leechers that want to download files, and share data to leechers.
- Steps to Start a Seeder: 

 1.Open a new terminal window. To run multiple seeders simultaneously, open as many terminal windows as the number of seeders you want to operate. 

 2.Navigate to the project directory. 

 3.Run the Seeder script  

    python Seeder.py 

 4.Enter the files you want to register. 

 5.The Seeder will register itself with the Tracker, send periodic heartbeats and start sharing file.

Leecher

- Leecher request for files and later transition to seeders when they have the full file.
- Leecher creates a USP connection with the tracker to obtain a list of seeders that have the file it wants, then later create a TCP connection with a seeder to request a file.
- If a leecher gets more than one seeder with a file it has requested, it distributes the data chunks among seeders.
- After successfully downloading the file, it transition to being  a seeder.
- Steps to Start a Leecher: 

 1. Open another terminal window. To run multiple leechers simultaneously, open as many terminal windows as the number of leechers you want to operate. 

 2. Navigate to the project directory. 

 3. Run the Leecher script 

        python Leecher.py 

 4. Enter the file name of the file to be requested from the Tracker and thereafter downloaded from seeders. 

 5. The Leecher will receive a list of active seeders from the Tracker and attempt to download the requested file.

Collaborators
- Sithokomele Nxumalo
- Athenkosi Miya
