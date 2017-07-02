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

# ip = "127.0.0.1"
ip = "localhost"
selfport = 0
peerport = 0
windowsize = 0
dropmode = "" #d(deterministic) or p(probabilistic)
n = 0
p = 0
acknum = 0
requestnum = 0
sequencebase = 0
sequencemax = 0
messagesize = 0
rcvmsgcnt = 0
rcvackcnt = 0
buffersize = 0
bufferindex = 0
sendingindex = 0
sendingbuffer = []
transmitstate = []
timeoutStarted = False
timeout = datetime.datetime.now()
listensocket = socket(AF_INET, SOCK_DGRAM)


"""
Function that is called when an entire message is received
prints out summary
"""
def message_finished():
    global rcvmsgcnt, rcvackcnt, requestnum, timeoutStarted
    print "Summary "
    rcvmsgcnt = 0
    rcvackcnt = 0
    requestnum = 0
    timeoutStarted = False
    # for i in range(0, buffersize):
    #     sendingbuffer[i] = None
    sys.stdout.write("\nnode> ")
    sys.stdout.flush()

"""
Thread for listening to incoming UDP messages
"""
def listen():
    global sequencebase, sequencemax, windowsize, listensocket, acknum, requestnum, rcvmsgcnt, rcvackcnt, messagesize, buffersize, sendingbuffer, timeout
    while True:
        data, sender = listensocket.recvfrom(1024)
        datasplit = data.split(";")
        if datasplit[0] == "a":
            # received an ack
            #TODO need to fix logic for receiving the right ack
            rcvdack = int(datasplit[1])
            for i in range(0, windowsize):
                last = False
                seqnum = (sequencebase + i) % buffersize
                if rcvdack == seqnum:
                    # print "************************************ ", rcvdack, seqnum, i
                    # got an ack that is in the window
                    # acknowledge all packets in the window up to the ack and move the window
                    for j in range(0, i+1):
                        bufferindex = (sequencebase + j) % buffersize
                        sendingbuffer[bufferindex] = None
                        transmitstate[bufferindex] = False
                        # print sendingbuffer
                        rcvackcnt += 1
                    timeoutStarted = False
                    sequencebase = seqnum+1
                    # reset the timer if window 0 was already sent
                    if transmitstate[sequencebase] is True:
                        timeoutStarted = True
                        timeout = datetime.datetime.now() + datetime.timedelta(0,3)
                        print "timeout reset ", timeout - datetime.datetime.now()

                    last = True
                if last is True:
                    break


            print "[" + str(datetime.datetime.now()) +"] ACK" + str(rcvdack) + " received, window moves to " + str(sequencebase)

            if rcvackcnt == messagesize:
                print "last ACK received"
                message_finished()
        elif datasplit[0] == "s":
            # received a data packet
            print "[" + str(datetime.datetime.now()) +"] packet" + str(datasplit[2]) + " " + str(datasplit[3]) + " received"
            ack = "a;" + str(acknum)
            listensocket.sendto(ack, (ip,peerport))
            sys.stdout.write("[" + str(datetime.datetime.now()) +"] ACK")

            if int(datasplit[2]) == requestnum:
                acknum = requestnum
                sys.stdout.write(str(acknum) + " sent")
                requestnum = (requestnum + 1) % buffersize
                rcvmsgcnt += 1
                if rcvmsgcnt == int(datasplit[1]):
                    # last packet was received
                    print ", full message received"
                    message_finished()
                else:
                    print ", expecting packet" + str(requestnum)
            else:
                print str(acknum) + " sent, expecting packet" + str(requestnum)




"""
sending buffer
"""
def buffer_add(data):
    global sendingbuffer
    global bufferindex
    while sendingbuffer[bufferindex] is not None:
        pass
    packet = "s;" + str(messagesize) + ";" + str(bufferindex) + ";" + str(data)
    sendingbuffer[bufferindex] = packet
    bufferindex += 1
    if bufferindex >= len(sendingbuffer):
        bufferindex = 0
    # print sendingbuffer


"""
sending function
"""
def send_message():
    global sendingbuffer, bufferindex, sequencebase, sequencemax,timeoutStarted, timeout, buffersize, windowsize, transmitstate
    while True:
        if timeoutStarted is True:
            print "timeout ", timeout - datetime.datetime.now()
        # don't send window again while the timer is active
        while timeoutStarted is True and datetime.datetime.now() <= timeout:
            pass

        sendsocket = socket(AF_INET, SOCK_DGRAM)

        if sendingbuffer[sequencebase] is not None:

            for i in range(0, windowsize):
                seqnum = (sequencebase + i) % buffersize
                split = []
                try:
                    split = sendingbuffer[seqnum].split(";")
                except:
                    break
                sendsocket.sendto(sendingbuffer[seqnum], (ip, peerport))
                transmitstate[seqnum] = True
                if timeoutStarted is False:
                    timeoutStarted = True
                    timeout = datetime.datetime.now() + datetime.timedelta(0,3)
                # print sendingbuffer
                print "[" + str(datetime.datetime.now()) +"] packet" + split[2] + " " + split[3] + " sent"
                seqnum = (seqnum + 1) % buffersize
                if sendingbuffer[seqnum] is None:
                    break


        sendsocket.close()




"""
handler for client input
"""
def input():
    global messagesize
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
                    messagesize = len(messagelist)
                    for i in range(0, len(messagelist)):
                        buffer_add(messagelist[i])


                else:
                    print "Please provide a message to the peer."
            else:
                print "<"+ command + "> is not a recognized command."



def main():
    """
    argument parser
    python gbnnode.py 6000 6001 5 -d 3
    ./gbnnode.py 6000 6001 5 -p 0.333
    """
    global selfport, peerport, windowsize, dropmode, n, p, sequencemax, buffersize, transmitstate

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
            transmitstate.append(False)
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