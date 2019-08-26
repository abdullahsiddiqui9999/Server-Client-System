from DiscreteMessageHandlingServer import DiscreteMessageHandlingServer
import base64


class SimpleServer(DiscreteMessageHandlingServer):
    def __init__(self):
        DiscreteMessageHandlingServer.__init__(self)

    def process_discrete_message(self, socket, message):
        print(message)


ss = SimpleServer()
ss.bind_clients_listener('127.0.0.1', 27015)
ss.power_on()
