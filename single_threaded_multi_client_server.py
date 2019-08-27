import select
import socket
import queue
import threading

class SingleThreadedMultiClientServer:
    client_id = 0

    MESSAGE_DELIMITER = '$'
    MAXIMUM_NUM_OF_CLIENTS = 10
    RECEIVING_NUM_OF_BYTES = 1024 * 10
    LOOP_BACK_RECEIVING_NUM_OF_BYTES = 1

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

    def __init__(self, host, port):
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

        # Make initializing client method thread safe as it will be called by other threads too.
        # specially from AsyncHandshakeModule
        self._initialize_client_mutex = threading.Semaphore(1)

        # When _inputs, _outputs, _messages_queues, and other data are in use don't let them change
        # by other methods of this class as other methods can also be called from separate threads.
        self._thread_sensitive_data_in_use_mutex = threading.Semaphore(1)

        # __loop_back_connection is the connection which is formed with the self._listener
        # The purpose of keeping it is when the main thread is stuck at "select" statement
        # and meanwhile we add some connections into _inputs and _outputs from another thread
        # (which will be AsyncHandshakeModule usually).
        self.__loop_back_connection = socket.socket()
        self.__loop_back_connection_reading_end = None

        self.host = host
        self.port = port
        # bind listener
        self._listener.bind((self.host, self.port))

    def power_on(self):
        self._listener.listen(SingleThreadedMultiClientServer.MAXIMUM_NUM_OF_CLIENTS)
        self._listener.setblocking(False)
        self._inputs.append(self._listener)

        # connect loop back connection to the listener
        self.__loop_back_connection.connect((self.host, self.port))

        print("Listening to client on: {}".format(self._listener.getsockname()))

        while self._inputs:
            readable, writable, exceptional = select.select(
                self._inputs, self._outputs, self._inputs)

            # Acquire mutex
            self._thread_sensitive_data_in_use_mutex.acquire()

            for connection in readable:
                if connection is self._listener:
                    client_socket, client_address = connection.accept()

                    # Check if it the first client connected, because it will be of loop back connection.
                    if SingleThreadedMultiClientServer.client_id == 0:
                        self._initialize_loop_back_connection_reading_end(client_socket)
                    else:
                        AsyncHandshakeModule(self, client_socket).start()

                elif connection is self.__loop_back_connection_reading_end:
                    self.__loop_back_connection_reading_end.recv(SingleThreadedMultiClientServer.LOOP_BACK_RECEIVING_NUM_OF_BYTES)  # Flush
                else:
                    self._process_received_data(connection)

            for connection in writable:
                self._send_data_through_socket(connection)

            for connection in exceptional:
                self.drop_client(connection)

            # Release mutex
            self._thread_sensitive_data_in_use_mutex.release()

    def process_message(self, connection, message):
        raise NotImplementedError

    def append_message_to_sending_queue(self, recipient_connection, message):
        message = SingleThreadedMultiClientServer.MESSAGE_DELIMITER + message + SingleThreadedMultiClientServer.MESSAGE_DELIMITER

        # Python queues are already thread safe.
        self._message_queues[recipient_connection].put(message)

        self._thread_sensitive_data_in_use_mutex.acquire()
        if recipient_connection not in self._outputs:
            self._outputs.append(recipient_connection)
        self._thread_sensitive_data_in_use_mutex.release()

    def initialize_client(self, connection, connection_information={}):
        self._initialize_client_mutex.acquire()
        self._thread_sensitive_data_in_use_mutex.acquire()

        connection.setblocking(False)

        print("A client connected from {}".format(connection.getpeername()))
        self._inputs.append(connection)
        self._message_queues[connection] = queue.Queue()
        self._sockets_incomplete_messages[connection] = ""
        self.connections_information[connection] = connection_information
        SingleThreadedMultiClientServer.client_id += 1

        # send this to trigger select.
        self._trigger_select()

        self._thread_sensitive_data_in_use_mutex.release()
        self._initialize_client_mutex.release()

    # This method is called by AsyncHandshakeModule from a separate thread as a callback.
    # CAUTION: be thread-safe.
    # This method is expected to be orridden by the child class and add custom data receiving logic in it.
    def perform_handshake_return_client_information(self, client_connection):
        """This method should return a dictionary which will be stored
        against connections_information[client_connection]
        CAUTION: Don't try to change any attribute of this class in attribute"""
        raise NotImplementedError

    def drop_client(self, connection, is_called_from_main_thread=True):
        if not is_called_from_main_thread:
            self._thread_sensitive_data_in_use_mutex.acquire()

        self._remove_resources(connection)
        connection.close()

        if not is_called_from_main_thread:
            self._thread_sensitive_data_in_use_mutex.release()

    # ---------------------------------------------------------
    #                   PROTECTED FUNCTIONS
    # ---------------------------------------------------------

    def _process_received_data(self, connection):
        try:
            received_data = connection.recv(SingleThreadedMultiClientServer.RECEIVING_NUM_OF_BYTES).decode()
            if not received_data:
                raise ConnectionAbortedError
        except SingleThreadedMultiClientServer.EXCEPTIONS_TO_BE_CAUGHT_DURING_RECEIVING:
            self.drop_client(connection)
        else:
            received_data = self._sockets_incomplete_messages[connection] + received_data

            # clear the incomplete message after prepending its data to the received data
            self._sockets_incomplete_messages[connection] = ""

            # messages will be array of splitted messages.
            messages = received_data.split(SingleThreadedMultiClientServer.ADJACENT_MESSAGES_SEPARATOR)

            # get the last message and check if it also complete.
            last_message = messages.pop()

            for message in messages:
                self.process_message(connection, message.strip(SingleThreadedMultiClientServer.MESSAGE_DELIMITER))

            # if the last_message ends with a delimiter this means that it is a complete message
            # else not and some of its part will come in the next message.
            if last_message.endswith(SingleThreadedMultiClientServer.MESSAGE_DELIMITER):
                self.process_message(connection, last_message.strip(SingleThreadedMultiClientServer.MESSAGE_DELIMITER))
            else:
                self._sockets_incomplete_messages[connection] = last_message

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
            except SingleThreadedMultiClientServer.EXCEPTIONS_TO_BE_CAUGHT_DURING_SENDING:
                self.drop_client(connection)

    def _initialize_loop_back_connection_reading_end(self, loop_back_reading_end_connection):
        self._inputs.append(loop_back_reading_end_connection)
        self.__loop_back_connection_reading_end = loop_back_reading_end_connection
        SingleThreadedMultiClientServer.client_id += 1

    def _trigger_select(self):
        # Sending a dummy message through the loop back connection
        # will generate the system call that will trigger select.
        self.__loop_back_connection.send(' '.encode())

    def _remove_resources(self, connection):
        print("Removing: {}".format(connection.getpeername()))
        if connection in self._outputs:
            self._outputs.remove(connection)
        self._inputs.remove(connection)
        del self.connections_information[connection]
        del self._message_queues[connection]
        del self._sockets_incomplete_messages[connection]


class AsyncHandshakeModule(threading.Thread):
    def __init__(self, parent_sv, client_connection):
        threading.Thread.__init__(self)
        self.parent_sv = parent_sv
        self.client_connection = client_connection

    def run(self):
        self.client_connection.setblocking(True)

        # Get a dictionary containing user data.
        client_connection_information = self.parent_sv.perform_handshake_return_client_information(self.client_connection)

        self.parent_sv.initialize_client(self.client_connection, client_connection_information)
