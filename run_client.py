import socket


s = socket.socket()
s.connect(('127.0.0.1', 27015))
s.setblocking(True)

for i in range(0, 50):
    s.send('$a$'.encode())

s.close()
