from single_threaded_multi_client_server import SingleThreadedMultiClientServer


class Station(SingleThreadedMultiClientServer):
    def __init__(self, host, port):
        SingleThreadedMultiClientServer.__init__(self, host, port)

    def process_message(self, connection, message):
        print(message)

    def perform_handshake_return_client_information(self, client_connection):
        return {}
