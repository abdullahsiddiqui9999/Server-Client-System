from BasicServer import BasicServer
import socket

sv = BasicServer( 5, 4096, '$' )

sv.bind_clients_listener( socket.gethostname(), 27015 )

sv.connectToHub( socket.gethostname(), 3000 )

sv.power_on()

