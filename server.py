import socket as sock
import threading
import os

server = sock.socket()
server.bind(('localhost', 8080))
server.listen(5)
print("Server is listening on port 8080...")
