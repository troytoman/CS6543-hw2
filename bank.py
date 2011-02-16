__author__ = 'troytoman'

import socket
import select
import sys
import threading

class Bank:
    def __init__(self):
        print "CREATING BANK"
        self.accounts = {'10': 50}  #todo flesh out rest of account list

    def debit(self,message):

        message[2] = int(message[2])
        
        if self.accounts.has_key(message[1]):
            if self.accounts[message[1]] >= message[2]:
                self.accounts[message[1]] -= message[2]
                reply = 'OK'
            else:
                reply = 'ER Balance is only: ' + str(self.accounts[message[1]])
        else:
            reply = 'ER Invalid Account Number'
        return reply

    def credit(self, message):
        if self.accounts.has_key(message[1]):
            self.accounts[message[1]] += message[2]
            reply = 'OK'
        else:
            reply = 'ER Invalid Account Number'
        return reply

class BankServer:
    def __init__(self):
        # setup the default socket connection parameters
        self.host = ''
        #todo convert port number to be passed in at the command line
        self.port = 3333
        self.backlog = 5
        self.size = 1024
        self.server = None   # create a placeholder for the socket
        self.threads = []    # setup a thread list
        self.bank = Bank()   # create a bank for this server to operate

    def open_socket(self):
        try:        # create the socket and listen on the port
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((self.host, self.port))
            self.server.listen(self.backlog)
            print "BankServer Waiting for client on port 3333" #todo change message with variable port

        except socket.error, (value, message):   # handle any socket errors with a message
            if self.server:
                self.server.close()
            print "Could not open socket: " + message
            sys.exit(1)

    def run(self):
        self.open_socket()
        input = [self.server,sys.stdin]    # setup to listen for either keyboard or socket input
        running = 1
        while running:    #main loop for handling socket requests

            #monitor for input, output and exception events and take action on input
            inputready,outputready,exceptready = select.select(input,[],[])

            for s in inputready:
                if s == self.server:    # process socket input
                    print "RECEIVED INPUT"
                    c = BankThread(self.bank,self.server.accept()) # create a thread using the bank object
                    c.start()      # kick off the thread and put it in the list
                    self.threads.append(c)

                elif s == sys.stdin:     # check for keyboard input
                    print 'EXITING BANK SERVER'
                    junk = sys.stdin.readline()
                    running = 0          # then shut the server down

        # close the socket
        self.server.close()

        # wait for threads to finish
        for t in self.threads:
            t.join()

# This object handles processing requests that come in through the BankServer socket
class BankThread(threading.Thread):
    def __init__(self, bank, (server, address)):
        threading.Thread.__init__(self)
        self.server = server
        self.address = address
        self.size = 1024
        self.bank = bank
        print "I got a connection from ", self.address

    def run(self):
        running = 1  #todo examine if this parameter is necessary since the thread just handles one request
        while running:

            data = self.server.recv(self.size)
            message = data.split(' ')

            if message[0] == 'D':                 # Debit request
                reply = self.bank.debit(message)  # call debit method and get reply
                self.server.send (reply)          # send reply
                print "Processing debit: " + data
                self.server.close()               # close socket

            elif data[0] == 'C':                  # Credit request
                reply = self.bank.credit(message)
                self.server.send (reply)
                print "Processing credit: " + data
                self.server.close()

            running = 0

if __name__ == "__main__":
    s = BankServer()
    s.run()