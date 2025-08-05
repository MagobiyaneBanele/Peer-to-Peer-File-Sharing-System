'''
This is the P2P2 GUI class, built with PyQt5, which combines the tracker, seeder, and downloader functionalities into a unified peer-to-peer file-sharing system.
We created a separate file to accommodate the use of threads in the GUI, while integrating all classes and adding PyQt5 features for a complete graphical interface.
The classes are exactly the same as the original classes. 
'''


import sys
import socket
import threading
import os
import hashlib
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLineEdit, QLabel
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QFont

# Global variables
ip_address = "127.0.0.1"
port_number = 6000
format = 'utf-8'
chunk_storage = {}
leecherIP = "127.0.0.1"
leecherPortNum = 6010
trackerIP = "127.0.0.1"
trackerPortNum = 6000
CHUNK_SIZE = 1024
filesPresent = {"dataFile.pdf", "Afile.txt", "Bfile.txt", "Computer_Networks.pdf"}

tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tracker_socket.bind((trackerIP, trackerPortNum))
tracker_socket.setblocking(False)

seeders = {}
leechers = {}
next_seeder_id = 1
next_file_id = 1
next_leecher_id = 1
SEEDER_TIMEOUT = 45

def get_file_hash(file_path):
    hash_sha256 = hashlib.sha256()
    with open(file_path, 'rb') as file:
        while chunk := file.read(8192):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()
# This class works the same as the Leecher class, and this class handles the downloading of files in a separate thread
class DownloadThread(QThread):
    update_signal = pyqtSignal(str)

    def __init__(self, file_name, leecherIP, leecherPortNum, seeder_tab):
        super().__init__()
        self.file_name = file_name
        self.leecherIP = leecherIP
        self.leecherPortNum = leecherPortNum
        self.seeder_tab = seeder_tab  

    def run(self):
        try:
            seeders, total_chunks = self.get_seeders_and_chunks(self.file_name)
            if not seeders:
                self.update_signal.emit("No seeders available")
                return
            
            threads = []
            seeder_chunks = {seeder: [] for seeder in seeders}
            for chunk_id in range(total_chunks):
                assigned_seeder = seeders[chunk_id % len(seeders)]
                seeder_chunks[assigned_seeder].append(chunk_id)

            # Start download threads
            for seeder, chunks in seeder_chunks.items():
                seeder_ip, seeder_port = seeder.split(',')
                seeder_port = int(seeder_port)
                for chunk_id in chunks:
                    thread = threading.Thread(target=self.download_chunk, args=(seeder_ip, seeder_port, self.file_name, chunk_id))
                    thread.start()
                    threads.append(thread)

            # Wait for all downloads to complete
            for thread in threads:
                thread.join()

            self.finalize_download(total_chunks)
        except Exception as e:
            self.update_signal.emit(f"Error in download thread: {str(e)}")

    def get_seeders_and_chunks(self, file_name):
        try:
            leecherSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message = f"REQUEST {file_name}"
            leecherSocket.sendto(message.encode(), (ip_address, port_number))
            self.update_signal.emit("Request list of seeders")

            response, _ = leecherSocket.recvfrom(1024)
            data = response.decode().strip().split(" ")
            seeders = data[:-1]
            total_chunks = int(data[-1])
            
            self.update_signal.emit(f"List of seeders received: {seeders}")
            self.update_signal.emit(f"Total chunks: {total_chunks}")
            leecherSocket.close()
            return seeders, total_chunks
        except Exception as e:
            self.update_signal.emit(f"Error getting seeders: {str(e)}")
            return [], 0

    def download_chunk(self, seeder_ip, seeder_port, file_name, chunk_id):
        try:
            seederSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            seederSocket.connect((seeder_ip, seeder_port))
            
            message = f"REQUEST {file_name} {chunk_id}"
            seederSocket.send(message.encode('utf-8'))
            
            data = seederSocket.recv(5048)
            if data:
                chunk_filename = f"chunk_{chunk_id}"
                with open(chunk_filename, 'wb') as chunk_file:
                    chunk_file.write(data)
                chunk_storage[chunk_id] = chunk_filename
            
            seederSocket.close()
        except Exception as e:
            self.update_signal.emit(f"Failed to download chunk {chunk_id} from {seeder_ip}:{seeder_port}: {str(e)}")

    def finalize_download(self, total_chunks):
        new_file = "New_" + self.file_name
        try:
            # Reconstruct the file
            with open(new_file, 'wb') as final_file:
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
            self.update_signal.emit(f"All chunks are downloaded")            

            # Hash comparison and seeding
            if os.path.exists(self.file_name):  # If original file exists locally
                original_file_hash = self.get_file_hash(self.file_name)
                downloaded_file_hash = self.get_file_hash(new_file)
                if original_file_hash and downloaded_file_hash and original_file_hash == downloaded_file_hash:
                    self.update_signal.emit(f"File download and reconstruction successful. Hashes match.")
                    self.update_signal.emit(f" Transitioning to a Seeder...")                    

                    self.start_seeding()
                else:
                    self.update_signal.emit("Hashes do not match or error occurred. File might be corrupted.")
            else:
                self.update_signal.emit("No original file for hash comparison. Assuming download success.")
                self.start_seeding()

            # Clean up chunk files
            for chunk_id in range(total_chunks):
                chunk_filename = f"chunk_{chunk_id}"
                if os.path.exists(chunk_filename):
                    os.remove(chunk_filename)

        except Exception as e:
            self.update_signal.emit(f"Error in finalize_download: {str(e)}")
            if os.path.exists(new_file):
                os.remove(new_file)

    def get_file_hash(self, file_path):
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as file:
                while chunk := file.read(8192):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.update_signal.emit(f"Error calculating hash for {file_path}: {str(e)}")
            return None

    def start_seeding(self):
        try:
            filesPresent.add(self.file_name)
            self.update_signal.emit(f"Starting seeder for {self.file_name}")
            # Run seeder in a new thread
            seeder_thread = threading.Thread(target=self.seeder_tab.start_seeder_operations)
            seeder_thread.daemon = True  # Make it a daemon thread to avoid blocking shutdown
            seeder_thread.start()
        except Exception as e:
            self.update_signal.emit(f"Error starting seeder: {str(e)}")


# TrackerTab works the same as the Tracker class handles the communication between the tracker and the leechers/seeders
class TrackerTab(QWidget):
    update_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.update_signal.connect(self.append_message)

    def init_ui(self):
        layout = QVBoxLayout()
        self.status_label = QLabel('🌟 Tracker Status 🌟')
        self.status_label.setFont(QFont("Comic Sans MS", 12))
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.start_button = QPushButton('Start Tracker ✨')
        self.start_button.clicked.connect(self.start_tracker)
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.text_area)
        layout.addWidget(self.start_button)
        self.setLayout(layout)

        # Apply styling
        self.setStyleSheet("""
            QLabel {
                color: #4b0082;
            }
            QTextEdit {
                background-color: #e6e6fa;
                border: 2px solid #4b0082;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton {
                background-color: #4b0082;
                color: white;
                border-radius: 15px;
                padding: 8px;
                font-family: 'Comic Sans MS';
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #4b0082;
            }
        """)

    def append_message(self, message):
        self.text_area.append(message)

    def start_tracker(self):
        tracker_thread = threading.Thread(target=self.start_tracker_operations)
        tracker_thread.start()

    def start_tracker_operations(self):
        self.update_signal.emit("Tracker is ready on " + trackerIP)
        threading.Thread(target=self.remove_inactive_seeders, daemon=True).start()

        while True:
            try:
                message, clientAddress = tracker_socket.recvfrom(2048)
                message_str = message.decode()
                self.update_signal.emit(f"Received message from {clientAddress}: {message_str}")
                parts = message_str.split()

                if parts[0] == "REQUEST":
                    response = self.leecher_msg(message, clientAddress)
                elif parts[0] in ["REGISTER_FILES", "HEARTBEAT"]:
                    response = self.seeder_msg(message, clientAddress)
                else:
                    response = "ERROR: Unknown message type".encode()

                tracker_socket.sendto(response, clientAddress)
                self.update_signal.emit(f"Sent response to {clientAddress}: {response.decode()}")

            except BlockingIOError:
                time.sleep(0.1)  # Small delay to prevent CPU overuse
            except Exception as e:
                self.update_signal.emit(f"Error: {e}")

    def leecher_msg(self, message, clientAddress):
        global next_leecher_id
        message_str = message.decode()
        parts = message_str.split()
        file_name = parts[1]
        leecher_id = f"L{next_leecher_id}"
        next_leecher_id += 1

        leechers[leecher_id] = {
            "Leecher_IP": clientAddress[0],
            "Leecher_Port": clientAddress[1],
            "RequestedFile": file_name
        }

        available_seeders = []
        total_chunks = None
        for seeder_id, seeder_info in seeders.items():
            for file_id, file_info in seeder_info["Files"].items():
                if file_info["FileName"] == file_name:
                    total_chunks = file_info["TotalChunks"]
                    available_seeders.append(f"{seeder_info['IP']},{seeder_info['Port']}")

        if total_chunks is not None:
            available_seeders.append(str(total_chunks))
            return f"{' '.join(available_seeders)}".encode()
        return f"No Seeders with file {file_name}.".encode()

    def seeder_msg(self, message, clientAddress):
        global next_seeder_id, next_file_id
        message_str = message.decode()
        parts = message_str.split()
        IP_address = parts[1]
        Port = parts[2]

        if parts[0] == "REGISTER_FILES":
            available_files_size = parts[3].split(',')
            available_files = []
            available_sizes = []

            for item in available_files_size:
                filename, filesize = item.split(':')
                available_files.append(filename)
                available_sizes.append(filesize)

            seeder_id = f"S{next_seeder_id}"
            next_seeder_id += 1

            if seeder_id not in seeders:
                seeders[seeder_id] = {"IP": IP_address, "Port": Port, "Files": {}}

            for file_info, file_size in zip(available_files, available_sizes):
                current_time = int(time.time())
                file_id = f"F{next_file_id}"
                next_file_id += 1
                total_chunks = int(file_size) // CHUNK_SIZE + (1 if int(file_size) % CHUNK_SIZE else 0)
                seeders[seeder_id]["Files"][file_id] = {
                    "FileName": file_info,
                    "FileSize": file_size,
                    "TotalChunks": total_chunks,
                    "LastSeen": current_time
                }

            return f"REGISTERED {seeder_id} : {clientAddress}".encode()

        elif parts[0] == "HEARTBEAT":
            for sid, data in seeders.items():
                if data["IP"] == IP_address and data["Port"] == Port:
                    current_time = int(time.time())
                    for file_id in seeders[sid]["Files"]:
                        seeders[sid]["Files"][file_id]["LastSeen"] = current_time
                    return f"HEARTBEAT RECEIVED {sid} : {clientAddress}".encode()
            return "ERROR: Seeder not registered.".encode()

    def remove_inactive_seeders(self):
        while True:
            current_time = int(time.time())
            inactive_seeders = []

            for seeder_id, seeder_info in list(seeders.items()):
                if seeder_id == "S1":
                    continue
                for file_info in seeder_info["Files"].values():
                    if current_time - file_info["LastSeen"] > SEEDER_TIMEOUT:
                        inactive_seeders.append(seeder_id)
                        break

            for seeder_id in inactive_seeders:
                self.update_signal.emit(f"Removing inactive seeder: {seeder_id}")
                del seeders[seeder_id]
            time.sleep(10)
# SeederTab works the same Seeder Class 
class SeederTab(QWidget):
    update_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.update_signal.connect(self.append_message)

    def init_ui(self):
        layout = QVBoxLayout()
        self.status_label = QLabel('🌱 Seeder Status 🌱')
        self.status_label.setFont(QFont("Comic Sans MS", 12))
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.start_button = QPushButton('Start Seeding 🌸')
        self.start_button.clicked.connect(self.start_seeder)
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.text_area)
        layout.addWidget(self.start_button)
        self.setLayout(layout)

        # Apply  styling
        self.setStyleSheet("""
            QLabel {
                color: #4b0082;
            }
            QTextEdit {
                background-color: #e6e6fa;
                border: 2px solid #4b0082;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton {
                background-color: #4b0082;
                color: white;
                border-radius: 15px;
                padding: 8px;
                font-family: 'Comic Sans MS';
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #4b0082;
            }
        """)

    def append_message(self, message):
        self.text_area.append(message)

    def start_seeder(self):
        seeder_thread = threading.Thread(target=self.start_seeder_operations)
        seeder_thread.start()

    def start_seeder_operations(self):
        seederSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        seederSock.bind(('0.0.0.0', 0))
        seederIP = socket.gethostbyname(socket.gethostname())
        seederPort = seederSock.getsockname()[1]

        self.update_signal.emit(f"Seeder running at {seederIP}:{seederPort}")
        trackerSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        trackerAddr = (trackerIP, trackerPortNum)

        if self.register(trackerSock, trackerAddr, seederIP, seederPort):
            time.sleep(5)
            heartBeatThread = threading.Thread(target=self.discoverable, args=(trackerSock, trackerAddr, seederIP, seederPort), daemon=True)
            heartBeatThread.start()
            self.start(seederIP, seederPort)
        else:
            self.update_signal.emit("Registration failed.")
            trackerSock.close()

    def handlingClient(self, connectionSock, addr):
        try:
            fileRequest = connectionSock.recv(3000).decode(format)
            if fileRequest.startswith("REQUEST"):
                data = fileRequest.split(" ")
                file_name = data[1]
                chunk_id = int(data[2])

                with open(file_name, "rb") as f:
                    f.seek(chunk_id * CHUNK_SIZE)
                    chunk_data = f.read(CHUNK_SIZE)
                connectionSock.send(chunk_data)

        except Exception as e:
            self.update_signal.emit(f"Error: {e}")
        finally:
            connectionSock.close()

    def start(self, seederIP, seederPort):
        seederSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        seederSock.bind((seederIP, seederPort))
        seederSock.listen(10)
        self.update_signal.emit(f"Seeder listening on {seederPort}")

        while True:
            connectionSock, addr = seederSock.accept()
            thread = threading.Thread(target=self.handlingClient, args=(connectionSock, addr))
            thread.start()

    def register(self, trackerSock, trackerAddr, seederIP, seederPort):
        fileStr = self.fileAvailable()
        if not fileStr:
            return False

        message = f"REGISTER_FILES {seederIP} {seederPort} {fileStr}"
        trackerSock.sendto(message.encode(format), trackerAddr)
        data, _ = trackerSock.recvfrom(1024)
        self.update_signal.emit(f"Tracker Response: {data.decode(format)}")
        return True

    def fileAvailable(self):
        fileArray = []
        for file in filesPresent:
            if os.path.exists(file):
                fileSize = os.path.getsize(file)
                fileArray.append(f"{file}:{fileSize}")
        return ",".join(fileArray) if fileArray else ""

    def discoverable(self, trackerSock, trackerAddr, seederIP, seederPort):
        while True:
            trackerSock.sendto(f"HEARTBEAT {seederIP} {seederPort}".encode(), trackerAddr)
            data, _ = trackerSock.recvfrom(1024)
            self.update_signal.emit("Server Response: " + data.decode(format))
            time.sleep(30)

class DownloaderTab(QWidget):
    def __init__(self, seeder_tab):
        super().__init__()
        self.seeder_tab = seeder_tab
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.file_name_label = QLabel('📥 Enter Filename 📥')
        self.file_name_label.setFont(QFont("Comic Sans MS", 12))
        self.file_name_input = QLineEdit()
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.download_button = QPushButton("Download Now!")
        self.download_button.clicked.connect(self.start_download)
        
        layout.addWidget(self.file_name_label)
        layout.addWidget(self.file_name_input)
        layout.addWidget(self.text_area)
        layout.addWidget(self.download_button)
        self.setLayout(layout)

        # Apply cute styling
        self.setStyleSheet("""
            QLabel {
                color: #4b0082;
            }
            QLineEdit {
                background-color: #e6e6fa;
                border: 2px solid #4b0082;
                border-radius: 10px;
                padding: 5px;
            }
            QTextEdit {
                background-color: #f8f0ff;
                border: 2px solid #4b0082;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton {
                background-color: #4b0082;
                color: white;
                border-radius: 15px;
                padding: 8px;
                font-family: 'Comic Sans MS';
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #4b0082;
            }
        """)

    def append_message(self, message):
        self.text_area.append(message)

    def start_download(self):
        file_name = self.file_name_input.text().strip()
        if not file_name:
            self.append_message("Please enter a valid file name.")
            return

        self.append_message(f"Starting download for {file_name}...")
        self.download_thread = DownloadThread(file_name, leecherIP, leecherPortNum, self.seeder_tab)
        self.download_thread.update_signal.connect(self.append_message)
        self.download_thread.start()
        
# Main app to control the GUI interface and interaction
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🌼 P2P File Sharing System 🌼")
        self.setGeometry(100, 100, 800, 600)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.tracker_tab = TrackerTab()
        self.seeder_tab = SeederTab()
        self.downloader_tab = DownloaderTab(self.seeder_tab)
        
        self.tabs.addTab(self.tracker_tab, "Tracker")
        self.tabs.addTab(self.seeder_tab, "Seeder")
        self.tabs.addTab(self.downloader_tab, "Downloader")

        # Set cyan background and overall styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #e6e6fa;  /* Cyan background */
            }
            QTabWidget::pane {
                border: 2px solid #e6e6fa;
                background-color: #e6e6fa;
                border-radius: 10px;
            }
            QTabBar::tab:selected {
                background-color:#e6e6fa;
            }
        """)

def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()