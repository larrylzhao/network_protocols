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

# Known bugs
# Loss rate calculation is working, but the routing table does not update properly

import sys
import threading
from socket import *
import dvnode
import datetime
import random
import json


ip = "localhost"
localPort = 0
windowsize = 5
buffersize = 0
iteration = 0

sendTable = {}
pckcnt = {}
acknum = {}
requestnum = {}
sequencebase = {}
messagesize = {}
rcvmsgcnt = {}
rcvcorrectackcnt = {}
rcvtotalackcnt = {}
bufferindex = {}
sendingbuffer = {}
transmitstate = {}
pckdropcnt = {}
sentpckcnt = {}
timeoutStarted = {}
timeout = {}
sendlock = {}


"""
Thread for listening to incoming UDP messages
"""
def listen(ip, localPort, routingTable, listensocket, lossRateTable, neighbors):

    global pckdropcnt, sentpckcnt, sequencebase, windowsize, \
        acknum, requestnum, rcvmsgcnt, rcvcorrectackcnt, messagesize, buffersize, \
        sendingbuffer, timeoutStarted, timeout, rcvtotalackcnt, sendTable, iteration

    while True:
        data, sender = listensocket.recvfrom(1024)
        datasplit = data.split(";")
        if datasplit[0] == "a" or datasplit[0] == "s":
            # getting a data packet for calculating loss
            # data schema: a;senderport;acknum
            #              s;senderport;bufferindex;data
            node = datasplit[1]


            if datasplit[0] == "a":
                # received an ack
                rcvdack = int(datasplit[2])

                rcvtotalackcnt[node] += 1
                if rcvdack != -1:
                    for i in range(0, windowsize):
                        last = False
                        seqnum = (sequencebase[node] + i) % buffersize
                        if rcvdack == seqnum:
                            # got an ack that is in the window
                            # acknowledge all packets in the window up to the ack and move the window
                            for j in range(0, i+1):
                                bufferindex[node] = (sequencebase[node] + j) % buffersize
                                sendingbuffer[node][bufferindex[node]] = None
                                transmitstate[node][bufferindex[node]] = False
                                rcvcorrectackcnt[node] += 1
                            timeoutStarted[node] = False
                            sequencebase[node] = (seqnum + 1) % buffersize
                            # reset the timer if window 0 was already sent
                            if transmitstate[node][sequencebase[node]] is True:
                                timeoutStarted[node] = True
                                timeout[node] = datetime.datetime.now() + datetime.timedelta(0,.5)
                            last = True
                        if last is True:
                            break
                    # print "[" + str(datetime.datetime.now()) +"] ACK" + str(rcvdack) + " received, window moves to " + str(sequencebase)
                    # if rcvcorrectackcnt == messagesize:
                    #     pckdropcnt = sentpckcnt - rcvtotalackcnt
                    #     print "last ACK received"
                    #     message_finished()
            elif datasplit[0] == "s":
                if random.uniform(0, 1) <= lossRateTable[node]:
                    pass
                    # print "[" + str(datetime.datetime.now()) +"] packet" + str(datasplit[2]) + " " + str(datasplit[3]) + " discarded"
                else:
                    # received a data packet
                    # print "[" + str(datetime.datetime.now()) +"] packet" + str(datasplit[2]) + " " + str(datasplit[3]) + " received"

                    ackMsg = "[" + str(datetime.datetime.now()) +"] ACK"
                    if int(datasplit[2]) == requestnum[node]:
                        acknum[node] = requestnum[node]
                        ack = "a;" + localPort + ";" + str(acknum[node])
                        listensocket.sendto(ack, (ip,int(node)))
                        ackMsg = ackMsg + str(acknum[node]) + " sent to " + node
                        requestnum[node] = (requestnum[node] + 1) % buffersize
                        # print ackMsg + ", expecting packet" + str(requestnum[node]), ack
                    else:
                        ack = "a;" + localPort + ";" + str(acknum[node])
                        listensocket.sendto(ack, (ip,int(node)))
                        # print ackMsg + str(acknum[node]) + " sent to " + node + ", expecting packet" + str(requestnum[node]), ack
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
                dvnode.send_table(ip, localPort, routingTable, neighbors)
                iteration += 1

            elif tableUpdated is True:
                dvnode.send_table(ip, localPort, routingTable, neighbors)


def buffer_start(localPort, node):
    global iteration
    # while True:
    while iteration == 0:
        pass
    while True:
        for node in sendTable:
            buffer_add(localPort, node)


def loss_status(routingTable, neighbors):
    while iteration == 0:
        pass
    global sendTable, sentpckcnt, rcvtotalackcnt, localPort, ip
    lossStatusTimer = datetime.datetime.now() + datetime.timedelta(0,1)
    updateTableTimer = datetime.datetime.now() + datetime.timedelta(0,5)
    weightTable = {}
    while True:
        while datetime.datetime.now() <= lossStatusTimer:
            pass
        for node in sendTable:
            pckdropcnt = sentpckcnt[node] - rcvtotalackcnt[node]
            lossrate = 0

            if sentpckcnt[node] != 0:
                lossrate = round(float(pckdropcnt)/float(sentpckcnt[node]), 2)
            weightTable[node] = lossrate
            print "[" + str(datetime.datetime.now()) +"] Link to " + node + ": " \
                + str(sentpckcnt[node]) + " packets sent, " + str(pckdropcnt) \
                + " packets lost, loss rate " + str(lossrate)
        lossStatusTimer = datetime.datetime.now() + datetime.timedelta(0,1)

        while datetime.datetime.now() <= updateTableTimer:
            pass
        for node in weightTable:
            if routingTable[node]['weight'] != weightTable[node]:
                routingTable[node]['weight'] = weightTable[node]
                dvnode.print_routing_table(localPort, routingTable)
                dvnode.send_table(ip, localPort, routingTable, neighbors)

        lossStatusTimer = datetime.datetime.now() + datetime.timedelta(0,1)




"""
sending buffer
"""
def buffer_add(localPort, node):
    global sendingbuffer
    global bufferindex
    while sendingbuffer[node][bufferindex[node]] is not None:
        pass
    packet = "s;" + localPort + ";" + str(bufferindex[node]) + ";x"
    sendingbuffer[node][bufferindex[node]] = packet
    bufferindex[node] += 1
    if bufferindex[node] >= len(sendingbuffer[node]):
        bufferindex[node] = 0
        # print sendingbuffer




"""
probe sending function
"""
def send_message(node):
    print "sending thread started for " + node
    global sendingbuffer, bufferindex, sequencebase, timeoutStarted, timeout, buffersize, windowsize, transmitstate, sentpckcnt, sendlock
    while True:

        if sendlock[node] is False:
            sendsocket = socket(AF_INET, SOCK_DGRAM)
            base = sequencebase[node]
            for i in range(0, windowsize):
                seqnum = (base + i) % buffersize
                packet = sendingbuffer[node][seqnum]
                trstate = transmitstate[node][seqnum]
                if packet is not None:
                    if trstate is False:
                        sendsocket.sendto(packet, (ip, int(node)))
                        sentpckcnt[node] += 1
                        transmitstate[node][seqnum] = True
                        if timeoutStarted[node] is False:
                            timeoutStarted[node] = True
                            timeout[node] = datetime.datetime.now() + datetime.timedelta(0,.5)
                        # print "seq ", sequencebase, sendingbuffer
                        # split = packet.split(";")
                        # print "[" + str(datetime.datetime.now()) +"] packet" + split[2] + " " + split[3] + " sent to " + node, packet
            sendsocket.close()


"""
resending function
if message was already sent, wait for timeout to run out, then resend
"""
def resend_message(node):
    global sendingbuffer, bufferindex, sequencebase, timeoutStarted, timeout, buffersize, windowsize, transmitstate, sentpckcnt, sendlock
    while True:
        # don't send window again while the timer is active
        if timeoutStarted[node] is True:
            if datetime.datetime.now() <= timeout[node]:
                pass
            else:
                # print "timed out"
                sendlock[node] = True
                resendsocket = socket(AF_INET, SOCK_DGRAM)
                base = sequencebase[node]
                for i in range(0, windowsize):
                    seqnum = (base + i) % buffersize
                    packet = sendingbuffer[node][seqnum]
                    trstate = transmitstate[node][seqnum]
                    if packet is not None:
                        # if trstate is True:
                        resendsocket.sendto(packet, (ip, int(node)))
                        sentpckcnt[node] += 1
                        if i == 0:
                            timeout[node] = datetime.datetime.now() + datetime.timedelta(0,.5)
                        # print sendingbuffer
                        # split = packet.split(";")
                        # print "[" + str(datetime.datetime.now()) +"] packet" + split[2] + " " + split[3] + " resent to " + node, packet

                resendsocket.close()
                sendlock[node] = False



def main():
    """
    argument parser

    python cnnode.py 1111 receive send 2222 3333
    python cnnode.py 2222 receive 1111 .1 send 3333 4444
    python cnnode.py 3333 receive 1111 .5 2222 .2 send 4444
    python cnnode.py 4444 receive 2222 .8 3333 .5 send last
    """

    global ip, localPort, sendTable, iteration
    lossRateTable = {}
    routingTable = {}
    neighbors = []
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
                neighbors.append(neighborPort)
                lossRateTable[neighborPort] = neighborLossRate
                routingTable[neighborPort] = {}
                routingTable[neighborPort]['weight'] = 0.0
                routingTable[neighborPort]['next'] = neighborPort

                requestnum[neighborPort] = 0
                acknum[neighborPort] = -1 #need to start negative in case first packet is dropped. otherwise it'd send ack0

            except:
                print "please provide a neighbor loss rate for neighbor", neighborPort
                print usage
                exit()
        print "loss rate table ", lossRateTable
    if probeMode == "send":
        global sendingbuffer, bufferindex, sequencebase, timeoutStarted, timeout, buffersize, windowsize, transmitstate, sentpckcnt, sendlock
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
            neighbors.append(neighborPort)
            routingTable[neighborPort] = {}
            routingTable[neighborPort]['weight'] = 0.0
            routingTable[neighborPort]['next'] = neighborPort

            sendTable[neighborPort] = 0
            sequencebase[neighborPort] = 0
            rcvcorrectackcnt[neighborPort] = 0
            rcvtotalackcnt[neighborPort] = 0
            bufferindex[neighborPort] = 0
            sendingbuffer[neighborPort] = []
            transmitstate[neighborPort] = []
            pckdropcnt[neighborPort] = 0
            sentpckcnt[neighborPort] = 0
            timeoutStarted[neighborPort] = False
            timeout[neighborPort] = datetime.datetime.now()
            sendlock[neighborPort] = False

    dvnode.print_routing_table(localPort, routingTable)
    # print c
    # print lossRateTable



    try:
        buffersize = windowsize * 2 # not sure what buffer size should be
        for node in sendTable:
            for i in range(0, buffersize):
                sendingbuffer[node].append(None)
                transmitstate[node].append(False)



        # start thread to listen to inbound traffic
        listensocket.bind(('', int(localPort)))
        listenthread = threading.Thread(target=listen, args=(ip, localPort, routingTable, listensocket, lossRateTable, neighbors))
        listenthread.daemon = True
        listenthread.start()



        for node in sendTable:
            # start thread for populating buffer
            bufferaddthread = threading.Thread(target=buffer_start, args=(localPort, node))
            bufferaddthread.daemon = True
            bufferaddthread.start()

            # start thread for calculating loss rate
            lossthread = threading.Thread(target=loss_status, args=(routingTable, neighbors))
            lossthread.daemon = True
            lossthread.start()

            # start thread to send packets in sending buffer
            sendthread = threading.Thread(target=send_message, args=(node,))
            sendthread.daemon = True
            sendthread.start()

            # start thread to resend packets that do not receive acks
            resendthread = threading.Thread(target=resend_message, args=(node,))
            resendthread.daemon = True
            resendthread.start()

        if last is True:
            dvnode.send_table(ip, localPort, routingTable, neighbors)
            iteration += 1


            # while True:
            # for i in range (0,21):
            #     for node in sendTable:
            #         buffer_add(localPort, node)

        while True:
            pass
        exit()
    except (KeyboardInterrupt):
        listensocket.close()
        print "\n[exiting]"
        exit()


if __name__ == "__main__":
    main()