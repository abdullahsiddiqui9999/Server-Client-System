from ServerCore import ServerCore

class ContinuousMessageHandlingServer( ServerCore ):
    def __init__(self, max_num_clients, receiving_buffer_size, message_delimiter):
        ServerCore.__init__(self, max_num_clients, receiving_buffer_size, message_delimiter)


    def process_received_data(self, socket):
        try:
            data = socket.recv(self.receiving_chunk_size).decode()
        except ConnectionResetError:
            self.drop_client(socket)
            return
        except OSError:
            self.drop_client(socket)
            return

        if data:
            self.process_message(socket, data)
        else:
            self.drop_client(socket)