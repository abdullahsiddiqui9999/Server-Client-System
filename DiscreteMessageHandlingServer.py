from ServerCore import ServerCore


class DiscreteMessageHandlingServer(ServerCore):
    def __init__(self):
        ServerCore.__init__(self)

    def process_message(self, socket, message):
        self.process_discrete_message(socket, message)

    def process_discrete_message(self, socket, message):
        raise NotImplementedError
