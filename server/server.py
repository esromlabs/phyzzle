from websocket_server import WebsocketServer
from time import sleep

# Called for every client connecting (after handshake)
def new_client(client, server):
	print("New client connected and was given id %d" % client['id'])
	server.send_message_to_all('{"msg":"Hey all, a new client has joined us"}')


# Called for every client disconnecting
def client_left(client, server):
	print("Client(%d) disconnected" % client['id'])


# Called when a client sends a message
def message_received(client, server, message):
	if len(message) > 200:
		message = message[:200]+'..'
	if message == 'start-stream':
		# echo start-streaming
		server.send_message_to_all('{"msg": "Starting to stream"}')
		# start the streaming
		server.streaming = True;
		print 'start-streaming'
		server.send_message_to_all('{"data": [20, 27, 11, 36, 13, 23, 19, 12]}')
		server.send_message_to_all('{"data": [22, 17, 15, 26, 33, 13, 29, 17]}')

	if message == 'stop-stream':
		# echo stop-streaming
		server.send_message_to_all('{"msg": "stop streaming"}')
		# stop the streaming
		server.streaming = False
		print 'stop-streaming'

	print("Client(%d) said: %s" % (client['id'], message))


PORT=9001
server = WebsocketServer(PORT)
server.set_fn_new_client(new_client)
server.set_fn_client_left(client_left)
server.set_fn_message_received(message_received)
server.streaming = False
server.run_forever()
