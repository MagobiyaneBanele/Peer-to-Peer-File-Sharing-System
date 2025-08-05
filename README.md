<<<<<<< HEAD
SOCKET PROGRAMMING PROJECT : P2P FILE SHARING SYSTEM
=======
SOCKET PROGRAMMING: P2P FILE SHARING SYSTEM
>>>>>>> 77a75a66bd728338f7e62276a7b8e739b8c9489f

This project implements a simplified torrent-like file-sharing system that enables peer-to-peer (P2P) file distribution. It uses TCP for reliable data transfer and UDP for tracker communication and peer discovery. It includes:

This project develops a basic file-sharing system, similar to torrents, for peer-to-peer (P2P) file distribution. It relies on TCP to ensure reliable data transmission and utilizes UDP for tracker communication and discovering peers. It encompasses: 

 -Tracker: Registers and manages seeders and provides a list of available peers.  

 -Seeder: Shares files with leechers. 

 -Leecher: Downloads files from seeders.  

PREREQUISITES

Ensure the file downloaded by the leecher is stored in the same directory as all the source codes. Have the following installed: 

  -Python 3.x 

  -Required libraries: 

  -socket 

  -threading 

  -time  

  -os 

  -seeder ( Seeder module) 

  -hashlip 

  -PyQt5 

RUNNING A TRACKER

The Tracker monitors seeders by registering their information and receiving periodic heartbeats to notify the Tracker of their presence. Additionally, it handles requests and provides responses to leechers. 

Steps to Start the Tracker: 

 1. Open a terminal and navigate to the project directory. 

 2. Run the Tracker script: 

        python Tracker.py 

 3. The Tracker will now listen for Seeder and Leecher requests. 

RUNNING A SEEDER

A Seeder shares files with Leechers by registering itself with the Tracker. 

Steps to Start a Seeder: 

 1.Open a new terminal window. To run multiple seeders simultaneously, open as many terminal windows as the number of seeders you want to operate. 

 2.Navigate to the project directory. 

 3.Run the Seeder script  

    python Seeder.py 

 4.Enter the files you want to register. 

 5.The Seeder will register itself with the Tracker, send periodic heartbeats and start sharing file. 

RUNNING A LEECHER

A Leecher retrieves files by making requests to available Seeders. Once it successfully downloads the entire file, it transitions into a Seeder, registers its presence with the Tracker, and begins sending periodic heartbeats to indicate its availability. 

Steps to Start a Leecher: 

 1. Open another terminal window. To run multiple leechers simultaneously, open as many terminal windows as the number of leechers you want to operate. 

 2. Navigate to the project directory. 

 3. Run the Leecher script 

        python Leecher.py 

 4. Enter the file name of the file to be requested from the Tracker and thereafter downloaded from seeders. 

 5. The Leecher will receive a list of active seeders from the Tracker and attempt to download the requested file. 

TROUBLESHOOTING

1. Leecher cannot find any seeder 

   -Ensure that the seeder had registered with the Tracker and is sending periodic heartbeats. 

   -Check if the Tracker is running. 

   -Ensure that the file name entered is correct and in the correct form. 

 2. Connection refused or timeouts 

    -Ensure that the Tracker, Seeder and Leecher are running. 

    -Verify that the correct IP and Port numbers are used correctly. 

 
3. Seeder is not sharing files properly 

   -Ensure that the Seeder sent a heartbeat message to stay active. 

   -Check if the file exists in the Seeder’s directory. 

   -Ensure that a connection has been established between the Seeder and Leecher. 

 
 4. Multiple seeders conflicts 

   -Ensure each seeder instance is using a unique port number. 

   -Verify that seeders aren't trying to register the same files with different chunk calculations. 

 
5. Tracker not responding 

   -Confirm the tracker is running on the specified IP and port. 

   -Check if any firewall settings are blocking UDP communication. 

   -Restart the Tracker if it has been running for an extended period. 

 

Future Enhancements 

-Implement encryption for secure file transfers. 

-Improve error handling for failed connections. 

-Add bandwidth management to balance internet usage. 

 

