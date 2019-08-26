from ServerCore import ServerCore

class ContinuousMessageHandlingServer( ServerCore ):
    def __init__(self, max_num_clients, receiving_chunk_size, message_delimiter ):
        ServerCore.__init__( self, max_num_clients, receiving_chunk_size, message_delimiter )


    def processReceivedData(self, socket):
        try:
            data = socket.recv(self.receiving_chunk_size).decode()
        except ConnectionResetError:
            self.dropClient( socket )
            return
        except OSError:
            self.dropClient( socket )
            return

        if data:
            self.processMessage( socket, data )
        else:
            self.dropClient( socket )