Larry Zhao

LZ2479

Network Protocols

========================================================================================
GBN Node
----------------------------------------------------------------------------------------
usage:
python gbnnode.py <self-port> <peer-port> <window-size> [ -d <value-of-n> | -p <value-of-p> ]
example:
python gbnnode.py 6000 6001 5 -p 0.2

This uses UDP to simulate the go back n protocol.
There is a sending buffer 2x the size of the window to prevent wrap-around issues.
The buffer is implemented using an array.
There are 4 threads: main, listen, send, and resend.
The listen thread listens for incoming UDP packets.
The send thread sends as long as there are items in the window that have not been previously sent.
The resent thread sends already sent items in the window if an ACK has not been received within 500ms.

Known Bugs:
keeps trying to resend last packet if last ACK was dropped.

Test case:
z2479@instance-1:~/PA2/network_protocols$ python gbnnode.py 6000 6001 5 -d 5
self port number:  6000
peer port number:  6001
window size:  5
deterministic drop rate:  5
node> send abcdefghijklmnopqrstuvwxyz
message:  abcdefghijklmnopqrstuvwxyz
[2017-07-04 23:03:27.596369] packet0 a sent
[2017-07-04 23:03:27.596531] packet1 b sent
[2017-07-04 23:03:27.596629] packet2 c sent
[2017-07-04 23:03:27.596721] packet3 d sent
[2017-07-04 23:03:27.596819] packet4 e sent
[2017-07-04 23:03:27.608030] ACK0 received, window moves to 1
[2017-07-04 23:03:27.608132] ACK1 received, window moves to 2
[2017-07-04 23:03:27.608201] ACK2 received, window moves to 3
.
.
.
[2017-07-04 23:03:30.764034] ACK4 received, window moves to 5
[2017-07-04 23:03:30.764120] ACK5 received, window moves to 6
last ACK received
[Summary] 14/53 packets discarded, loss rate = 26.4150943396%

lz2479@instance-1:~/PA2/network_protocols$ python gbnnode.py 6001 6000 5 -d 10
self port number:  6001
peer port number:  6000
window size:  5
deterministic drop rate:  10
node> [2017-07-04 23:03:27.602494] packet0 a received
[2017-07-04 23:03:27.602586] ACK0 sent, expecting packet1
[2017-07-04 23:03:27.602893] packet1 b received
[2017-07-04 23:03:27.602951] ACK1 sent, expecting packet2
[2017-07-04 23:03:27.603074] packet2 c received
[2017-07-04 23:03:27.603121] ACK2 sent, expecting packet3
.
.
.
[2017-07-04 23:03:30.239995] ACK3 sent, expecting packet4
[2017-07-04 23:03:30.751956] packet4 y received
[2017-07-04 23:03:30.759906] ACK4 sent, expecting packet5
[2017-07-04 23:03:30.760056] packet5 z received
[2017-07-04 23:03:30.760111] ACK5 sent, full message received
[Summary] 6/48 packets discarded, loss rate = 12.5%



========================================================================================
DV Node
----------------------------------------------------------------------------------------
usage:
python dvnode.py <local-port> <neighbor1-port> <loss-rate-1> <neighbor2-port> <loss-rate-2> ... [last]
example:
python dvnode.py 1111 2222 .1 3333 .5
python dvnode.py 2222 1111 .1 3333 .2 4444 .8
python dvnode.py 3333 1111 .5 2222 .2 4444 .5
python dvnode.py 4444 2222 .8 3333 .5 last

This uses UDP to simulate a DV bellman-ford protocol.
A dictionary holds the routing tables, and the tables are sent to neighbors.
    data schema: neighborPort;serialized json object for neighbor's routing table.
A listening thread will check if the received neighbor tables improve the listening table.
    The table is updated if it does and sent out to neighbors.
There is an iteration counter that notifies the non-last nodes when they should send their tables.

Test case:
lz2479@instance-1:~/PA2/network_protocols$ python dvnode.py 1111 2222 .1 3333 .5
[2017-07-04 23:12:43.513294] Node 1111 Routing Table
- (0.5 -> 3333);
- (0.1 -> 2222);
[2017-07-04 23:12:57.400701] Message received from Node 2222 to Node 1111
[2017-07-04 23:12:57.400986] Node 1111 Routing Table
- (0.3 -> 3333); Next hop -> Node 2222
- (0.9 -> 4444); Next hop -> Node 2222
- (0.1 -> 2222);
.
.
.
[2017-07-04 23:12:57.424907] Message received from Node 2222 to Node 1111
[2017-07-04 23:12:57.424969] Node 1111 Routing Table
- (0.3 -> 3333); Next hop -> Node 2222
- (0.8 -> 4444); Next hop -> Node 2222
- (0.1 -> 2222);

lz2479@instance-1:~/PA2/network_protocols$     python dvnode.py 3333 1111 .5 2222 .2 4444 .5
[2017-07-04 23:12:53.764453] Node 3333 Routing Table
- (0.5 -> 1111);
- (0.5 -> 4444);
- (0.2 -> 2222);
[2017-07-04 23:12:57.407955] Message received from Node 4444 to Node 3333
[2017-07-04 23:12:57.408063] Node 3333 Routing Table
.
.
.
[2017-07-04 23:12:57.428382] Message received from Node 1111 to Node 3333
[2017-07-04 23:12:57.428440] Node 3333 Routing Table
- (0.3 -> 1111); Next hop -> Node 2222
- (0.5 -> 4444);
- (0.2 -> 2222);

lz2479@instance-1:~/PA2/network_protocols$     python dvnode.py 2222 1111 .1 3333 .2 4444 .8
[2017-07-04 23:12:48.646715] Node 2222 Routing Table
- (0.1 -> 1111);
- (0.2 -> 3333);
- (0.8 -> 4444);
[2017-07-04 23:12:57.399985] Message received from Node 4444 to Node 2222
.
.
.
[2017-07-04 23:12:57.436445] Message received from Node 1111 to Node 2222
[2017-07-04 23:12:57.436492] Node 2222 Routing Table
- (0.1 -> 1111);
- (0.2 -> 3333);
- (0.7 -> 4444); Next hop -> Node 3333

lz2479@instance-1:~/PA2/network_protocols$     python dvnode.py 4444 2222 .8 3333 .5 last
[2017-07-04 23:12:57.389075] Node 4444 Routing Table
- (0.5 -> 3333);
- (0.8 -> 2222);
[2017-07-04 23:12:57.392219] Message sent from Node 4444 to Node 3333
[2017-07-04 23:12:57.396157] Message sent from Node 4444 to Node 2222
[2017-07-04 23:12:57.408643] Message received from Node 2222 to Node 4444
.
.
.
[2017-07-04 23:12:57.413814] Node 4444 Routing Table
- (0.5 -> 3333);
- (0.8 -> 1111); Next hop -> Node 2222
- (0.7 -> 2222); Next hop -> Node 3333
[2017-07-04 23:12:57.414225] Message sent from Node 4444 to Node 3333
[2017-07-04 23:12:57.416036] Message sent from Node 4444 to Node 2222




========================================================================================
GBN DV Node
----------------------------------------------------------------------------------------
usage:
python cnnode.py <local-port> receive <neighbor1-port> <loss-rate-1> <neighbor2-port> <loss-rate-2> ... " \
    "<neighborM-port> <loss-rate-M> send <neighbor(M+1)-port> <neighbor(M+2)-port> ... <neighborN-port> [last]
example:
python cnnode.py 1111 receive send 2222 3333
python cnnode.py 2222 receive 1111 .1 send 3333 4444
python cnnode.py 3333 receive 1111 .5 2222 .2 send 4444
python cnnode.py 4444 receive 2222 .8 3333 .5 send last

This is a combination of the GBN and DV node protocols.
The weights on the edges of the DV network are calculated by the loss rate given in the GBN protocols.
The implementation is a combination of the two above protocols.
There is an extra thread for continuously calculating the loss rates on the links on the sender side.
Every 5 seconds the link costs are updated, and the routing table is sent out if the table is changed.

Known bugs:
Loss rate calculation is working, but the routing table does not update properly
Print statements from different threads are intermingled

Test case:

.
.
.
[2017-07-04 23:22:09.915864] Link to 3333: 3993 packets sent, 3559 packets lost, loss rate 0.89
[2017-07-04 23:22:09.948073] Message received from Node 2222 to Node 1111
[2017-07-04 23:22:09.955950] Link to 2222: 886 packets sent, 347 packets lost, loss rate 0.39
[2017-07-04 23:22:09.963961] Node 1111 Routing Table
- (0.89 -> 3333); Next hop -> Node 2222
- (0.0 -> 4444); Next hop -> Node 3333
- (0.39 -> 2222);

.
.
.
2017-07-04 23:22:07.531921] Node 2222 Routing Table
- (0.0 -> 1111);
- (0.48 -> 3333); Next hop -> Node 1111
- (0.85 -> 4444); Next hop -> Node 1111
[2017-07-04 23:22:08.311930] Link to 3333: 31815 packets sent, 14994 packets lost, loss rate 0.47
[2017-07-04 23:22:08.367990] Link to 4444: 1505 packets sent, 1284 packets lost, loss rate 0.85

.
.
.
[2017-07-04 23:22:12.152473] Node 3333 Routing Table
- (0.0 -> 1111);
- (0.51 -> 4444); Next hop -> Node 1111
- (0.0 -> 2222);
[2017-07-04 23:22:12.152603] Message sent from Node 3333 to Node 1111
[2017-07-04 23:22:12.152732] Message sent from Node 3333 to Node 4444
[2017-07-04 23:22:12.152837] Message sent from Node 3333 to Node 2222

.
.
.
2017-07-04 23:22:12.356751] Node 4444 Routing Table
- (0.0 -> 3333);
- (0.0 -> 1111); Next hop -> Node 3333
- (0.0 -> 2222);
[2017-07-04 23:22:12.356898] Message received from Node 2222 to Node 4444