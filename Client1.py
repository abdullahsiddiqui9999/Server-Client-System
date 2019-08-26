from Client import Client
import socket

host = socket.gethostname()
client1 = Client( host )

client1.login()


client1.connectToMessagingServer( client1.session_id, host, 6000 )

# client1.composeAndSendMessage()

client1.connectToCallExchange( client1.session_id, host, 9000 , 10000 )

client1.call( client1.session_id )
client1.call( client1.session_id )

client1.hold()