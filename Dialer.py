from DiscreteMessageHandlingServer import DiscreteMessageHandlingServer
import socket
from CustomExceptions import ClientOfflineException, UnknownCallerException, UserValidationFailedException

class Dialer( DiscreteMessageHandlingServer ):
    def __init__(self, max_num_clients, receiving_buffer_size, message_delimiter, basic_server_pointer, max_ring_count):
        DiscreteMessageHandlingServer.__init__(self, max_num_clients, receiving_buffer_size, message_delimiter)
        self.basic_server_pointer = basic_server_pointer
        self.max_ring_count = max_ring_count
        self.exchange_sockets = {}

    def setVideoServer(self, video_server_pointer ):
        self.video_server_pointer = video_server_pointer

    def setCallExchange(self, call_exchange_pointer ):
        self.call_exchange_pointer = call_exchange_pointer

    def _drop_client(self, connection):
        #-------------------------------------------------------------------------
        #Remove extra resources if allocated here!
        #------------------------------------------------------------------------
        try:
            exchange_socket = self.connections_information[ connection]["exchange_socket"]
            exchange_socket.close()
            del self.exchange_sockets[ exchange_socket ]
        except KeyError:
            pass
        DiscreteMessageHandlingServer._drop_client(self, connection)

    def registerUser(self, socket, message):
        header, id = message.split( '\n' )
        try:
            self.connections_information[ socket] = {
                'id' : id,
                'username': self.basic_server_pointer.getUsernameThroughID( id )
            }
            self.append_message_to_sending_queue(socket,
                             "{}1\nValidation succeed!{}".format(self.message_delimiter, self.message_delimiter))
        except UserValidationFailedException:
            print( "Invalid user" )
            self.append_message_to_sending_queue(socket, "{}0\nValidation failed!{}".format(self.message_delimiter, self.message_delimiter))
            self._drop_client(socket)

    def handleDataFromDialingClient(self, sock, message):
        if message.startswith('dial_info'):
            try:
                self.configureDial(sock, message)
            except ClientOfflineException:
                self.append_message_to_sending_queue(sock, "{}ERROR:{}{}".format(self.message_delimiter, "Client offline",
                                                                                 self.message_delimiter))
                print("Current cline is offline now")
                self._drop_client(sock)
            except UnknownCallerException:
                print( "Unregistered caller" )
            except socket.error:
                self.append_message_to_sending_queue(sock, "{}ERROR:{}{}".format(self.message_delimiter, "Client Unreachable",
                                                                                 self.message_delimiter))
                print("Unable to connect to exchange")
                self._drop_client(sock)

        elif message.startswith( 'tone' ):
            self.append_message_to_sending_queue(self.connections_information[ sock]['exchange_socket'], "{}tone{}".format(self.message_delimiter, self.message_delimiter))

    def handleDataFromExchangeSocket(self, sock, message ):
        if message.startswith("ERROR"):
            self.append_message_to_sending_queue(self.exchange_sockets[ sock]['dialer_socket'], "{}{}{}".format(self.message_delimiter, message, self.message_delimiter))
        elif message.startswith("ACCEPTED"):
            # Export to video server
            dialer_socket = self.exchange_sockets[ sock ][ 'dialer_socket' ]

            # self.sendMessage( dialer_socket,
            #                  "{}{}{}".format(self.message_delimiter, message, self.message_delimiter))
            dialer_socket.sendall( "{}{}{}".format(self.message_delimiter, message, self.message_delimiter).encode() )

            self.video_server_pointer.importClient(dialer_socket, sock, self.connections_information[ dialer_socket]['caller_exchange_socket'])

            self._remove_resources(dialer_socket)
            self._remove_resources(sock)
        elif message.startswith("REJECTED"):
            # Drop client
            self.append_message_to_sending_queue(self.exchange_sockets[sock]['dialer_socket'],
                             "{}{}{}".format(self.message_delimiter, message, self.message_delimiter))
            self._drop_client(sock)

    def process_discrete_message(self, sock, message):
        if message.startswith( 'registration' ):
            self.registerUser( sock, message )
        elif sock in self.exchange_sockets:
            self.handleDataFromExchangeSocket( sock, message )
        else:
            self.handleDataFromDialingClient( sock, message )

    def configureDial(self, sock, configuration_message):
        notification, recipient, caller, type_of_dial = configuration_message.split( '\n' )
        self.connections_information[ sock]["recipient"] = recipient
        self.connections_information[ sock]["caller"] = caller
        self.connections_information[ sock]["type_of_dial"] = type_of_dial
        self.connections_information[ sock]["number_of_rings"] = 0

        caller_exchange_socket = self.call_exchange_pointer.findSocket( caller )
        if caller_exchange_socket == False:
            raise UnknownCallerException

        self.connections_information[sock]["caller_exchange_socket"] = caller_exchange_socket

        gateway = self.basic_server_pointer.getClientGateway( recipient )
        exchange_socket = socket.socket()
        exchange_socket.connect( ( gateway, self.call_exchange_pointer.getPort() ) )
        self.connections_information[ sock]["exchange_socket"] = exchange_socket
        self._initialize_client(exchange_socket)
        self.append_message_to_sending_queue(exchange_socket, "{}connect_to\n{}\n{}\n{}{}".format(self.message_delimiter, recipient, caller, type_of_dial, self.message_delimiter))
        self.exchange_sockets[ exchange_socket ] = {
            'dialer_socket' : sock
        }
        self.call_exchange_pointer.setIsBusy( caller_exchange_socket, True )
