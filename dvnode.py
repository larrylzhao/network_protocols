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
import re
from socket import *
import datetime
import random
import json
import unicodedata

ip = "localhost"
localPort = 0
routingTable = {}
listensocket = socket(AF_INET, SOCK_DGRAM)

"""
function to print the table
"""
def print_routing_table(port, table):
    print "[" + str(datetime.datetime.now()) +"] Node " + str(port) + " Routing Table"
    for key in table:
        print "- (" + str(table[key]['weight']) + " -> " + str(key) \
           + ") ; Next hop -> Node " + str(table[key]['next'])


"""
Function to send table
"""
def send_table(table):
    global ip, localPort

    sSocket = socket(AF_INET, SOCK_DGRAM)
    for key in routingTable:
        print "[" + str(datetime.datetime.now()) +"] Message sent from Node " + str(localPort) \
              + " to Node " + str(key)
        sSocket.sendto(str(localPort) + ";" + json.dumps(table), (ip,int(key)))
    sSocket.close


"""
Function to update the local routing table if there is a faster route
"""
def update_table(neighborTable):
    global localPort, routingTable
    #TODO implement this


"""
Thread for listening to incoming UDP messages
"""
def listen():
    global localPort, listensocket

    while True:
        # data schema: neighborPort;serialized json object for neighbor's routing table
        data, sender = listensocket.recvfrom(1024)
        datasplit = data.split(";")
        neighborPort = datasplit[0]
        neighborTable = json.loads(datasplit[1])
        print "[" + str(datetime.datetime.now()) +"] Message received from Node " + str(neighborPort) \
              + " to Node " + str(localPort)
        print_routing_table(neighborPort, neighborTable)




def main():
    """
    argument parser
    python dvnode.py 1111 2222 .2 3333 .7
    python dvnode.py 2222 1111 .2 3333 .1
    python dvnode.py 3333 1111 .7 2222 .1 last
    """
    global localPort, routingTable

    usage = "usage: dvnode <local-port> <neighbor1-port> <loss-rate-1> <neighbor2-port> <loss-rate-2> ... [last]"
    goodArgs = True
    if len(sys.argv) > 1:
        localPort = int(sys.argv[1])
        if localPort < 1025 or localPort > 65535:
            print "please give a local port number between 1025 and 65535"
            print usage
            exit()
    else:
        print usage
        exit()

    # parse neighbors into routing table
    if len(sys.argv) < 3:
        print "please provide at least one neighbor"
        print usage
        exit()

    last = False
    for i in range(2, len(sys.argv))[::2]:
        if sys.argv[i] == "last":
            last = True
            break

        neighborPort = int(sys.argv[i])
        if localPort < 1025 or localPort > 65535:
            print "please give a neighbor port number between 1025 and 65535"
            print usage
            exit()
        try:
            neighborPort = str(neighborPort)
            neighborWeight = float(sys.argv[i+1])
            if neighborWeight < 0.0 or neighborWeight > 1.0:
                print "please provide a valid loss rate for neighbor", neighborPort
            routingTable[neighborPort] = {}
            routingTable[neighborPort]['weight'] = neighborWeight
            routingTable[neighborPort]['next'] = neighborPort
        except Exception,e:
            print "please provide a neighbor loss rate for neighbor", neighborPort
            print usage
            print str(e)
            exit()
    print_routing_table(localPort, routingTable)

    try:
        # start thread to listen to inbound traffic
        listensocket.bind(('', localPort))
        listenthread = threading.Thread(target=listen, args=())
        listenthread.daemon = True
        listenthread.start()

        if last is True:
            send_table(routingTable)

        while True:
            pass
        exit()
    except (KeyboardInterrupt):
        listensocket.close()
        print "\n[exiting]"
        exit()







if __name__ == "__main__":
    main()