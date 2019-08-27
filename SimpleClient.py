import base64
import socket


s = socket.socket()
s.connect(('127.0.0.1', 27015))
s.setblocking(True)

with open("DSC_0124.JPG", "rb") as image_file:
    file_data = image_file.read()
    print(len(file_data))
    b64encoded_file_data = base64.b64encode(file_data).decode()
    for i in range(0, 50):
        print("Sending...")
        s.send('$a$'.encode())
s.close()





