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
sequencebase = 0
sequencemax = 0
sendingbuffer = []
timer = 0


listensocket = socket(AF_INET, SOCK_DGRAM)

"""
Thread for listening to incoming UDP messages
"""
# def listen():
#     while True:
#         sender, data = selfport.recvfrom(1024)
#         datasplit = data.split(";")
#         if sender[0] == serverip and sender[1] == sPort:
#             # messages from server
#             try:
#                 clientTable = json.loads(datasplit[1])
#             except:
#                 pass
#             print datasplit[0]
#         elif datasplit[0] == "CHAT":
#             # chat messages from clients
#             listensocket.sendto("ACK", (sender[0],sender[1]))
#             find = re.search('^CHAT;'+datasplit[1]+';'+datasplit[2]+';(.*)', data)
#             if find:
#                 message = find.group(1)
#                 print datasplit[1] + ": " + message
#         sys.stdout.write(">>> ")
#         sys.stdout.flush()


"""
sending function
"""
def sendmessage():
    sendsocket = socket(AF_INET, SOCK_DGRAM)
    sendsocket.settimeout(.5)
    while len(sendingbuffer) > 0:
        sendsocket.sendto(message, (ip, peerport))
        try:
            data, sender = sendsocket.recvfrom(1024)
        except timeout:
            print ">>> [No ACK from <" + recipient + ">, message sent to server.]"
            chattimeout = offline_chat(message)
            if chattimeout is True:
                break
        else:
            for name in clientTable:
                if sender[0] == clientTable[name]['ip'] and sender[1] == clientTable[name]['port']:
                    print ">>> [Message received by <" + name + ">.]"
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
                    sendingbuffer = list(message)
                    sendmessage()



                else:
                    print "Please provide a message to the peer."
            else:
                print "<"+ command + "> is not a recognized command."



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

try:
    # start thread to listen to inbound traffic
    # listensocket.bind(('', selfport))
    # listenthread = threading.Thread(target=listen, args=())
    # listenthread.daemon = True
    # listenthread.start()

    # initialize sequence max
    sequencemax = windowsize - 1

    # start command input functionality
    input()
    exit()
except (KeyboardInterrupt):
    print "\n[exiting]"
    exit()