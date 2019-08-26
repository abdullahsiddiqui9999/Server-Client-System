from ServerCore import ServerCore

class DiscreteMessageHandlingServer( ServerCore ):
    def __init__(self, max_num_clients, receiving_chunk_size, message_delimiter ):
        ServerCore.__init__( self, max_num_clients, receiving_chunk_size, message_delimiter )

    def processMessage( self, socket, message ):
        if  message.endswith( '{}'.format( self.message_delimiter ) ) :
            is_complete_message = True
            message = self.socket_buffers[ socket ] + message
            self.socket_buffers[ socket ] = ""
        else:
            self.socket_buffers[ socket ] += message
            is_complete_message = False

        if is_complete_message:
            message = message.strip( self.message_delimiter )
            self.processDiscreteMessage( socket, message )

    def processDiscreteMessage(self, socket, message ):
        raise NotImplementedError