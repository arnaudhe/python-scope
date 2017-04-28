import socket
import time

UDP_IP   = "127.0.0.1"
UDP_PORT = 9000
MESSAGE  = "-4.5"

print "UDP target IP:", UDP_IP
print "UDP target port:", UDP_PORT
print "message:", MESSAGE

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

count = 0

while True:
    print "send {}".format(count)
    sock.sendto(str(count), (UDP_IP, UDP_PORT))
    count = count + 1
    if (count == 10):
        count = 0
    time.sleep(0.01)