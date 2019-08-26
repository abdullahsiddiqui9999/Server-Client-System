import select
import socket
import queue


class ServerCore:
    client_id = 0

    MESSAGE_DELIMITER = '$'
    MAXIMUM_NUM_OF_CLIENTS = 10
    RECEIVING_NUM_OF_BYTES = 1024 * 10

    ADJACENT_MESSAGES_SEPARATOR = MESSAGE_DELIMITER + MESSAGE_DELIMITER

    EXCEPTIONS_TO_BE_CAUGHT_DURING_SENDING = [
        ConnectionResetError,
        BlockingIOError
    ]

    EXCEPTIONS_TO_BE_CAUGHT_DURING_RECEIVING = [
        ConnectionResetError,
        OSError
    ]

    def __init__(self):
        # inputs, outputs are the arrays which will contain the sockets in which either the data is to be written or fetched from.
        self.inputs = []
        self.outputs = []

        # messages queues contain data which is to be sent through the socket
        # self.messages_queues[socket_object] gives the data which is to be sent.
        self.message_queues = {}

        # connection_information[socket_object] gives a dictionary which stores information of the client
        # which is connected to the socket.
        self.connections_information = {}

        # Case 1: When the application data is sent in bulk, many separate transport layer messages arrive at the same time and get stored in socket buffers adjacent
        # to one another. e.g.
        # "xyzxyzxyz" are three separate application layer messages present in the receiving buffer of socket if we consider xyz as a separate application layer message.

        # Case 2: Or if a very big file is sent over the socket then it arrives in parts at the receiving end. Therefore we must buffer the file data until
        # whole file is received.

        # "abcde" , "fghij" can be considered 2 different transport layer messages of the same app layer message if we consider "abcdefghij" as a single
        # application layer message.

        # What we do is we surround the application layer message with a special character called "message_delimiter"
        # and partition the data on 2 adjacent delimiters on the receiving end.
        # e.g. "$abc$$abc$" we can split the data on "$$" to get 2 separate app layer messages.

        # It contains data of which some part is yet to be received.
        self.sockets_incomplete_messages = {}

        self.listener = socket.socket()

    def bind_clients_listener(self, host, port):
        try:
            self.listener.bind((host, port))
        except socket.error:
            print("Unable to bind server with specified host and port!")

    def initialize_client(self, socket):
        socket.setblocking(False)

        print("A client connected from {}".format(socket.getpeername()))
        self.inputs.append(socket)
        self.message_queues[socket] = queue.Queue()
        self.sockets_incomplete_messages[socket] = ""
        self.connections_information[socket] = {}
        ServerCore.client_id += 1

    def power_on(self):
        self.listener.listen(ServerCore.MAXIMUM_NUM_OF_CLIENTS)
        self.listener.setblocking(False)
        self.inputs.append(self.listener)

        print("Listening to client on: {}".format(self.listener.getsockname()))

        while self.inputs:
            readable, writable, exceptional = select.select(
                self.inputs, self.outputs, self.inputs)

            for sock in readable:
                if sock is self.listener:
                    client_socket, client_address = sock.accept()
                    self.initialize_client(client_socket)
                else:
                    self.process_received_data(sock)

            for sock in writable:
                self.send_data_through_socket(sock)

            for sock in exceptional:
                print('asdad')
                self.drop_client(sock)

    def send_data_through_socket(self, socket):
        try:
            next_msg = self.message_queues[socket].get_nowait()
        except queue.Empty:
            self.outputs.remove(socket)
        else:
            # During sending catch different exceptions like ConnectionReset.
            # If any exception occurs, drop that client.
            try:
                socket.sendall(next_msg.encode())
            except zip(*ServerCore.EXCEPTIONS_TO_BE_CAUGHT_DURING_SENDING):
                self.drop_client(socket)

    def process_received_data(self, socket):
        try:
            received_data = socket.recv(ServerCore.RECEIVING_NUM_OF_BYTES).decode()
            if not received_data:
                self.drop_client(socket)
                return
        except zip(*ServerCore.EXCEPTIONS_TO_BE_CAUGHT_DURING_RECEIVING):
            self.drop_client(socket)
        else:
            received_data = self.sockets_incomplete_messages[socket] + received_data

            # clear the incomplete message after prepending its data to the received data
            self.sockets_incomplete_messages[socket] = ""

            # messages will be array of splitted messages.
            messages = received_data.split(ServerCore.ADJACENT_MESSAGES_SEPARATOR)

            # get the last message and check if it also complete.
            last_message = messages.pop()

            for message in messages:
                self.process_message(socket, message.strip(ServerCore.MESSAGE_DELIMITER))

            # if the last_message ends with a delimiter this means that it is a complete message
            # else not and some of its part will come in the next message.
            if last_message.endswith(ServerCore.MESSAGE_DELIMITER):
                self.process_message(socket, last_message.strip(ServerCore.MESSAGE_DELIMITER))
            else:
                self.sockets_incomplete_messages[socket] = last_message

    def process_message(self, socket, message):
        raise NotImplementedError

    def drop_client(self, socket):
        self.remove_resources(socket)
        socket.close()

    def remove_resources(self, socket):
        print("Removing: {}".format(socket.getpeername()))
        if socket in self.outputs:
            self.outputs.remove(socket)
        self.inputs.remove(socket)
        del self.connections_information[socket]
        del self.message_queues[socket]
        del self.sockets_incomplete_messages[socket]

    def append_message_to_sending_queue(self, recipient_socket, message):
        message = ServerCore.MESSAGE_DELIMITER + message + ServerCore.MESSAGE_DELIMITER
        self.message_queues[recipient_socket].put(message)
        if recipient_socket not in self.outputs:
            self.outputs.append(recipient_socket)

    def send_immediate(self, recipient_socket, message):
        self.append_message_to_sending_queue(recipient_socket, message)
        self.send_data_through_socket(recipient_socket)
