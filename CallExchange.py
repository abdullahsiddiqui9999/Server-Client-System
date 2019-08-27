from DiscreteMessageHandlingServer import DiscreteMessageHandlingServer
import socket
from CustomExceptions import ClientOfflineException, ClientIsBusyException, ClientUnreachableException, UserValidationFailedException

class CallExchange( DiscreteMessageHandlingServer ):
    def __init__(self, max_num_clients, receiving_buffer_size, message_delimiter, basic_server_pointer, video_server_pointer):
        DiscreteMessageHandlingServer.__init__(self, max_num_clients, receiving_buffer_size, message_delimiter)
        self.basic_server_pointer = basic_server_pointer
        self.recipient_call_sockets = {}
        self.video_server_pointer = video_server_pointer

    def _drop_client(self, connection):
        #-------------------------------------------------------------------------
        #Remove extra resources if allocated here!
        #------------------------------------------------------------------------
        try:
            recipient_call_socket = self.connections_information[ connection]['recipient_call_socket']
            recipient_call_socket.close()
            recipient_exchange_socket = self.connections_information[ connection]['recipient_exchange_socket']
            self.setIsBusy( recipient_exchange_socket, False )
            del self.recipient_call_sockets[ recipient_call_socket ]
        except KeyError:
            pass
        DiscreteMessageHandlingServer._drop_client(self, connection)

    def setIsBusy(self, exchange_socket, value ):
        self.connections_information[ exchange_socket]['is_busy'] = value

    def registerUser(self, socket, message):
        header, id, port = message.split( '\n' )
        try:
            self.connections_information[ socket] = {
                'id' : id,
                'username': self.basic_server_pointer.getUsernameThroughID( id ),
                'incoming_call_port': port,
                'is_busy': False
            }
            self.append_message_to_sending_queue(socket,
                             "{}1\nValidation succeed!{}".format(self.message_delimiter, self.message_delimiter))
        except UserValidationFailedException:
            print( "Invalid user" )
            self.append_message_to_sending_queue(socket, "{}0\nValidation failed!{}".format(self.message_delimiter, self.message_delimiter))
            self._drop_client(socket)

    def handleMessageFromDialer(self, dialer_socket, message):
        if message.startswith( 'connect_to' ):
            try:
                self.configureIncomingConnection(dialer_socket, message)
            except ClientOfflineException:
                self.append_message_to_sending_queue(dialer_socket, "{}ERROR:{}{}".format(self.message_delimiter, "Client offline",
                                                                                          self.message_delimiter))
                self._drop_client(dialer_socket)
                print( "Client is offline" )
            except ClientIsBusyException:
                self.append_message_to_sending_queue(dialer_socket, "{}ERROR:{}{}".format(self.message_delimiter, "Client is busy",
                                                                                          self.message_delimiter))
                self._drop_client(dialer_socket)
                print( "Client is busy" )
            except ClientUnreachableException:
                self.append_message_to_sending_queue(dialer_socket, "{}ERROR:{}{}".format(self.message_delimiter, "Client is unreachable",
                                                                                          self.message_delimiter))
                self._drop_client(dialer_socket)
                print("Client is unreachable")
        elif message.startswith( 'tone' ):
            self.append_message_to_sending_queue(self.connections_information[ dialer_socket]['recipient_call_socket'], '{}tone{}'.format(
                self.message_delimiter, self.message_delimiter ))

    def handleMessageFromRecipientCallSocket( self, recipient_call_socket, message ):
        if message.startswith("ACCEPTED"):
            # Export to video server
            # self.sendMessage(self.recipient_call_sockets[recipient_call_socket]['dialer_socket'], '{}ACCEPTED{}'.format(
            #     self.message_delimiter, self.message_delimiter))

            self.recipient_call_sockets[ recipient_call_socket ][ 'dialer_socket' ].sendall( '{}ACCEPTED{}'.format(
                self.message_delimiter, self.message_delimiter).encode() )

            # self.sendMessage( recipient_call_socket , '{}connected{}'.format( self.message_delimiter, self.message_delimiter) )
            recipient_call_socket.sendall( '{}connected{}'.format( self.message_delimiter, self.message_delimiter).encode() )


            self.video_server_pointer.importClient(
                                                    recipient_call_socket,
                                                    self.recipient_call_sockets[ recipient_call_socket ][ 'dialer_socket' ],
                                                    self.recipient_call_sockets[ recipient_call_socket ][ 'recipient_exchange_socket' ]
                                                    )

            self._remove_resources(recipient_call_socket)
            self._remove_resources(self.recipient_call_sockets[recipient_call_socket]['dialer_socket'])

        elif message.startswith("REJECTED"):
            self.append_message_to_sending_queue(self.recipient_call_sockets[ recipient_call_socket]['dialer_socket'], '{}REJECTED{}'.format(
                self.message_delimiter, self.message_delimiter))

    def process_discrete_message(self, socket, message):
        if message.startswith( 'registration' ) :
            self.registerUser( socket, message )
        elif socket in self.recipient_call_sockets:
            self.handleMessageFromRecipientCallSocket( socket, message )
        else:
            self.handleMessageFromDialer( socket, message )

    def configureIncomingConnection(self, dialer_socket, message):
        noti, recipient, caller, type_of_dial = message.split( '\n' )

        recipient_exchange_socket = self.findSocket(recipient)

        if recipient_exchange_socket == False:
            raise ClientOfflineException

        if self.connections_information[ recipient_exchange_socket]['is_busy']:
            raise ClientIsBusyException


        recipient_call_socket = socket.socket()
        try:
            port = eval(self.connections_information[ recipient_exchange_socket]['incoming_call_port'])
            recipient_call_socket.connect( ( recipient_exchange_socket.getpeername()[0], port ) )
        except socket.error:
            raise ClientUnreachableException

        # self.sendMessage(recipient_call_socket, "{}incoming_call\n{}\n{}\n{}{}".format(self.message_delimiter,
        #                                                                                recipient, caller, type_of_dial,
        #                                                                                self.message_delimiter))

        recipient_call_socket.sendall( "{}incoming_call\n{}\n{}\n{}{}".format(self.message_delimiter,
                                                                                       recipient, caller, type_of_dial,
                                                                                       self.message_delimiter).encode() )

        self.connections_information[ dialer_socket]["recipient"] = recipient
        self.connections_information[ dialer_socket]["caller"] = caller
        self.connections_information[ dialer_socket]["type_of_dial"] = type_of_dial
        self.connections_information[ dialer_socket]['recipient_call_socket'] = recipient_call_socket
        self.connections_information[ dialer_socket]['recipient_exchange_socket'] = recipient_exchange_socket
        self.recipient_call_sockets[ recipient_call_socket ] = {
            'dialer_socket': dialer_socket,
            'recipient_exchange_socket': recipient_exchange_socket
        }
        self.setIsBusy( recipient_exchange_socket, True )
        DiscreteMessageHandlingServer._initialize_client(self, recipient_call_socket)

