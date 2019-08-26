from ContinuousMessageHandlingServer import ContinuousMessageHandlingServer
import socket, queue

class VideoServer( ContinuousMessageHandlingServer ):
    def __init__(self, max_num_clients, receiving_buffer_size, message_delimiter):
        ContinuousMessageHandlingServer.__init__(self, max_num_clients, receiving_buffer_size, message_delimiter)

    def setCallExchange(self, call_exchange_pointer):
        self.call_exchange_pointer = call_exchange_pointer

    def drop_client(self, socket):
        #-------------------------------------------------------------------------
        #Remove extra resources if allocated here!
        #-------------------------------------------------------------------------
        self.connections_information[ socket]['partner_socket'].close()
        try:
            print( 'Executing set is busy!' )
            self.call_exchange_pointer.setIsBusy(self.connections_information[ socket]['client_exchange_socket'], False)
        except KeyError:
            pass

        ContinuousMessageHandlingServer.drop_client(self, socket)

    def importClient(self, client_socket, partner_socket, client_exchange_socket):
        print( "Importing!" )
        dummy_socket = socket.socket()
        # client_socket.sendall( "Hi".encode() )
        self.initialize_client(client_socket)
        self.initialize_client(partner_socket)
        self.connections_information[ client_socket] = {
            'partner_socket': partner_socket,
            'client_exchange_socket': client_exchange_socket
        }
        self.connections_information[ partner_socket] = {
            'partner_socket': client_socket
        }
        print( "Dummy socket connecting!" )
        dummy_socket.connect( self.listener.getsockname() )

    def process_message(self, socket, message):
        self.append_message_to_sending_queue(self.connections_information[ socket]['partner_socket'], message)