from ServerCore import ServerCore


class SimpleServer(ServerCore):
    def __init__(self):
        ServerCore.__init__(self)

    def process_message(self, connection, message):
        print(message)


ss = SimpleServer()
ss.bind_clients_listener('127.0.0.1', 27015)
ss.power_on()
