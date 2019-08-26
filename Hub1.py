from Hub import Hub
import socket



hub = Hub( 5, 1024, '$'  )
# hub.bind_servers_listener( "192.168.4.100", 3000 )
hub.bind_clients_listener( socket.gethostname(), 3000 )
hub.power_on()