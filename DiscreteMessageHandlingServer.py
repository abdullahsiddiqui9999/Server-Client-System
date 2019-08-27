from ServerCore import ServerCore


class DiscreteMessageHandlingServer(ServerCore):
    def __init__(self):
        ServerCore.__init__(self)

    def process_message(self, connection, message):
        self.process_discrete_message(connection, message)

    def process_discrete_message(self, socket, message):
        raise NotImplementedError
