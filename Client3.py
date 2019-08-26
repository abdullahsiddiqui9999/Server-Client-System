from Client import Client
import socket

host = socket.gethostname()
client3 = Client(host)

client3.login()


client3.connectToMessagingServer(client3.session_id, host, 6000)

# client2.composeAndSendMessage()

client3.connectToCallExchange( client3.session_id, host, 9000, 12000 )

client3.hold()