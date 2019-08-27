from ServerCore import ServerCore

class ContinuousMessageHandlingServer( ServerCore ):
    def __init__(self, max_num_clients, receiving_buffer_size, message_delimiter):
        ServerCore.__init__(self, max_num_clients, receiving_buffer_size, message_delimiter)


    def _process_received_data(self, connection):
        try:
            data = connection.recv(self.receiving_chunk_size).decode()
        except ConnectionResetError:
            self._drop_client(connection)
            return
        except OSError:
            self._drop_client(connection)
            return

        if data:
            self.process_message(connection, data)
        else:
            self._drop_client(connection)