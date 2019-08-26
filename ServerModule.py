import threading

class ServerModule( threading.Thread ):
    def __init__(self, server ):
        threading.Thread.__init__( self )
        self.server = server

    def run(self):
        self.server.power_on()