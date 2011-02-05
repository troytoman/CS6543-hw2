__author__ = 'troytoman'

import socket
import select
import sys
import threading

class HotelServer:
    def __init__(self):
        self.host = ''
        self.port = 3333
        self.backlog = 5
        self.size = 1024
        self.server = None
        self.threads = []

    def open_socket(self):
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((self.host, self.port))
            self.server.listen(self.backlog)
            print "HotelServer Waiting for client on port 3333"

        except socket.error, (value, message):
            if self.server:
                self.server.close()
            print "Could not open socket: " + message
            sys.exit(1)

    def run(self):
        self.open_socket()
        input = [self.server,sys.stdin]
        running = 1
        while running:
            inputready,outputready,exceptready = select.select(input,[],[])

            for s in inputready:
                if s == self.server:
                    # handle the server socket
                    c = HotelThread(self.server.accept())
                    c.start()
                    self.threads.append(c)

                elif s == sys.stdin:
                    # check for keyboard input to shut the server down
                    junk - sys.stdin.readline()
                    running = 0

        # close the sockets
        self.server.close()
        # wait for threads to finish
        for t in self.threads:
            t.join()

class HotelThread(threading.Thread):
    def __init__(self, (server, address)):
        threading.Thread.__init__(self)
        self.server = server
        self.address = address
        self.size = 1024
        print "I got a connection from ", self.address

    def run(self):
        running = 1
        while running:

            data = self.server.recv(self.size)
            print "RECEIVED: " , data

            if data[0:3] == "GET":
                infile = open('index.html', 'r')
                reply = infile.read()
                print "REPLY:" , reply
                self.server.send (reply)
            elif data[0:4] == "POST":
                reply =' HTTP/1.1 200 OK'
                self.server.send (reply)
                data = self.server.recv(self.size)
                message = data.partition("whattodo=")
                print "WHAT TO DO: ", message[2]
            else:
                self.server.close()
                running = 0

if __name__ == "__main__":
    s = HotelServer()
    s.run()