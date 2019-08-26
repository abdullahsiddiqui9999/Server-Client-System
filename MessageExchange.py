from DiscreteMessageHandlingServer import DiscreteMessageHandlingServer
import socket as sc

class MessageExchange( DiscreteMessageHandlingServer ):
    def __init__( self, max_num_clients, receiving_chunk_size, message_delimiter, messaging_server_pointer ):
        DiscreteMessageHandlingServer.__init__( self, max_num_clients, receiving_chunk_size, message_delimiter )
        self.messaging_server_pointer = messaging_server_pointer

    def dropClient(self, socket):
        #-------------------------------------------------------------------------
        #Remove extra resources if allocated here!
        #------------------------------------------------------------------------

        DiscreteMessageHandlingServer.dropClient( self, socket )

    def processDiscreteMessage( self, socket, message ):
        try:
            temp_socket = sc.socket()
            temp_socket.connect( ( self.listener.getsockname()[0], 6000 ) )
            temp_socket.sendall( "{}{}{}".format( self.message_delimiter, message, self.message_delimiter ).encode() )
            temp_socket.close()
        except sc.error:
            print( "Unable to connect to messaging server!" )