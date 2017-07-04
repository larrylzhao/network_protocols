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
        listenthread = threading.Thread(target=dvnode.listen, args=(ip, localPort, routingTable, iteration, listensocket))
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