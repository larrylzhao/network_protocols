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

selfport = 0
peerport = 0
windowsize = 0
dropmode = "" #d(deterministic) or p(probabilistic)
n = 0
p = 0

"""
argument parser
./gbnnode.py 6000 6001 5 -d 3
./gbnnode.py 6000 6001 5 -p 0.333
"""
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
    sys.exit