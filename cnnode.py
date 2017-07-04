#!/usr/bin/python
#####################################################################
#                                                                   #
#       Distance Vector Routing Algorithm                           #
#       CSEEW4119                                                   #
#       Author: Larry Zhao                                          #
#       UNI: LZ2479                                                 #
#       github: larrylzhao/network_protocols                        #
#                                                                   #
#####################################################################

import sys
import threading
from socket import *
import dvnode
import datetime
import random


pckcnt = 0
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
sendlock = False
windowsize = 5

"""
Thread for listening to incoming UDP messages
"""
def listen(ip, localPort, routingTable, iteration, listensocket, lossRateTable):

    while True:
        data, sender = listensocket.recvfrom(1024)
        datasplit = data.split(";")

        if datasplit[0] == "a" or datasplit[0] == "s":
            # getting a data packet for calculating loss
            # data schema: a;acknum
            #              s;senderport;data
            global pckdropcnt, sentpckcnt, sequencebase, windowsize, \
                acknum, requestnum, rcvmsgcnt, rcvcorrectackcnt, messagesize, buffersize, \
                sendingbuffer, timeoutStarted, timeout, rcvtotalackcnt

            pckcnt += 1
            droppkt = False
            if random.uniform(0, 1) <= lossRateTable:
                droppkt = True
                pckdropcnt += 1
            if datasplit[0] == "a":
                # received an ack
                rcvdack = int(datasplit[1])

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
                    # if rcvcorrectackcnt == messagesize:
                    #     pckdropcnt = sentpckcnt - rcvtotalackcnt
                    #     print "last ACK received"
                    #     message_finished()
            elif datasplit[0] == "s":
                peerport = datasplit[1]
                if random.uniform(0, 1) <= lossRateTable[peerport]:
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
                        print ackMsg + ", expecting packet" + str(requestnum)
                    else:
                        ack = "a;" + str(acknum)
                        listensocket.sendto(ack, (ip,peerport))
                        sentpckcnt += 1
                        print ackMsg + str(acknum) + " sent, expecting packet" + str(requestnum)
        else:
            # dv updates
            # data schema: neighborPort;serialized json object for neighbor's routing table
            neighborPort = datasplit[0]
            neighborTable = json.loads(datasplit[1])
            print "[" + str(datetime.datetime.now()) +"] Message received from Node " + str(neighborPort) \
                  + " to Node " + str(localPort)
            # print_routing_table(neighborPort, neighborTable)
            tableUpdated = dvnode.update_table(localPort, neighborPort, routingTable, neighborTable)
            # always send if node has never sent table before
            if iteration == 0:
                dvnode.send_table(ip, localPort, routingTable)
                iteration += 1
            elif tableUpdated is True:
                dvnode.send_table(ip, localPort, routingTable)


def main():
    """
    argument parser

    python cnnode.py 1111 receive send 2222 3333
    python cnnode.py 2222 receive 1111 .1 send 3333 4444
    python cnnode.py 3333 receive 1111 .5 2222 .2 send 4444
    python cnnode.py 4444 receive 2222 .8 3333 .5 send last
    """

    ip = "localhost"
    localPort = 0
    iteration = 0
    lossRateTable = {}
    routingTable = {}
    listensocket = socket(AF_INET, SOCK_DGRAM)

    usage = "cnnode <local-port> receive <neighbor1-port> <loss-rate-1> <neighbor2-port> <loss-rate-2> ... " \
            "<neighborM-port> <loss-rate-M> send <neighbor(M+1)-port> <neighbor(M+2)-port> ... <neighborN-port> [last]"
    goodArgs = True
    if len(sys.argv) > 1:
        localPort = int(sys.argv[1])
        if localPort < 1024 or localPort > 65535:
            print "please give a local port number between 1024 and 65535"
            print usage
            exit()
        localPort = str(localPort)
    else:
        print usage
        exit()

    probeMode = ""
    # parse neighbors into routing table
    if len(sys.argv) > 2 and (sys.argv[2] == "receive" or sys.argv[2] == "send"):
        probeMode = sys.argv[2]
    else:
        print usage
        exit()

    last = False
    j = 0
    if probeMode == "receive":
        for i in range(3, len(sys.argv))[::2]:
            if sys.argv[i] == "last":
                last = True
                break
            if sys.argv[i] == "send":
                probeMode = sys.argv[i]
                j = i + 1
                break

            neighborPort = int(sys.argv[i])
            if neighborPort < 1024 or neighborPort > 65535:
                print "please give a neighbor port number between 1024 and 65535"
                print usage
                exit()
            try:
                neighborPort = str(neighborPort)
                neighborLossRate = float(sys.argv[i+1])
                if neighborLossRate < 0.0 or neighborLossRate > 1.0:
                    print "please provide a valid loss rate for neighbor", neighborPort
                lossRateTable[neighborPort] = neighborLossRate
                routingTable[neighborPort] = {}
                routingTable[neighborPort]['weight'] = 0
                routingTable[neighborPort]['next'] = neighborPort
            except:
                print "please provide a neighbor loss rate for neighbor", neighborPort
                print usage
                exit()

    if probeMode == "send":
        for i in range(j, len(sys.argv)):
            if sys.argv[i] == "last":
                last = True
                break

            neighborPort = int(sys.argv[i])
            if neighborPort < 1024 or neighborPort > 65535:
                print "please give a neighbor port number between 1024 and 65535"
                print usage
                exit()
            neighborPort = str(neighborPort)
            routingTable[neighborPort] = {}
            routingTable[neighborPort]['weight'] = 0
            routingTable[neighborPort]['next'] = neighborPort

    dvnode.print_routing_table(localPort, routingTable)
    # print c
    # print lossRateTable

    try:
        # start thread to listen to inbound traffic
        listensocket.bind(('', int(localPort)))
        listenthread = threading.Thread(target=listen, args=(ip, localPort, routingTable, iteration, listensocket, lossRateTable))
        listenthread.daemon = True
        listenthread.start()

        if last is True:
            print "afeoiawjfoawiefjawfiojafiojfaieofjaoiwjfeajf"
            dvnode.send_table(ip, localPort, routingTable)
            iteration += 1

        while True:
            pass
        exit()
    except (KeyboardInterrupt):
        listensocket.close()
        print "\n[exiting]"
        exit()


if __name__ == "__main__":
    main()