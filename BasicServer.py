from DiscreteMessageHandlingServer import DiscreteMessageHandlingServer
import socket, queue
from CustomExceptions import ClientOfflineException, UserValidationFailedException

class BasicServer( DiscreteMessageHandlingServer ):
    def __init__(self, max_num_clients, receiving_buffer_size, message_delimiter):
        DiscreteMessageHandlingServer.__init__(self, max_num_clients, receiving_buffer_size, message_delimiter)
        self.clients_ledger = {}
        self.hub = socket.socket()

    # ------------------------------
    def process_discrete_message(self, socket, message):
        if socket is self.hub:
            self.handleMessageFromHub(message)
        else:
            message = message.strip( self.message_delimiter )
            if message.startswith("login_request".format( self.message_delimiter )):
                if self.authenticate( socket, message ):
                    self.append_message_to_sending_queue(socket, "{}{}{}".format(self.message_delimiter, self.connections_information[ socket]['id'], self.message_delimiter))
                    self.broadcastClient( socket )
                else:
                    self.append_message_to_sending_queue(socket, "{}{}{}".format(self.message_delimiter, '-1', self.message_delimiter))
    # --------------------------------

    def handleMessageFromHub(self, message):
        if message.startswith( 'new_client_alert' ):
            self.storeClientInLedger( message )
    # ----------------------------------

    def storeClientInLedger (self, notification):
        notification, name, gateway = notification.split( '\n' )
        name = name.split( ':' )[1]
        gateway = gateway.split( ':' )[1]
        self.clients_ledger[ name ] = {
            'gateway': gateway
        }
        print( "{} is online at {}".format( name, gateway ) )
    # -------------------------------------

    def broadcastClient(self, socket ):
        broadcasting_message = \
            "{}new_client_alert\nName:{}\ngateway:{}{}".format(self.message_delimiter,
                                                               self.connections_information[ socket]["username"],
                                                               self._listener.getsockname()[0],
                                                               self.message_delimiter)
        self._message_queues[ self.hub].put(broadcasting_message)
        if self.hub not in self._outputs:
            self._outputs.append(self.hub)
    # ------------------------------------

    def _drop_client(self, connection):
        print( "Dropping {}!".format(self.connections_information[ connection]['username']))
        #-------------------------------------------------------------------------
        #Remove extra resources if allocated here!
        #------------------------------------------------------------------------
        DiscreteMessageHandlingServer._drop_client(self, connection)
    # ------------------------------------

    def authenticate(self, socket, request_message):
        try:
            header, username, password = request_message.split('\n')

            #Generate a key for this client.
            self.connections_information[ socket] = {
                'id' : DiscreteMessageHandlingServer.client_id,
                'username' : username,
            }
            return True
        except Exception:
            return False
    # ------------------------------------

    def connectToHub(self, host, port):
        self.hub.connect((host, port))
        self._initialize_client(self.hub)
    # ------------------------------------

    def getClientGateway(self, client_name):
        if self.findSocket( client_name ) != False:
            return self._listener.getsockname()[0]
        elif client_name in self.clients_ledger:
            return self.clients_ledger[ client_name ][ 'gateway' ]

        raise ClientOfflineException
    # ------------------------------------

    def getUsernameThroughID( self, id ):
        for socket, info in self.connections_information.items():
            try:
                if "{}".format( info[ "id" ] ) == id:
                    return info[ "username" ]
            except KeyError:
                pass
        raise UserValidationFailedException
    # -------------------------------------