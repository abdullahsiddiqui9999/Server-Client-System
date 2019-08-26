from DiscreteMessageHandlingServer import DiscreteMessageHandlingServer
import socket, queue
from CustomExceptions import ClientOfflineException, UserValidationFailedException

class BasicServer( DiscreteMessageHandlingServer ):
    def __init__(self, max_num_clients, receiving_chunk_size, message_delimiter ):
        DiscreteMessageHandlingServer.__init__( self, max_num_clients, receiving_chunk_size, message_delimiter )
        self.clients_ledger = {}
        self.hub = socket.socket()

    # ------------------------------
    def processDiscreteMessage(self, socket, message):
        if socket is self.hub:
            self.handleMessageFromHub(message)
        else:
            message = message.strip( self.message_delimiter )
            if message.startswith("login_request".format( self.message_delimiter )):
                if self.authenticate( socket, message ):
                    self.sendMessage( socket, "{}{}{}".format(self.message_delimiter, self.sockets_info[ socket ][ 'id' ], self.message_delimiter) )
                    self.broadcastClient( socket )
                else:
                    self.sendMessage(socket, "{}{}{}".format(self.message_delimiter, '-1', self.message_delimiter))
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
            "{}new_client_alert\nName:{}\ngateway:{}{}".format( self.message_delimiter,
                                                                                 self.sockets_info[ socket ][ "username" ],
                                                                                 self.listener.getsockname()[0],
                                                                                 self.message_delimiter )
        self.message_queues[ self.hub ].put(broadcasting_message)
        if self.hub not in self.outputs:
            self.outputs.append( self.hub )
    # ------------------------------------

    def dropClient(self, socket):
        print( "Dropping {}!".format( self.sockets_info[ socket ][ 'username' ] ) )
        #-------------------------------------------------------------------------
        #Remove extra resources if allocated here!
        #------------------------------------------------------------------------
        DiscreteMessageHandlingServer.dropClient( self, socket )
    # ------------------------------------

    def authenticate(self, socket, request_message):
        try:
            header, username, password = request_message.split('\n')

            #Generate a key for this client.
            self.sockets_info[ socket ] = {
                'id' : DiscreteMessageHandlingServer.id,
                'username' : username,
            }
            return True
        except Exception:
            return False
    # ------------------------------------

    def connectToHub(self, host, port):
        self.hub.connect((host, port))
        self.initializeClient( self.hub )
    # ------------------------------------

    def getClientGateway(self, client_name):
        if self.findSocket( client_name ) != False:
            return self.listener.getsockname()[0]
        elif client_name in self.clients_ledger:
            return self.clients_ledger[ client_name ][ 'gateway' ]

        raise ClientOfflineException
    # ------------------------------------

    def getUsernameThroughID( self, id ):
        for socket, info in self.sockets_info.items(  ):
            try:
                if "{}".format( info[ "id" ] ) == id:
                    return info[ "username" ]
            except KeyError:
                pass
        raise UserValidationFailedException
    # -------------------------------------