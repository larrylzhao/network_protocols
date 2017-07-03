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


localPort = 0
routingTable = {}

"""
function to print the routing table
"""
def print_routing_table():
    global routingTable
    print "Node " + str(localPort) + " Routing Table"
    for key in routingTable:
        print "- (" + str(routingTable[key]['weight']) + " -> " + str(key) + " ; Next hop -> Node " + str(routingTable[key]['next'])


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
        if 1024 <= localPort <= 65535:
            print "local port number:", localPort
        else:
            print "please give a local port number between 1024 and 65535"
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
    # routingTable[localPort] = {}
    for i in range(2, len(sys.argv))[::2]:
        if sys.argv[i] == "last":
            #TODO add method for kickstarting algo
            break

        neighborPort = int(sys.argv[i])
        if localPort < 1024 or localPort > 65535:
            print "please give a neighbor port number between 1024 and 65535"
            print usage
            exit()
        try:
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
    print_routing_table()






if __name__ == "__main__":
    main()