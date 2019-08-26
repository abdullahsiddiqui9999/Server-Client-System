from ServerPackage import ServerPackage
import threading
import socket

sv1 = ServerPackage( socket.gethostname(), 5, '$' )
video_receiving_buffer_size = 51200



sv1.startBasicServer( 27015, 1024, socket.gethostname(), 3000 )
sv1.startMessagingServer( 6000, 7000, 1024 )
sv1.startVideoServer( 8000, 9000, video_receiving_buffer_size )
sv1.startDialer( 5000, 1024 )

sv1.stopMainThread()