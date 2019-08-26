import socket, select, queue, threading, base64, time, cv2
import numpy as np
from ReceiverModules import MessagesReceivingModule, IncomingConnectionReceivingAndCallingModule

class Client:
    def __init__( self, server_ip ):
        self.session_id = None
        self.username = None
        self.basic_server_socket = None
        self.server_ip = server_ip
        self.messaging_server_socket = None
        self.video_server_socket = None
        self.incoming_call_socket = None
        self.call_exchange_socket = None
        self.message_delimiter = '$'
        self.threads = []

        self.fps = 30
        self.compression_factor = 0.5

    def login(self):
        username = input( 'Username: ' )
        password = input( 'Password: ' )

        try:
            session_id, basic_server_socket = self.loginAttempt( username, password )
        except socket.error:
            print( "Cannot connect to basic server for authentication!" )
            return


        if session_id != -1:
            self.username = username
            self.session_id = session_id
            self.basic_server_socket = basic_server_socket
            print( "Logged in successfully with session ID: {}".format( self.session_id ) )
        else:
            print( "Login failed, disconnecting!" )

    def hold(self):
        for thread in self.threads:
            thread.join()

    def composeAndSendMessage(self):
        username = input( "Please enter username of recipient:\t" )
        message = input( "Please enter message:\t" )

        self.sendMessage( username, message, self.message_delimiter )

    def startListeningToIncomingCall(self, host, port, message_delimiter ):
        incoming_conn_and_call_receiving_module = IncomingConnectionReceivingAndCallingModule(
            host, port, message_delimiter )

        incoming_conn_and_call_receiving_module.start()
        self.threads.append( incoming_conn_and_call_receiving_module )
        print( "Started call listening!" )

    def connectToMessagingServer( self, id, ip_address, port):
        if self.basic_server_socket is None:
            print( "Please connect to basic server first!" )
            return
        sock = socket.socket()

        try:
            sock.connect( ( ip_address, port ) )
        except socket.error:
            print( "Cannot connect to messaging server!" )

        sock.send( '{}registration\n{}{}'.format( self.message_delimiter, id, self.message_delimiter ).encode() )

        response = sock.recv( 1024 ).decode()
        status, message = response.strip( self.message_delimiter ).split( '\n' )

        if status == '0':
            print( message )
            return
        else:
            print( message )

        messages_receiving_module = MessagesReceivingModule( sock, 1024, self.message_delimiter )
        self.threads.append( messages_receiving_module )
        messages_receiving_module.start()
        self.messaging_server_socket = sock
        print( "Started messages listening" )

    def connectToCallExchange( self, id, ip_address, port, incoming_call_port ):
        if self.basic_server_socket is None:
            print( "Please connect to basic server first!" )
            return
        sock = socket.socket()

        try:
            sock.connect( ( ip_address, port ) )
        except socket.error:
            print( "Cannot connect to call exchange server!" )

        sock.send( '{}registration\n{}\n{}{}'.format( self.message_delimiter, id, incoming_call_port, self.message_delimiter ).encode() )

        response = sock.recv( 1024 ).decode()
        status, message = response.strip( self.message_delimiter ).split( '\n' )

        if status == '0':
            print( message )
            return
        else:
            print( message )
            self.call_exchange_socket = sock

        self.startListeningToIncomingCall( self.call_exchange_socket.getsockname()[0], incoming_call_port, self.message_delimiter )

    def sendMessage(self, recipient, message, message_delimiter):
        if self.messaging_server_socket is None:
            print( "Connect to messaging server first!" )
            return

        self.messaging_server_socket.sendall( "{}{}\n{}\n{}{}".format(
            message_delimiter,
            recipient,
            self.username,
            message,
            message_delimiter ).encode() )

        print( "Message sent!" )

    def call(self, id):
        recipient = input( "Please enter the username of recipient: " )
        #Connect to dialer
        #Call
        #If call connects, start chatting
        try:
            dialer_socket = self.connectToDialer( self.server_ip, 5000 )
            dialer_socket.sendall( '{}registration\n{}{}'.format( self.message_delimiter, id, self.message_delimiter ).encode() )

            response = dialer_socket.recv(1024).decode()
            status, message = response.strip(self.message_delimiter).split('\n')

            if status == '0':
                print(message)
                return
            else:
                print(message)

            dialer_socket.sendall( '{}dial_info\n{}\n{}\nvideo{}'.format( self.message_delimiter, recipient, self.username, self.message_delimiter ).encode() )

            response = dialer_socket.recv(1024).decode().strip(self.message_delimiter)
            # print(dialer_socket.recv(1024).decode())
            if response.startswith( 'ACCEPTED' ):
                with open("DSC_0124.JPG", "rb") as imageFile:
                    file_data = imageFile.read()
                    b64encoded_file_data = base64.b64encode(file_data).decode()
                    sending_data = "{}{}{}".format( self.message_delimiter, b64encoded_file_data, self.message_delimiter )
                    for i in range( 0, 10 ):
                        dialer_socket.sendall( sending_data.encode() )
                        print( "Sending!" )
            elif response.startswith( 'REJECTED' ):
                print( "{} has rejected your call!".format( recipient ) )
            elif response.startswith( 'ERROR' ):
                print( response.split( ':' )[1] )


            input()
            dialer_socket.close()
        except socket.error:
            pass

    def connectToDialer(self, host, port):
        dialer_socket = socket.socket()
        dialer_socket.connect( ( host, port ) )
        return dialer_socket

    def loginAttempt(self, username, password):
        basic_server_socket = socket.socket()

        basic_server_socket.connect( ( self.server_ip, 27015 ) )

        basic_server_socket.send( "{}login_request\n{}\n{}{}".format(self.message_delimiter, username, password ,self.message_delimiter ).encode() )

        response = basic_server_socket.recv( 1024 ).decode()

        return response.strip( self.message_delimiter ), basic_server_socket