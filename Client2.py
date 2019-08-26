from Client import Client
import socket

host = socket.gethostname()
client2 = Client( host )

client2.login()


client2.connectToMessagingServer(client2.session_id, host, 6000)

# client2.composeAndSendMessage()

client2.connectToCallExchange( client2.session_id, host, 9000 , 11000 )

client2.call( client2.session_id )
client2.call( client2.session_id )

client2.hold()