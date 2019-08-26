from ContinuousMessageHandlingServer import ContinuousMessageHandlingServer
import socket, queue

class VideoServer( ContinuousMessageHandlingServer ):
    def __init__(self, max_num_clients, receiving_chunk_size, message_delimiter ):
        ContinuousMessageHandlingServer.__init__( self, max_num_clients, receiving_chunk_size, message_delimiter )

    def setCallExchange(self, call_exchange_pointer):
        self.call_exchange_pointer = call_exchange_pointer

    def dropClient(self, socket):
        #-------------------------------------------------------------------------
        #Remove extra resources if allocated here!
        #-------------------------------------------------------------------------
        self.sockets_info[ socket ][ 'partner_socket' ].close()
        try:
            print( 'Executing set is busy!' )
            self.call_exchange_pointer.setIsBusy( self.sockets_info[ socket ][ 'client_exchange_socket' ], False )
        except KeyError:
            pass

        ContinuousMessageHandlingServer.dropClient( self, socket )

    def importClient(self, client_socket, partner_socket, client_exchange_socket):
        print( "Importing!" )
        dummy_socket = socket.socket()
        # client_socket.sendall( "Hi".encode() )
        self.initializeClient( client_socket )
        self.initializeClient( partner_socket )
        self.sockets_info[ client_socket ] = {
            'partner_socket': partner_socket,
            'client_exchange_socket': client_exchange_socket
        }
        self.sockets_info[ partner_socket ] = {
            'partner_socket': client_socket
        }
        print( "Dummy socket connecting!" )
        dummy_socket.connect( self.listener.getsockname() )

    def processMessage(self, socket, message):
        self.sendMessage( self.sockets_info[ socket ][ 'partner_socket' ], message )