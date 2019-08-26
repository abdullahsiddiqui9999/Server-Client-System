from DiscreteMessageHandlingServer import DiscreteMessageHandlingServer
import socket
from CustomExceptions import ClientOfflineException, UnknownCallerException, UserValidationFailedException

class Dialer( DiscreteMessageHandlingServer ):
    def __init__(self, max_num_clients, receiving_chunk_size, message_delimiter, basic_server_pointer, max_ring_count ):
        DiscreteMessageHandlingServer.__init__( self, max_num_clients, receiving_chunk_size, message_delimiter )
        self.basic_server_pointer = basic_server_pointer
        self.max_ring_count = max_ring_count
        self.exchange_sockets = {}

    def setVideoServer(self, video_server_pointer ):
        self.video_server_pointer = video_server_pointer

    def setCallExchange(self, call_exchange_pointer ):
        self.call_exchange_pointer = call_exchange_pointer

    def dropClient(self, socket):
        #-------------------------------------------------------------------------
        #Remove extra resources if allocated here!
        #------------------------------------------------------------------------
        try:
            exchange_socket = self.sockets_info[ socket ][ "exchange_socket" ]
            exchange_socket.close()
            del self.exchange_sockets[ exchange_socket ]
        except KeyError:
            pass
        DiscreteMessageHandlingServer.dropClient( self, socket )

    def registerUser(self, socket, message):
        header, id = message.split( '\n' )
        try:
            self.sockets_info[ socket ] = {
                'id' : id,
                'username': self.basic_server_pointer.getUsernameThroughID( id )
            }
            self.sendMessage(socket,
                             "{}1\nValidation succeed!{}".format(self.message_delimiter, self.message_delimiter))
        except UserValidationFailedException:
            print( "Invalid user" )
            self.sendMessage(socket, "{}0\nValidation failed!{}".format(self.message_delimiter, self.message_delimiter))
            self.dropClient( socket )

    def handleDataFromDialingClient(self, sock, message):
        if message.startswith('dial_info'):
            try:
                self.configureDial(sock, message)
            except ClientOfflineException:
                self.sendMessage(sock, "{}ERROR:{}{}".format(self.message_delimiter, "Client offline",
                                                             self.message_delimiter))
                print("Current cline is offline now")
                self.dropClient(sock)
            except UnknownCallerException:
                print( "Unregistered caller" )
            except socket.error:
                self.sendMessage(sock, "{}ERROR:{}{}".format(self.message_delimiter, "Client Unreachable",
                                                             self.message_delimiter))
                print("Unable to connect to exchange")
                self.dropClient(sock)

        elif message.startswith( 'tone' ):
            self.sendMessage( self.sockets_info[ sock ][ 'exchange_socket' ], "{}tone{}".format( self.message_delimiter, self.message_delimiter ) )

    def handleDataFromExchangeSocket(self, sock, message ):
        if message.startswith("ERROR"):
            self.sendMessage(self.exchange_sockets[ sock ][ 'dialer_socket' ], "{}{}{}".format(self.message_delimiter, message, self.message_delimiter))
        elif message.startswith("ACCEPTED"):
            # Export to video server
            dialer_socket = self.exchange_sockets[ sock ][ 'dialer_socket' ]

            # self.sendMessage( dialer_socket,
            #                  "{}{}{}".format(self.message_delimiter, message, self.message_delimiter))
            dialer_socket.sendall( "{}{}{}".format(self.message_delimiter, message, self.message_delimiter).encode() )

            self.video_server_pointer.importClient( dialer_socket, sock, self.sockets_info[ dialer_socket ][ 'caller_exchange_socket' ] )

            self.removeResources(dialer_socket)
            self.removeResources(sock)
        elif message.startswith("REJECTED"):
            # Drop client
            self.sendMessage(self.exchange_sockets[sock]['dialer_socket'],
                             "{}{}{}".format(self.message_delimiter, message, self.message_delimiter))
            self.dropClient(sock)

    def processDiscreteMessage(self, sock, message):
        if message.startswith( 'registration' ):
            self.registerUser( sock, message )
        elif sock in self.exchange_sockets:
            self.handleDataFromExchangeSocket( sock, message )
        else:
            self.handleDataFromDialingClient( sock, message )

    def configureDial(self, sock, configuration_message):
        notification, recipient, caller, type_of_dial = configuration_message.split( '\n' )
        self.sockets_info[ sock ][ "recipient" ] = recipient
        self.sockets_info[ sock ][ "caller" ] = caller
        self.sockets_info[ sock ][ "type_of_dial" ] = type_of_dial
        self.sockets_info[ sock ][ "number_of_rings" ] = 0

        caller_exchange_socket = self.call_exchange_pointer.findSocket( caller )
        if caller_exchange_socket == False:
            raise UnknownCallerException

        self.sockets_info[sock]["caller_exchange_socket"] = caller_exchange_socket

        gateway = self.basic_server_pointer.getClientGateway( recipient )
        exchange_socket = socket.socket()
        exchange_socket.connect( ( gateway, self.call_exchange_pointer.getPort() ) )
        self.sockets_info[ sock ][ "exchange_socket" ] = exchange_socket
        self.initializeClient( exchange_socket )
        self.sendMessage( exchange_socket, "{}connect_to\n{}\n{}\n{}{}".format( self.message_delimiter, recipient, caller, type_of_dial, self.message_delimiter ) )
        self.exchange_sockets[ exchange_socket ] = {
            'dialer_socket' : sock
        }
        self.call_exchange_pointer.setIsBusy( caller_exchange_socket, True )
