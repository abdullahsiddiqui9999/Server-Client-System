import socket
from BasicServer import BasicServer
from CallExchange import CallExchange
from MessageExchange import MessageExchange
from MessagingServer import MessagingServer
from VideoServer import VideoServer
from ServerModule import ServerModule
from Dialer import Dialer


class ServerPackage:
    def __init__(self, host, num_clients, message_delimiter):
        self.host = host
        self.message_delimiter = message_delimiter
        self.num_clients = num_clients

        self.basic_server = None
        self.basic_server_port = None
        self.basic_server_module = None

        self.video_server = None
        self.video_server_port = None
        self.video_server_module = None

        self.message_exchange = None
        self.message_exchange_port = None
        self.message_exchange_module = None

        self.messaging_server = None
        self.messaging_server_port = None
        self.messaging_server_module = None

        self.call_exchange = None
        self.call_exchange_port = None
        self.call_exchange_module = None

        self.dialer = None
        self.dialer_port = None
        self.dialer_module = None

    def startBasicServer(self, port, receiving_chunk_size, hub_host, hub_port ):
        print( "Starting basic server!" )
        try:
            basic_server = BasicServer( self.num_clients, receiving_chunk_size, self.message_delimiter )
            basic_server.bind_clients_listener( self.host, port )
            basic_server.connectToHub( hub_host, hub_port )

            basic_server_module = ServerModule( basic_server )
            basic_server_module.start()
            self.basic_server = basic_server
            self.basic_server_port = port
            self.basic_server_module = basic_server_module
        except socket.error:
            print( "Unable to start basic server module!" )

    def startVideoServer( self, sv_port, exchange_port, receiving_chunk_size ):
        print("Starting video server!")
        if self.basic_server is None:
            print( "Cannot start video server without basic server" )
        else:
            try:
                video_server = VideoServer( self.num_clients, receiving_chunk_size, self.message_delimiter )
                video_server.bind_clients_listener( self.host, sv_port )

                call_exchange = CallExchange( self.num_clients, receiving_chunk_size, self.message_delimiter, self.basic_server, video_server )
                call_exchange.bind_clients_listener( self.host, exchange_port )


                #Setters
                video_server.setCallExchange( call_exchange )


                video_server_module = ServerModule( video_server )
                video_server_module.start()

                call_exchange_module = ServerModule( call_exchange )
                call_exchange_module.start()


                self.video_server = video_server
                self.video_server_port = sv_port
                self.video_server_module = video_server_module
                self.call_exchange = call_exchange
                self.call_exchange_port = exchange_port
                self.call_exchange_module = call_exchange_module
            except socket.error:
                print( "Unable to start video server module!" )

    def startDialer(self, port, receiving_chunk_size ):
        print("Starting dialer!")
        if self.basic_server is None:
            print( "Cannot start dialer without basic server" )
            return
        if self.video_server is None:
            print("Cannot start dialer without video server")
            return
        if self.call_exchange is None:
            print("Cannot start dialer without call exchange server")
            return

        dialer = Dialer(self.num_clients, receiving_chunk_size, self.message_delimiter, self.basic_server, 10)
        dialer.bind_clients_listener(self.host, port)

        dialer.setCallExchange(self.call_exchange)
        dialer.setVideoServer(self.video_server)

        dialer_module = ServerModule(dialer)
        dialer_module.start()

        self.dialer = dialer
        self.dialer_port = port
        self.dialer_module = dialer_module

    def startMessagingServer(self, sv_port, exchange_port, receiving_chunk_size):
        print("Starting messaging server!")
        if self.basic_server is None:
            print( "Cannot start messaging server without basic server" )
        else:
            try:
                messaging_server = MessagingServer( self.num_clients, receiving_chunk_size, self.message_delimiter, self.basic_server )
                messaging_server.bind_clients_listener(self.host, sv_port)
                messaging_exchange = MessageExchange(self.num_clients, receiving_chunk_size, self.message_delimiter, messaging_server)
                messaging_exchange.bind_clients_listener(self.host, exchange_port )


                messaging_server_module = ServerModule( messaging_server )
                messaging_server_module.start()
                messaging_exchange_module = ServerModule(messaging_exchange)
                messaging_exchange_module.start()

                self.messaging_server = messaging_server
                self.messaging_server_port = sv_port
                self.messaging_server_module = messaging_server_module
                self.message_exchange = messaging_exchange
                self.message_exchange_port = exchange_port
                self.message_exchange_module = messaging_exchange_module
            except socket.error:
                print( "Unable to start messaging server module!" )


    def stopMainThread(self):
        if self.basic_server_module is not None:
            self.basic_server_module.join()

        if self.video_server_module is not None:
            self.video_server_module.join()

        if self.message_exchange_module is not None:
            self.message_exchange_module.join()

        if self.messaging_server_module is not None:
            self.messaging_server_module.join()

        if self.dialer_module is not None:
            self.dialer_module.join()

        if self.call_exchange_module is not None:
            self.call_exchange_module.join()


