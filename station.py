from single_threaded_multi_client_server import SingleThreadedMultiClientServer


class Station(SingleThreadedMultiClientServer):
    def __init__(self, host, port):
        SingleThreadedMultiClientServer.__init__(self, host, port)

    def process_message(self, connection, message):
        print(message)

        # SAY HI!
        self.append_message_to_sending_queue(connection, 'lighton')

    def perform_handshake_return_client_information(self, client_connection):
        data = client_connection.recv(SingleThreadedMultiClientServer.RECEIVING_NUM_OF_BYTES).decode()
        print(data)
        return {
            'name': data.split(':')[1]
        }
