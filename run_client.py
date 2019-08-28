import socket

for i in range(0, 5):
    s = socket.socket()
    s.setblocking(True)
    s.connect(('127.0.0.1', 27016))
    s.close()
