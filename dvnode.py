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
import datetime
import json

ip = "localhost"
localPort = 0
iteration = 0
c = {}
routingTable = {}
listensocket = socket(AF_INET, SOCK_DGRAM)

"""
function to print the table
input: port, routing table
output: stdout routing table
return: null
"""
def print_routing_table(port, table):
    print "[" + str(datetime.datetime.now()) +"] Node " + str(port) + " Routing Table"
    for node in table:
        sys.stdout.write( "- (" + str(table[node]['weight']) + " -> " + str(node) + ");")
        if str(node) != str(table[node]['next']):
            sys.stdout.write(" Next hop -> Node " + str(table[node]['next']))
        print ""


"""
Function to send table
input: routing table
output: UDP packet containing routing table to each neighbor
return: null
"""
def send_table(table):
    global ip, localPort, c

    sSocket = socket(AF_INET, SOCK_DGRAM)
    for node in c:
        print "[" + str(datetime.datetime.now()) +"] Message sent from Node " + str(localPort) \
              + " to Node " + str(node)
        sSocket.sendto(str(localPort) + ";" + json.dumps(table), (ip,int(node)))
    sSocket.close


"""
Function to update the local routing table if there is a faster route
input: neighbor port and table
output:  stdout local routing table
return: True if local routing table is updated
"""
def update_table(neighborPort, neighborTable):
    global localPort, iteration, c, routingTable
    tableUpdated = False
    for node in neighborTable:
        if node != localPort:
            neighborWeight = c[neighborPort] + neighborTable[node]['weight']
            #check if node is in local table. add if not
            if node in routingTable:
                currentWeight = routingTable[node]['weight']
                if neighborWeight < currentWeight:
                    routingTable[node]['weight'] = neighborWeight
                    routingTable[node]['next'] = neighborPort
                    tableUpdated = True
            else:
                routingTable[node] = {}
                routingTable[node]['weight'] = neighborWeight
                routingTable[node]['next'] = neighborPort
                tableUpdated = True
    print_routing_table(localPort, routingTable)
    return tableUpdated


"""
Thread for listening to incoming UDP messages
"""
def listen():
    global localPort, iteration, listensocket

    while True:
        # data schema: neighborPort;serialized json object for neighbor's routing table
        data, sender = listensocket.recvfrom(1024)
        datasplit = data.split(";")
        neighborPort = datasplit[0]
        neighborTable = json.loads(datasplit[1])
        print "[" + str(datetime.datetime.now()) +"] Message received from Node " + str(neighborPort) \
              + " to Node " + str(localPort)
        # print_routing_table(neighborPort, neighborTable)
        tableUpdated = update_table(neighborPort, neighborTable)
        # always send if node has never sent table before
        if iteration == 0:
            send_table(routingTable)
            iteration += 1
        elif tableUpdated is True:
            send_table(routingTable)




def main():
    """
    argument parser
    python dvnode.py 1111 2222 .2 3333 .7
    python dvnode.py 2222 1111 .2 3333 .1
    python dvnode.py 3333 1111 .7 2222 .1 last

    python dvnode.py 1111 2222 .1 3333 .5
    python dvnode.py 2222 1111 .1 3333 .2 4444 .8
    python dvnode.py 3333 1111 .5 2222 .2 4444 .5
    python dvnode.py 4444 2222 .8 3333 .5 last
    """
    global localPort, iteration, c, routingTable

    usage = "usage: dvnode <local-port> <neighbor1-port> <loss-rate-1> <neighbor2-port> <loss-rate-2> ... [last]"
    goodArgs = True
    if len(sys.argv) > 1:
        localPort = int(sys.argv[1])
        if localPort < 1025 or localPort > 65535:
            print "please give a local port number between 1025 and 65535"
            print usage
            exit()
        localPort = str(localPort)
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
        if neighborPort < 1025 or neighborPort > 65535:
            print "please give a neighbor port number between 1025 and 65535"
            print usage
            exit()
        try:
            neighborPort = str(neighborPort)
            neighborWeight = float(sys.argv[i+1])
            if neighborWeight < 0.0 or neighborWeight > 1.0:
                print "please provide a valid loss rate for neighbor", neighborPort
            c[neighborPort] = neighborWeight
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
        listensocket.bind(('', int(localPort)))
        listenthread = threading.Thread(target=listen, args=())
        listenthread.daemon = True
        listenthread.start()

        if last is True:
            send_table(routingTable)
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