from ServerPackage import ServerPackage
import threading
import socket

sv2 = ServerPackage( '192.168.2.100', 5, '$')
video_receiving_buffer_size = 51200


sv2.startBasicServer(27015, 1024, socket.gethostname(), 3000)
sv2.startMessagingServer(6000, 7000, 1024)
sv2.startVideoServer(8000, 9000, video_receiving_buffer_size)
sv2.startDialer(5000, 1024)

sv2.stopMainThread()