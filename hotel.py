__author__ = 'troytoman'

# Setup TCP Socket and listen on port 3333
import socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("", 3333))

print "HotelServer Waiting for client on port 3333"

while 1:
    server_socket.listen(1)
    client_socket, address = server_socket.accept()
    print "I got a connection from ", address

    data = client_socket.recv(4096)
            
    print "RECEIVED: " , data

    if data[0:3] == "GET":
        infile = open('index.html', 'r')
        reply = infile.read()
        print "REPLY:" , reply
        client_socket.send (reply)
    elif data[0:4] == "POST":
        reply =' HTTP/1.1 200 OK'
        client_socket.send (reply)
        data = client_socket.recv(4096)
        message = data.partition("whattodo=")
        print "WHAT TO DO: ", message[2]
    client_socket.close()

