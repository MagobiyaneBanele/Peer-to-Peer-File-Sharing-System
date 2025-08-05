# Peer-to-Peer-File-Sharing-System

A simple file sharing system based on BitTorrent Protocol, it allows users to share and download files in a decentralised way, both using TCP and UDP communication.

Classes

Tracker
  
- Allows seeeders to register with the tracker via UDP, also responsible for listening to incoming messages and processing them based on their message types.
- Tracker can handle multiple types of requests, including file requests from leechers and registration of seeders.

Seeder

- Seeder contains files that can be requested by leechers
- Seeder binds to an available port, allows parallel connections for leechers that want to download files, and share data to leechers.

Leecher

- Leecher request for files and later transition to seeders when they have the full file.
- Leecher creates a USP connection with the tracker to obtain a list of seeders that have the file it wants, then later create a TCP connection with a seeder to request a file.
- If a leecher gets more than one seeder with a file it has requested, it distributes the data chunks among seeders.
- After successfully downloading the file, it transition to being  a seeder.

Collaborators
- Sithokomele Nxumalo
- Athenkosi Miya
