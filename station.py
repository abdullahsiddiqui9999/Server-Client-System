from single_threaded_multi_client_server import SingleThreadedMultiClientServer


class Station(SingleThreadedMultiClientServer):
    def __init__(self):
        SingleThreadedMultiClientServer.__init__(self)

    def process_message(self, connection, message):
        print(message)

