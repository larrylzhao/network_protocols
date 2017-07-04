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

# Known bugs
# keeps trying to resend last packet if last ACK was dropped.

import sys
import threading
import re
from socket import *
import datetime
import random

# ip = "127.0.0.1"
ip = "localhost"
selfport = 0
peerport = 0
windowsize = 0
dropmode = "" #d(deterministic) or p(probabilistic)
n = 0
p = 0
acknum = -1 #need to start negative in case first packet is dropped. otherwise it'd send ack0
requestnum = 0
sequencebase = 0
messagesize = 0
rcvmsgcnt = 0
rcvcorrectackcnt = 0
rcvtotalackcnt = 0
buffersize = 0
bufferindex = 0
sendingbuffer = []
transmitstate = []
pckdropcnt = 0
sentpckcnt = 0
timeoutStarted = False
timeout = datetime.datetime.now()
listensocket = socket(AF_INET, SOCK_DGRAM)
sendlock = False


"""
Function that is called when an entire message is received
prints out summary
"""
def message_finished():
    global rcvmsgcnt, rcvcorrectackcnt, requestnum, timeoutStarted, pckdropcnt, \
        sentpckcnt, acknum, sequencebase, messagesize, bufferindex, timeout, \
        transmitstate, sendingbuffer, rcvtotalackcnt


    lossrate = 100.0 * (float(pckdropcnt) / float(sentpckcnt))
    print "[Summary] "+ str(pckdropcnt) + "/" + str(sentpckcnt) + " packets discarded, loss rate = " + str(lossrate) + "%"

    # reset variables
    acknum = -1
    requestnum = 0
    sequencebase = 0
    messagesize = 0
    rcvmsgcnt = 0
    rcvcorrectackcnt = 0
    rcvtotalackcnt = 0
    bufferindex = 0
    pckdropcnt = 0
    sentpckcnt = 0
    timeoutStarted = False
    timeout = datetime.datetime.now()
    for i in range(0, buffersize):
        sendingbuffer[i] = None
        transmitstate[i] = False
    sys.stdout.write("\nnode> ")
    sys.stdout.flush()

"""
Thread for listening to incoming UDP messages
"""
def listen():
    global dropmode, n, pckdropcnt, sentpckcnt, sequencebase, windowsize, listensocket, \
        acknum, requestnum, rcvmsgcnt, rcvcorrectackcnt, messagesize, buffersize, \
        sendingbuffer, timeoutStarted, timeout, rcvtotalackcnt

    dropcnt = 0
    ackdrop = False
    while True:
        data, sender = listensocket.recvfrom(1024)
        droppkt = False
        if dropmode == "d" and n != 0:
            if dropcnt == n-1:
                droppkt = True
            dropcnt = (dropcnt + 1) % n
        else:
            if random.uniform(0, 1) <= p:
                droppkt = True

        datasplit = data.split(";")
        if datasplit[0] == "a":
            # received an ack
            rcvdack = int(datasplit[1])
            if droppkt is True:
                print "[" + str(datetime.datetime.now()) +"] ACK" + str(rcvdack) + " discarded"
            else:
                rcvtotalackcnt += 1
                if rcvdack != -1:
                    for i in range(0, windowsize):
                        last = False
                        seqnum = (sequencebase + i) % buffersize
                        if rcvdack == seqnum:
                            # got an ack that is in the window
                            # acknowledge all packets in the window up to the ack and move the window
                            for j in range(0, i+1):
                                bufferindex = (sequencebase + j) % buffersize
                                sendingbuffer[bufferindex] = None
                                transmitstate[bufferindex] = False
                                rcvcorrectackcnt += 1
                            timeoutStarted = False
                            sequencebase = (seqnum + 1) % buffersize
                            # reset the timer if window 0 was already sent
                            if transmitstate[sequencebase] is True:
                                timeoutStarted = True
                                timeout = datetime.datetime.now() + datetime.timedelta(0,.5)

                            last = True
                        if last is True:
                            break
                    print "[" + str(datetime.datetime.now()) +"] ACK" + str(rcvdack) + " received, window moves to " + str(sequencebase)
                    if rcvcorrectackcnt == messagesize:
                        pckdropcnt = sentpckcnt - rcvtotalackcnt
                        print "last ACK received"
                        message_finished()
        elif datasplit[0] == "s":
            if droppkt is True:
                print "[" + str(datetime.datetime.now()) +"] packet" + str(datasplit[2]) + " " + str(datasplit[3]) + " discarded"
            else:
                # received a data packet
                print "[" + str(datetime.datetime.now()) +"] packet" + str(datasplit[2]) + " " + str(datasplit[3]) + " received"

                ackMsg = "[" + str(datetime.datetime.now()) +"] ACK"

                if int(datasplit[2]) == requestnum:
                    acknum = requestnum
                    ack = "a;" + str(acknum)
                    listensocket.sendto(ack, (ip,peerport))
                    sentpckcnt += 1
                    ackMsg = ackMsg + str(acknum) + " sent"
                    requestnum = (requestnum + 1) % buffersize
                    rcvmsgcnt += 1
                    ackdrop = False
                    if rcvmsgcnt == int(datasplit[1]):
                        # last packet was received
                        print ackMsg + ", full message received"
                        message_finished()
                    else:
                        print ackMsg + ", expecting packet" + str(requestnum)
                else:
                    ack = "a;" + str(acknum)
                    listensocket.sendto(ack, (ip,peerport))
                    sentpckcnt += 1
                    if ackdrop is False:
                        pckdropcnt += 1
                        ackdrop = True
                    print ackMsg + str(acknum) + " sent, expecting packet" + str(requestnum)




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
    global sendingbuffer, bufferindex, sequencebase, timeoutStarted, timeout, buffersize, windowsize, transmitstate, sentpckcnt, sendlock
    while True:

        if sendlock is False:
            sendsocket = socket(AF_INET, SOCK_DGRAM)
            base = sequencebase
            for i in range(0, windowsize):
                seqnum = (base + i) % buffersize
                packet = sendingbuffer[seqnum]
                trstate = transmitstate[seqnum]
                if packet is not None:
                    if trstate is False:
                        sendsocket.sendto(packet, (ip, peerport))
                        sentpckcnt += 1
                        transmitstate[seqnum] = True
                        if timeoutStarted is False:
                            timeoutStarted = True
                            timeout = datetime.datetime.now() + datetime.timedelta(0,.5)
                        # print "seq ", sequencebase, sendingbuffer
                        split = packet.split(";")
                        print "[" + str(datetime.datetime.now()) +"] packet" + split[2] + " " + split[3] + " sent"
        sendsocket.close()



"""
resending function
if message was already sent, wait for timeout to run out, then resend
"""
def resend_message():
    global sendingbuffer, bufferindex, sequencebase, timeoutStarted, timeout, buffersize, windowsize, transmitstate, sentpckcnt, sendlock
    while True:
        # don't send window again while the timer is active
        if timeoutStarted is True:
            if datetime.datetime.now() <= timeout:
                pass
            else:
                # print "timed out"
                sendlock = True
                resendsocket = socket(AF_INET, SOCK_DGRAM)
                base = sequencebase
                for i in range(0, windowsize):
                    seqnum = (base + i) % buffersize
                    packet = sendingbuffer[seqnum]
                    trstate = transmitstate[seqnum]
                    if packet is not None:
                        # if trstate is True:
                        resendsocket.sendto(packet, (ip, peerport))
                        sentpckcnt += 1
                        if i == 0:
                            timeout = datetime.datetime.now() + datetime.timedelta(0,.5)
                        # print sendingbuffer
                        split = packet.split(";")
                        print "[" + str(datetime.datetime.now()) +"] packet" + split[2] + " " + split[3] + " resent"

                resendsocket.close()
                sendlock = False



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
    python gbnnode.py 6000 6001 5 -p 0.2
    python gbnnode.py 6001 6000 5 -p 0.2
    ./gbnnode.py 6000 6001 5 -p 0.333
    send abcdefghijklmnopqrstuvwxyz
    """
    global selfport, peerport, windowsize, dropmode, n, p, buffersize, transmitstate

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
        buffersize = windowsize * 2 # not sure what buffer size should be
        for i in range(0, buffersize):
            sendingbuffer.append(None)
            transmitstate.append(False)

        # start thread to listen to inbound traffic
        listensocket.bind(('', selfport))
        listenthread = threading.Thread(target=listen, args=())
        listenthread.daemon = True
        listenthread.start()

        # start thread to send packets in sending buffer
        sendthread = threading.Thread(target=send_message, args=())
        sendthread.daemon = True
        sendthread.start()

        # start thread to resend packets that do not receive acks
        resendthread = threading.Thread(target=resend_message, args=())
        resendthread.daemon = True
        resendthread.start()



        # start command input functionality
        input()
        exit()
    except (KeyboardInterrupt):
        listensocket.close()
        print "\n[exiting]"
        exit()


if __name__ == "__main__":
    main()