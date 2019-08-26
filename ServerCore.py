import  select, socket, queue, time

class ServerCore:
    id = 0

    def __init__(self, max_num_clients, receiving_chunk_size, message_delimiter ):
        self.inputs = []
        self.outputs = []
        self.message_queues = {}
        self.listener = socket.socket()
        self.max_num_clients = max_num_clients
        self.receiving_chunk_size = receiving_chunk_size
        self.socket_trailing_data = {}
        self.sockets_info = {}
        self.socket_buffers = {}
        self.message_delimiter = message_delimiter

    def bind_clients_listener(self, host, port):
        try:
            self.listener.bind((host, port))
        except socket.error:
            print( "Unable to bind server with specified host and port! ( For local clients )" )
            return

    def initializeClient(self, socket):
        socket.setblocking(0)

        print("A client connected from {}".format( socket.getpeername() ))
        self.inputs.append(socket)
        self.message_queues[socket] = queue.Queue()
        self.socket_trailing_data[socket] = ""
        self.socket_buffers[ socket ] = ""
        self.sockets_info[ socket ] = {}
        ServerCore.id += 1

    def power_on(self):
        self.listener.listen(self.max_num_clients)
        self.listener.setblocking(0)
        self.inputs.append(self.listener)

        print( "Listening to client on: {}".format(self.listener.getsockname()))

        while self.inputs:
            try:
                readable, writable, exceptional = select.select(
                    self.inputs, self.outputs, self.inputs )
                for sock in readable:
                    if sock is self.listener:
                        connection, client_address = sock.accept()
                        self.initializeClient(connection)
                    else:
                        try:
                            self.processReceivedData(sock)
                        except KeyError:
                            pass

                for sock in writable:
                    try:
                        next_msg = self.message_queues[sock].get_nowait()
                    except queue.Empty:
                        self.outputs.remove(sock)
                    except KeyError:
                        pass
                    else:
                        try:
                            sock.sendall(next_msg.encode())
                        except BlockingIOError:
                            print("Blocking IO error occurred!")
                        except ConnectionResetError:
                            print("Connection reset error occurred!")
                            self.dropClient(sock)

                for sock in exceptional:
                    self.dropClient(sock)
            except ValueError:
                print( "Value error occurred!" )
                for input_socket in self.inputs:
                    if input_socket.fileno() == -1:
                        if socket in self.outputs:
                            self.outputs.remove(socket)
                        self.inputs.remove(input_socket)
                        del self.sockets_info[input_socket]
                        del self.message_queues[input_socket]
                        del self.socket_trailing_data[input_socket]
                        del self.socket_buffers[input_socket]


    def flushSocketData( self, sock ):
        print( "Flushing data!" )
        while True:
            try:
                next_msg = self.message_queues[sock].get_nowait()
            except queue.Empty:
                break
            except KeyError:
                break
            else:
                try:
                    sock.sendall(next_msg.encode())
                except BlockingIOError:
                    pass
                except ConnectionResetError:
                    break

    def processReceivedData(self, socket):
        try:
            data = socket.recv(self.receiving_chunk_size).decode()
            data = self.socket_trailing_data[ socket ] + data
        except ConnectionResetError:
            self.dropClient( socket )
            return
        except OSError:
            self.dropClient( socket )
            return

        if data:
            while True:
                message = self.partitionData( socket, data )

                self.processMessage( socket, message )

                count_of_delimiter = self.socket_trailing_data[ socket ].count( self.message_delimiter )
                if count_of_delimiter < 2:
                    break
                data = self.socket_trailing_data[ socket ]
        else:
            self.dropClient( socket )

    def processMessage(self, socket, message):
        raise NotImplementedError

    def partitionData(self, socket, data ):
        index_of_first_interleaving_message = data.find("{}{}".format( self.message_delimiter, self.message_delimiter )  )
        if index_of_first_interleaving_message != -1:
            current_message = data[: index_of_first_interleaving_message + 1]
            trailing_data = data[index_of_first_interleaving_message + 1:]
            self.socket_trailing_data[socket] = trailing_data
            data = current_message
        else:
            self.socket_trailing_data[socket] = ""

        return data

    def dropClient(self, socket):
        self.removeResources( socket )
        socket.close()

    def removeResources(self, socket):
        print( "Removing: {}".format( socket.getpeername() ) )
        if socket in self.outputs:
            self.flushSocketData( socket )
            self.outputs.remove(socket)
        self.inputs.remove(socket)
        del self.sockets_info[socket]
        del self.message_queues[socket]
        del self.socket_trailing_data[socket]
        del self.socket_buffers[ socket ]

    def sendMessage(self, sendee_socket, message ):
        try:
            self.message_queues[sendee_socket].put( message )
            if sendee_socket not in self.outputs:
                self.outputs.append(sendee_socket)
        except KeyError:
            #KeyError occurs due to dropping of a client.
            pass
        return

    def findSocket(self, attribute_value, attribute_name ="username"):
        for socket, info in self.sockets_info.items():
            try:
                if info[attribute_name] == attribute_value:
                    return socket
            except KeyError:
                pass
        return False

    def getPort(self):
        return self.listener.getsockname()[ 1 ] #Port