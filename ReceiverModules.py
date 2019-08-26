import threading, base64, cv2
import socket
import numpy as np
from CustomExceptions import TerminateReceivingThreadException


class Receiver:
    def __init__(self, sock, receiving_chunk_size, message_delimiter ):
        self.socket = sock
        self.buffer = ""
        self.receiving_chunk_size = receiving_chunk_size
        self.message_delimiter = message_delimiter
        self.trailing_data = ""
        self.stop_receiving = False

    def startReceiving(self):
        self.socket.setblocking( 1 ) #Make socket blocking.

        while not self.stop_receiving:
            try:
                data = self.socket.recv( self.receiving_chunk_size ).decode()
                data = self.trailing_data + data
            except ConnectionResetError:
                print("Connection down!")
                break
            except ConnectionAbortedError:
                print("Connection down!")
                break
            except OSError:
                print("Connection down!")
                break

            if data:
                data = self.partitionData( data )

                if data.endswith('{}'.format(self.message_delimiter)):
                    is_complete_message = True
                    data = self.buffer + data
                    self.buffer = ""
                else:
                    self.buffer += data
                    is_complete_message = False

                if is_complete_message:
                    data = data.strip(self.message_delimiter)
                    try:
                        self.processReceivedMessage( data )
                    except TerminateReceivingThreadException:
                        break
            else:
                self.socket.close()
                break

    def stopReceiving(self):
        self.socket.close()
        self.stop_receiving = True

    def processReceivedMessage(self, data):
        raise NotImplementedError

    def partitionData(self, data ):
        index_of_first_interleaving_message = data.find("{}{}".format( self.message_delimiter, self.message_delimiter )  )
        if index_of_first_interleaving_message != -1:
            current_message = data[: index_of_first_interleaving_message + 1]
            trailing_data = data[index_of_first_interleaving_message + 1:]
            self.trailing_data = trailing_data
            data = current_message
        else:
            self.trailing_data = ""
        return data

class MessagesReceiver( Receiver ):
    def __init__( self, sock, receiving_chunk_size, message_delimiter ):
        Receiver.__init__( self, sock, receiving_chunk_size, message_delimiter )

    def processReceivedMessage(self, data):
        to, from_, content = data.split( '\n' )
        print( "{} says: {}".format( from_, content ) )

class VideoReceiver( Receiver ):
    def __init__( self, sock, receiving_chunk_size, message_delimiter, sender ):
        Receiver.__init__( self, sock, receiving_chunk_size, message_delimiter )
        self.sender = sender


    def processReceivedMessage(self, data):
        try:
            decoded_content = base64.b64decode( data.encode() )
            cv2.namedWindow( self.sender )
            received_image = np.fromstring( decoded_content , dtype=np.uint8)
            received_image = cv2.imdecode( received_image, 1 )
            cv2.imshow( self.sender , received_image )
            cv2.waitKey( 40 )

        except base64.binascii.Error:
            print("Something went wrong in decoding!")

class FileReceiver( Receiver ):
    def __init__( self, sock, receiving_chunk_size, message_delimiter, sender ):
        Receiver.__init__( self, sock, receiving_chunk_size, message_delimiter )
        self.sender = sender


    def processReceivedMessage(self, data):
        try:
            decoded_content = base64.b64decode( data.encode() )
            image_result = open('image_received.jpg', 'wb')
            image_result.write( decoded_content )
            image_result.close()
            print( "File written!" )

        except base64.binascii.Error:
            print("Something went wrong in decoding!")

class FileReceivingModule( threading.Thread, FileReceiver ):
    def __init__(self, sock, receiving_chunk_size, message_delimiter, sender):
        threading.Thread.__init__( self )
        FileReceiver.__init__( self, sock, receiving_chunk_size, message_delimiter, sender )

    def run(self):
        FileReceiver.startReceiving( self )

class MessagesReceivingModule(threading.Thread, MessagesReceiver):
    def __init__(self, sock, receiving_chunk_size, message_delimiter):
        threading.Thread.__init__( self )
        MessagesReceiver.__init__( self, sock, receiving_chunk_size, message_delimiter )

    def run(self):
        MessagesReceiver.startReceiving( self )

class VideoReceivingModule( threading.Thread, VideoReceiver ):
    def __init__(self, sock, receiving_chunk_size, message_delimiter, sender):
        threading.Thread.__init__( self )
        VideoReceiver.__init__( self, sock, receiving_chunk_size, message_delimiter, sender )

    def run(self):
        VideoReceiver.startReceiving( self )


class IncomingCallHandler( Receiver ):
    def __init__(self, conn_receiver_module, sock, receiving_chunk_size, message_delimiter):
        Receiver.__init__( self, sock, receiving_chunk_size, message_delimiter )
        self.conn_receiver_module = conn_receiver_module
        self.caller = None
        self.type_of_call = None

    def processReceivedMessage(self, data):
        if data.startswith( 'incoming_call' ):
            header, recipient, caller, type_of_call = data.split( '\n' )
            print( "{} is trying to connect with you via {}".format( caller, type_of_call ) )
            self.caller = caller
            self.type_of_call = type_of_call
            self.conn_receiver_module.caller = caller
            self.conn_receiver_module.type_of_call = type_of_call
        elif data.startswith( 'tone' ):
            print( "Ring Ring! {} is {} calling you!".format( self.caller, self.type_of_call ) )
        elif data.startswith( 'connected' ):
            print( "Connected" )
            raise TerminateReceivingThreadException

class IncomingCallHandlerModule( threading.Thread, IncomingCallHandler ):
    def __init__(self, connection_receiver_module_pointer, sock, receiving_chunk_size, message_delimiter):
        threading.Thread.__init__(self)
        IncomingCallHandler.__init__(self, connection_receiver_module_pointer, sock, receiving_chunk_size, message_delimiter)

    def run(self):
        IncomingCallHandler.startReceiving(self)

class IncomingConnectionReceiver:
    def __init__(self, host, port, message_delimiter):
        self.listener = self.bind_listener( host, port )
        self.message_delimiter = message_delimiter
        self.caller = None
        self.type_of_call = None

    def bind_listener(self, host, port):
        listener = socket.socket()
        listener.bind( ( host, port ) )
        listener.listen( 1 )
        return listener

    def startListening(self):
        while True:
            incoming_connection, address = self.listener.accept()

            incoming_call_handler_module = IncomingCallHandlerModule( self, incoming_connection, 1024, self.message_delimiter )
            incoming_call_handler_module.start()

            decision_set = [ 'accept', 'decline' ]
            decision = None
            is_call_rejected = False

            while decision not in decision_set:
                decision = input( "Please enter your decision: ( accept/decline )\t" )

                if decision == "accept":
                    incoming_connection.sendall( '{}ACCEPTED{}'.format( self.message_delimiter, self.message_delimiter ).encode() )
                elif decision == 'decline':
                    incoming_connection.sendall(  '{}REJECTED{}'.format( self.message_delimiter, self.message_delimiter ).encode() )
                    is_call_rejected = True
                else:
                    print( "Bad decision, please try again." )


            print( "Waiting for incoming call thread to join!" )
            incoming_call_handler_module.join()

            if not is_call_rejected:
                if self.type_of_call == 'video':
                    video_receiver_module = FileReceivingModule( incoming_connection, 51200, self.message_delimiter, self.caller )
                    video_receiver_module.start()

                    decision_set = ['stop']
                    decision = None
                    while decision not in decision_set:
                        decision = input("Type 'stop' to stop video chat. ")

                        if decision == "stop":
                            video_receiver_module.stopReceiving()
                        else:
                            print("Bad decision, please try again.")

                    video_receiver_module.join()
                    print( "Stopped video chat!" )
                else:
                    print( 'Bad call type!' )
            else:
                print( 'Call rejected!' )

class IncomingConnectionReceivingAndCallingModule(threading.Thread, IncomingConnectionReceiver):
    def __init__(self, host, port, message_delimiter):
        threading.Thread.__init__( self )
        IncomingConnectionReceiver.__init__( self, host, port, message_delimiter )

    def run(self):
        IncomingConnectionReceiver.startListening( self )




