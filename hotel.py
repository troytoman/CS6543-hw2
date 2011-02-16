__author__ = 'troytoman'

import socket
import select
import sys
import threading

class Hotel:
    def __init__(self):
        self.next_confirmation = 1001
        self.date = ['3', '21', '2011']
        self.rooms = {101: 0, 102: 0, 103: 0, 104: 0, 105: 0, 106: 0, 107: 0, 108: 0, 109: 0, 110: 0}
        self.confirmations = {}
        self.room_rate = '50'
        self.bank = BankClient()

    def check(self,request_message):

        # parse the input message by splitting at '&' and creating dictionary with '=' pairs
        request = dict(item.split("=") for item in request_message.split("&"))

        # take action based on the "whattodo" key in the dictionary
        if request['whattodo'] == 'reservation':                       # reservation request
            print "CHECKING RESERVATION", request['Rmonth'], request['Rday'], request['Ryear']
            requested_date = [request['Rmonth'], request['Rday'], request['Ryear']]

            if requested_date == self.date:                # rooms only on self.date
                found = 0                                  # set flag for no room found
                for room in self.rooms:
                    if not self.rooms[room] and not found: # room available if there is no confirmation number

                        found = 1                          # reset flag to show a room was found

                        if request['Raccountnumber']:      # validate that an account number was provided
                            bank_reply = self.bank.debit(request['Raccountnumber'], self.room_rate)  # debit account
                        else:
                            bank_reply = 'No account number provided'
                            
                        if bank_reply == 'OK':            # validate that the debit transaction succeeded
                            self.rooms[room] = self.next_confirmation     # assign the confirmation number
                            self.confirmations[self.next_confirmation] = request['Raccountnumber']
                            reply_message = ('Reservation is confirmed. Confirmation %d Room %d' %
                                                          (self.next_confirmation, room))  # create reply
                            self.next_confirmation += 1   # increment the confirmation #
                        else:
                            reply_message = 'Bank Error: ' + bank_reply
                if not found:
                    reply_message = 'No rooms available'
            else:
                reply_message = 'No rooms available'
                
        elif request['whattodo'] == 'cancelation':                       # cancellation request

            print "CHECKING CANCELLATION", request['Croomnumber'], request['Cconfirmationnumber']

            found = 0
            room_number = int(request['Croomnumber'])
            conf_number = int(request['Cconfirmationnumber'])

            for room in self.rooms:
                if room == room_number and self.rooms[room] == conf_number:
                    found = 1
                    bank_reply = self.bank.credit(self.confirmations[conf_number], self.room_rate)
                    if bank_reply == 'OK':
                        self.rooms[room] = 0
                        reply_message = 'Cancellation successful for ' + str(conf_number)
                    else:
                        reply_message = 'Bank Error: ' + bank_reply

            if not found:
                reply_message = 'No such Cancellation Number/Room combination exists'
        else:
            reply_message = 'Unsupported request'

        return reply_message

class BankClient:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 4444
        self.size = 1024

    def credit(self, account, amount):
        # create the credit message
        message = 'C ' + account + ' ' + amount
        print "Sending Credit: " + message

        # create the socket and send the message
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.send(message)

        # get the response and close the connection
        reply = s.recv(self.size)
        s.close()
        print "RECEVIED BANK REPLY: " + reply

        return reply

    def debit(self, account, amount):
        # create the debit message
        message = 'D ' + account + ' ' + amount

        print "Sending Debit: " + message

        # create the socket and send the message
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        s.send(message)

        # get the response and close the connection
        reply = s.recv(self.size)
        s.close()
        print "RECEVIED BANK REPLY: " + reply

        return reply


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
            print "RECEIVED:" , data

            if data[0:3] == "GET":
                infile = open('index.html', 'r')
                reply = infile.read()
                self.server.send (reply)
                self.server.close()
                
            elif data[0:4] == "POST":
                message = data.split('\n')
                if len(message[-1]) < 10:
                    message[-1] = self.server.recv(self.size)
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
    #todo make port a commandline parameter and pass it into the hotel server
    s = HotelServer()
    s.run()

        #todo comments throughout