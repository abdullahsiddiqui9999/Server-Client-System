import select
import socket
import queue


class ServerCore:
    client_id = 0

    MESSAGE_DELIMITER = '$'
    MAXIMUM_NUM_OF_CLIENTS = 10
    RECEIVING_NUM_OF_BYTES = 1024 * 10

    ADJACENT_MESSAGES_SEPARATOR = MESSAGE_DELIMITER + MESSAGE_DELIMITER

    EXCEPTIONS_TO_BE_CAUGHT_DURING_SENDING = (
        ConnectionAbortedError,
        ConnectionResetError,
        BlockingIOError
    )

    EXCEPTIONS_TO_BE_CAUGHT_DURING_RECEIVING = (
        ConnectionResetError,
        OSError
    )

    def __init__(self):
        # inputs, outputs are the arrays which will contain the sockets in which either the data is to be written or fetched from.
        self._inputs = []
        self._outputs = []

        # messages queues contain data which is to be sent through the socket
        # self.messages_queues[socket_object] gives the data which is to be sent.
        self._message_queues = {}

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
        self._sockets_incomplete_messages = {}

        self._listener = socket.socket()

    def bind_clients_listener(self, host, port):
        self._listener.bind((host, port))

    def power_on(self):
        self._listener.listen(ServerCore.MAXIMUM_NUM_OF_CLIENTS)
        self._listener.setblocking(False)
        self._inputs.append(self._listener)

        print("Listening to client on: {}".format(self._listener.getsockname()))

        while self._inputs:
            readable, writable, exceptional = select.select(
                self._inputs, self._outputs, self._inputs)

            for connection in readable:
                if connection is self._listener:
                    client_socket, client_address = connection.accept()
                    self._initialize_client(client_socket)
                else:
                    self._process_received_data(connection)

            for connection in writable:
                self._send_data_through_socket(connection)

            for connection in exceptional:
                self._drop_client(connection)

    def _process_received_data(self, connection):
        try:
            received_data = connection.recv(ServerCore.RECEIVING_NUM_OF_BYTES).decode()
            if not received_data:
                raise ConnectionAbortedError
        except ServerCore.EXCEPTIONS_TO_BE_CAUGHT_DURING_RECEIVING:
            self._drop_client(connection)
        else:
            received_data = self._sockets_incomplete_messages[connection] + received_data

            # clear the incomplete message after prepending its data to the received data
            self._sockets_incomplete_messages[connection] = ""

            # messages will be array of splitted messages.
            messages = received_data.split(ServerCore.ADJACENT_MESSAGES_SEPARATOR)

            # get the last message and check if it also complete.
            last_message = messages.pop()

            for message in messages:
                self.process_message(connection, message.strip(ServerCore.MESSAGE_DELIMITER))

            # if the last_message ends with a delimiter this means that it is a complete message
            # else not and some of its part will come in the next message.
            if last_message.endswith(ServerCore.MESSAGE_DELIMITER):
                self.process_message(connection, last_message.strip(ServerCore.MESSAGE_DELIMITER))
            else:
                self._sockets_incomplete_messages[connection] = last_message

    def process_message(self, connection, message):
        raise NotImplementedError

    def _initialize_client(self, connection):
        connection.setblocking(False)

        print("A client connected from {}".format(connection.getpeername()))
        self._inputs.append(connection)
        self._message_queues[connection] = queue.Queue()
        self._sockets_incomplete_messages[connection] = ""
        self.connections_information[connection] = {}
        ServerCore.client_id += 1

    def _send_data_through_socket(self, connection):
        try:
            next_msg = self._message_queues[connection].get_nowait()
        except queue.Empty:
            self._outputs.remove(connection)
        else:
            # During sending catch different exceptions like ConnectionReset.
            # If any exception occurs, drop that client.
            try:
                connection.sendall(next_msg.encode())
            except ServerCore.EXCEPTIONS_TO_BE_CAUGHT_DURING_SENDING:
                self._drop_client(connection)

    def append_message_to_sending_queue(self, recipient_connection, message):
        message = ServerCore.MESSAGE_DELIMITER + message + ServerCore.MESSAGE_DELIMITER
        self._message_queues[recipient_connection].put(message)
        if recipient_connection not in self._outputs:
            self._outputs.append(recipient_connection)

    def send_immediate(self, recipient_connection, message):
        self.append_message_to_sending_queue(recipient_connection, message)
        self._send_data_through_socket(recipient_connection)

    def _drop_client(self, connection):
        self._remove_resources(connection)
        connection.close()

    def _remove_resources(self, connection):
        print("Removing: {}".format(connection.getpeername()))
        if connection in self._outputs:
            self._outputs.remove(connection)
        self._inputs.remove(connection)
        del self.connections_information[connection]
        del self._message_queues[connection]
        del self._sockets_incomplete_messages[connection]
