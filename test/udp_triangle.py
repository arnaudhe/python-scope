import socket
import time

UDP_IP   = "127.0.0.1"
UDP_PORT = 9000

print "UDP target IP:", UDP_IP
print "UDP target port:", UDP_PORT

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

count = 0

while True:
    message = '{};{};{};{}'.format(count, (count + 5) % 10, ((count / 5) * 10), ((((count + 2) % 10) / 5) * 10))
    print "send " + message
    sock.sendto(message, (UDP_IP, UDP_PORT))
    count = (count + 1) % 10;
    time.sleep(0.05)