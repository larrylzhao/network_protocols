#!/usr/bin/python
#####################################################################
#                                                                   #
#       GBN Protocol                                                #
#       CSEEW4119                                                   #
#       Author: Larry Zhao                                          #
#       UNI: LZ2479                                                 #
#       github: larrylzhao/network_protocols                        #
#                                                                   #
#####################################################################

import sys
import threading
import re
import json
from socket import *
import os
import datetime
import shutil

ip = "127.0.0.1"
selfport = 0
peerport = 0
windowsize = 0
dropmode = "" #d(deterministic) or p(probabilistic)
n = 0
p = 0
requestnum = 0
sequencebase = 0
sequencemax = 0

buffersize = 0
bufferindex = 0
sendingindex = 0
sendingbuffer = []
timeout = datetime.datetime.now()
listensocket = socket(AF_INET, SOCK_DGRAM)


"""
Thread for listening to incoming UDP messages
"""
def listen():
    global sequencebase, sequencemax, windowsize, listensocket, requestnum
    while True:
        data, sender = listensocket.recvfrom(1024)
        datasplit = data.split(";")
        if datasplit[0] == "a":
            # received an ack
            sequencebase = int(datasplit[1])+1
            sequencemax = sequencebase + windowsize
            sendingbuffer[datasplit[1]] = None
            print "[" + str(datetime.datetime.now()) +"] ACK" + str(datasplit[1]) + " received, window moves to " + str(sequencebase)
        elif datasplit[0] == "s":
            # received a data packet
            print "[" + str(datetime.datetime.now()) +"] packet" + str(datasplit[1]) + " " + str(datasplit[1]) + " received"
            ack = "a;" + str(datasplit[1])
            listensocket.sendto(ack, (ip,peerport))
            sys.stdout.write("[" + str(datetime.datetime.now()) +"] ACK" + str(requestnum) + " sent, expecting packet")
            if int(datasplit[1]) == requestnum:
                requestnum += 1
            print str(requestnum)


"""
sending buffer
"""
def buffer_add(data):
    global sendingbuffer
    global bufferindex
    while sendingbuffer[bufferindex] is not None:
        pass
    packet = "s;" + str(bufferindex) + ";" + str(data)
    sendingbuffer[bufferindex] = packet
    bufferindex += 1
    if bufferindex >= len(sendingbuffer):
        bufferindex = 0
    # print sendingbuffer


"""
sending function
"""
def send_message():
    while True:
        global sendingbuffer, bufferindex, sequencebase, sequencemax, timeout, buffersize
        nextseqnum = 0
        sendsocket = socket(AF_INET, SOCK_DGRAM)
        while sendingbuffer[sequencebase] is not None:
            # print "meow ", sequencebase, " ", sequencemax
            for i in range(0, 4):
                split = sendingbuffer[(sequencebase+i) % buffersize].split(";")
                sendsocket.sendto(sendingbuffer[i], (ip, peerport))
                if i == 0:
                    timeout = datetime.datetime.now() + datetime.timedelta(0,3)
                print sendingbuffer
                print "[" + str(datetime.datetime.now()) +"] packet" + split[1] + " " + split[2] + " sent"
                nextseqnum += 1
                if nextseqnum >= len(sendingbuffer):
                    nextseqnum = 0
                if sendingbuffer[nextseqnum] is None:
                    break
            while datetime.datetime.now() <= timeout:
                pass
        sendsocket.close()




"""
handler for client input
"""
def input():
    while True:
        input = raw_input('node> ')
        find = re.search('(\S*)', input)
        if find:
            command = find.group(1)
            if command == "send":
                find = re.search('\S* (.+)', input)
                if find:
                    message = find.group(1)
                    print "message: ", message
                    # split message into list of chars
                    messagelist = list(message)
                    for i in range(0, len(messagelist)):
                        buffer_add(messagelist[i])



                else:
                    print "Please provide a message to the peer."
            else:
                print "<"+ command + "> is not a recognized command."



def main():
    """
    argument parser
    ./gbnnode.py 6000 6001 5 -d 3
    ./gbnnode.py 6000 6001 5 -p 0.333
    """
    global selfport, peerport, windowsize, dropmode, n, p, sequencemax, buffersize

    goodArgs = True
    if len(sys.argv) > 1:
        selfport = int(sys.argv[1])
        if selfport >= 1024 and selfport <= 65535:
            print "self port number: ", selfport
        else:
            print "please give a self port number between 1024 and 65535"
            exit()
    if len(sys.argv) > 2:
        peerport = int(sys.argv[2])
        if peerport >= 1024 and peerport <= 65535:
            print "peer port number: ", peerport
        else:
            print "please give a peer port number between 1024 and 65535"
            exit()
    if len(sys.argv) > 3:
        windowsize = int(sys.argv[3])
        print "window size: ", windowsize
        if len(sys.argv) > 4:
            if sys.argv[4] == "-d":
                dropmode = "d"
                if len(sys.argv) > 5:
                    n = int(sys.argv[5])
                    print "deterministic drop rate: ", n
                else:
                    print "please provide the deterministic drop interval"
                    exit()
            elif sys.argv[4] == "-p":
                dropmode = "p"
                if len(sys.argv) > 5:
                    p = float(sys.argv[5])
                    print "deterministic drop rate: ", p
                else:
                    print "please provide the probabilistic drop interval"
                    exit()
            else:
                print "please provide a method for dropping packets"
                exit()
        else:
            goodArgs = False
    else:
        goodArgs = False

    if goodArgs is False:
        print "Usage: <self-port> <peer-port> <window-size> [ -d <value-of-n> | -p <value-of-p> ]"
        exit()

    try:
        # initialize variables
        buffersize = windowsize * 3
        for i in range(0, buffersize):
            sendingbuffer.append(None)
        sequencemax = windowsize - 1

        # start thread to listen to inbound traffic
        listensocket.bind(('', selfport))
        listenthread = threading.Thread(target=listen, args=())
        listenthread.daemon = True
        listenthread.start()

        # start thread to send packets in sending buffer
        # listensocket.bind(('', selfport))
        sendthread = threading.Thread(target=send_message, args=())
        sendthread.daemon = True
        sendthread.start()



        # start command input functionality
        input()
        exit()
    except (KeyboardInterrupt):
        listensocket.close()
        print "\n[exiting]"
        exit()


if __name__ == "__main__":
    main()