from DiscreteMessageHandlingServer import DiscreteMessageHandlingServer
import socket
from CustomExceptions import UserValidationFailedException, ClientOfflineException

class MessagingServer( DiscreteMessageHandlingServer ):
    def __init__(self, max_num_clients, receiving_chunk_size, message_delimiter, basic_server_pointer ):
        DiscreteMessageHandlingServer.__init__( self, max_num_clients, receiving_chunk_size, message_delimiter )
        self.basic_server_pointer = basic_server_pointer


    def dropClient(self, socket):
        #-------------------------------------------------------------------------
        #Remove extra resources if allocated here!
        #------------------------------------------------------------------------

        DiscreteMessageHandlingServer.dropClient( self, socket )

    def registerUser(self, socket, message):
        noti, id = message.split( '\n' )
        try:
            self.sockets_info[ socket ] = {
                'id' : id,
                'username': self.basic_server_pointer.getUsernameThroughID( id )
            }
            self.sendMessage(socket, "{}1\nValidation succeed!{}".format(self.message_delimiter, self.message_delimiter))
        except UserValidationFailedException:
            print( "Invalid user" )
            self.sendMessage( socket, "{}0\nValidation failed!{}".format( self.message_delimiter, self.message_delimiter ) )
            self.dropClient( socket )

    def processDiscreteMessage(self, sock, message):
        if message.startswith( 'registration' ):
            self.registerUser( sock, message )
        else:
            sendee_name, sender_name, content = message.split( '\n' )

            sendee_socket = self.findSocket( sendee_name )
            if sendee_socket != False:
                #Local client.
                self.sendMessage( sendee_socket, '{}{}{}'.format( self.message_delimiter, message, self.message_delimiter ) )
            else:
                #Its a foreign client, connect to foreign servers exchange.
                print( "Foreign client!" )
                try:
                    client_exchange_gateway = self.basic_server_pointer.getClientGateway(sendee_name)
                    try:
                        #Foreign server exchange port = 7000
                        self.sendMessageToForeignServerExchange( client_exchange_gateway, 7000, "{}{}{}".format( self.message_delimiter, message, self.message_delimiter ) )
                    except socket.error:
                        print( "Unable to send message to foreign server exchange" )
                except ClientOfflineException:
                    print( "Client not found in the directory!" )

    def sendMessageToForeignServerExchange(self, gateway, port, message):
        temp_socket = socket.socket()
        temp_socket.connect( ( gateway, port ) )
        temp_socket.sendall( message.encode() )
        temp_socket.close()


