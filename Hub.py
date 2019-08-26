from DiscreteMessageHandlingServer import DiscreteMessageHandlingServer

class Hub ( DiscreteMessageHandlingServer ):
    def __init__(self, max_num_clients, receiving_buffer_size, message_delimiter):
        DiscreteMessageHandlingServer.__init__(self, max_num_clients, receiving_buffer_size, message_delimiter)
        self.clients_ledger = {}

    def drop_client(self, socket):
        gateway_of_dropping_server = socket.getsocketname()[0]
        for client_name, gateway in self.clients_ledger.items():
            if gateway == gateway_of_dropping_server:
                del self.clients_ledger[ client_name ]

        DiscreteMessageHandlingServer.drop_client(self, socket)

    def broadcastClient(self, sender_socket , client_name, gateway ):
        broadcasting_message = "{}new_client_alert\nName:{}\nServer gateway:{}{}".format( self.message_delimiter, client_name, gateway, self.message_delimiter )
        for socket in self.inputs:
            if sender_socket != socket:
                self.append_message_to_sending_queue(socket, broadcasting_message)

    def storeClientInLedger (self, notification):
        notification, name, server_ip = notification.split( '\n' )
        name = name.split( ':' )[1]
        server_ip = server_ip.split( ':' )[1]
        try:
            self.clients_ledger[name ]
            self.clients_ledger[ name ] = server_ip #Over write!
        except KeyError:
            print( "New client!" )
            self.clients_ledger[ name ] = server_ip

        print( "{} is online at {}".format( name, server_ip ) )
        return name, server_ip

    def process_discrete_message(self, socket, message):
        if message.startswith('new_client_alert'):
            client_name, server_ip = self.storeClientInLedger( message )
            self.broadcastClient(socket, client_name, server_ip)


