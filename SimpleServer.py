from DiscreteMessageHandlingServer import DiscreteMessageHandlingServer
import base64


class SimpleServer(DiscreteMessageHandlingServer):
    def __init__(self):
        DiscreteMessageHandlingServer.__init__(self)

    def process_discrete_message(self, socket, message):
        decoded_content = base64.b64decode(message.encode())
        image_result = open('image_received.jpg', 'wb')
        image_result.write(decoded_content)
        image_result.close()
        print("File written!")


ss = SimpleServer()
ss.bind_clients_listener('127.0.0.1', 27015)
ss.power_on()
