from single_threaded_multi_client_server import SingleThreadedMultiClientServer
from custom_exceptions import HandshakeOutOfSyncException
from custom_exceptions import UnknownClientException
from custom_exceptions import UnknownSlaveException

class Station(SingleThreadedMultiClientServer):
    def __init__(self, host, port):
        SingleThreadedMultiClientServer.__init__(self, host, port)

    def process_message(self, connection, message):
        print(message)

    def perform_handshake_return_client_information(self, connection):
        # Get type of client.
        # Either SLAVE or CLIENT
        received_message = connection.recv(SingleThreadedMultiClientServer.RECEIVING_NUM_OF_BYTES).decode()

        # Here message should be like:
        # "SLAVE|<SLAVE_IDENTIFICATION_NUM>" or
        # "CLIENT|<USERNAME>|<PASSWORD>"

        splitted_message = received_message.split('|')
        try:
            if splitted_message[0] == "SLAVE":
                # splitted_message[1] corresponds to slave_identification_number
                connection_info = self._complete_handshake_with_slave(connection, splitted_message[1])
            elif splitted_message[0] == "CLIENT":
                # splitted_message[1] and splitted_message[1] corresponds to client_username and client_password respectively
                connection_info = self._complete_handshake_with_client(connection, splitted_message[1], splitted_message[2])
            else:
                raise HandshakeOutOfSyncException
        except IndexError:
            raise HandshakeOutOfSyncException

        return connection_info

    # ------------------ PROTECTED FUNCTIONS --------------------
    def _complete_handshake_with_slave(self, slave_connection, slave_identification_number):
        self._authenticate_slave(slave_identification_number)

        # Get info about elements present on the board
        # Message should be in the format like.
        # "BOARD_INFORMATION\n
        # COUNT|<COUNT OF INSTALLED GADGETS>\n
        # <NAME OF GADGET>|<TYPE>|<IDENTIFICATION_NUMBER>\n
        # <NAME OF GADGET>|<TYPE>|<IDENTIFICATION_NUMBER>"

        received_message = slave_connection.recv(SingleThreadedMultiClientServer.RECEIVING_NUM_OF_BYTES).decode()

        splitted_message = received_message.split('\n')

        try:
            if splitted_message[0] == 'BOARD_INFORMATION':
                count_of_gadgets = int(splitted_message.split('|')[1])
            else:
                raise HandshakeOutOfSyncException
        except IndexError:
            raise HandshakeOutOfSyncException
        except TypeError:
            raise HandshakeOutOfSyncException
        pass

    def _complete_handshake_with_client(self, client_connection, client_username, client_password):
        pass

    def _authenticate_slave(self, slave_identification_number):
        # Or raise UnknownSlaveException
        pass

    def _authenticate_client(self, client_username, client_password):
        # Or raise UnknownClientException
        pass
