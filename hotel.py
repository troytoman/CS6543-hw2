__author__ = 'troytoman'

import socket
import select
import sys
import threading

class Hotel:
    def __init__(self):
        print "CREATING HOTEL"
        self.available = 30
        self.date = ['3', '21', '2011']

    def check(self,r):
        request = dict(item.split("=") for item in r.split("&"))
        if request['whattodo'] == 'reservation':
            print "CHECKING RESERVATION", request['Rmonth'], request['Rday'], request['Ryear']
            requested_date = [request['Rmonth'], request['Rday'], request['Ryear']]
            if (requested_date == self.date) and (self.available > 0) :
                reply_message = 'Reservation is confirmed. Confirmation #%d' % self.available
                self.available -= 1
            else:
                reply_message = 'Reservation is not available'
        if request['whattodo'] == 'cancelation':
            print "CHECKING Cancellation", request['Cmonth'], request['Cday'], request['Cyear']
            reply_message = 'Cancellation in process'
        else:
            reply_message = 'Unsupported request'
        return reply_message

class HotelServer:
    def __init__(self):
        self.host = ''
        self.port = 3333
        self.backlog = 5
        self.size = 1024
        self.server = None
        self.threads = []
        self.hotel = Hotel()

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
                    c = HotelThread(self.hotel,self.server.accept())
                    c.start()
                    self.threads.append(c)

                elif s == sys.stdin:
                    # check for keyboard input to shut the server down
                    junk = sys.stdin.readline()
                    running = 0

        # close the sockets
        self.server.close()
        # wait for threads to finish
        for t in self.threads:
            t.join()

class HotelThread(threading.Thread):
    def __init__(self, hotel, (server, address)):
        threading.Thread.__init__(self)
        self.server = server
        self.address = address
        self.size = 1024
        self.hotel = hotel
        print "I got a connection from ", self.address

    def run(self):
        running = 1
        while running:

            data = self.server.recv(self.size)
            # print "RECEIVED:" , data

            if data[0:3] == "GET":
                infile = open('index.html', 'r')
                reply = infile.read()
                self.server.send (reply)
                self.server.close()
                
            elif data[0:4] == "POST":
                message = data.split('\n')
                if len(message[-1]) < 10:
                    data = self.server.recv(self.size)
                print "WHAT TO DO: ",message[-1]
                reply_message = self.hotel.check(message[-1])
                reply = ('HTTP/1.1 200 OK\n' +
                         'Content-Type: text/plain\n' +
                         'Content-Length: '+ str(len(reply_message)) + '\n\n' +
                         reply_message)
                self.server.send (reply)
                self.server.close()

            running = 0

if __name__ == "__main__":
    s = HotelServer()
    s.run()