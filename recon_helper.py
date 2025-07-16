# recon_helper.py - Reconnaissance and Discovery Toolkit

import socket
import threading
from queue import Queue
import dns.resolver
import counter_strike_helper  # We still need this for the IP resolution helper

# --- A list of common subdomains to check ---
COMMON_SUBDOMAINS = [
    "mail", "webmail", "ftp", "cpanel", "direct", "dev", "staging", "test", "vpn",
    "blog", "m", "shop", "api", "dns", "email", "mail2", "owa", "portal", "admin",
    "autodiscover", "support", "files", "images", "static", "www", "smtp", "pop"
]

# --- 1. PORT SCANNING MODULE ---

# Thread-safe list to store the results of the scan
open_ports = []
ports_lock = threading.Lock()


def port_scan_worker(target_ip, port_queue):
    """Worker that takes port numbers from a queue and checks if they are open."""
    while not port_queue.empty():
        try:
            port = port_queue.get()
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex((target_ip, port)) == 0:
                    with ports_lock:
                        open_ports.append(port)
            port_queue.task_done()
        except Exception:
            port_queue.task_done()
            continue


def run_port_scan(target_url, ports_to_scan, threads=100):
    """Manages a multi-threaded TCP port scan to find open ports."""
    ips = counter_strike_helper.get_target_ips(target_url)
    if not ips:
        print(f"[RECON] Could not resolve {target_url}. Aborting scan.")
        return []

    target_ip = ips[0]
    print(f"[RECON] Starting TCP port scan on {target_ip}...")

    global open_ports
    open_ports = []
    port_queue = Queue()
    for port in ports_to_scan:
        port_queue.put(port)

    for _ in range(threads):
        t = threading.Thread(target=port_scan_worker, args=(target_ip, port_queue))
        t.daemon = True
        t.start()

    port_queue.join()

    print(f"[RECON] Scan complete. Found {len(open_ports)} open TCP ports.")
    return sorted(open_ports)


# --- 2. ORIGIN IP DISCOVERY MODULE ---

def find_origin_ip_by_mx(target_domain):
    """Finds potential origin IPs by looking up the domain's MX records."""
    print(f"[RECON] Checking MX records for {target_domain}...")
    potential_ips = set()
    try:
        mx_records = dns.resolver.resolve(target_domain, 'MX')
        if not mx_records: return set()

        for record in mx_records:
            mail_server = str(record.exchange).rstrip('.')
            print(f"  [+] Found mail server: {mail_server}")
            try:
                mail_ips = dns.resolver.resolve(mail_server, 'A')
                for ip in mail_ips:
                    potential_ips.add(str(ip))
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                continue
    except Exception as e:
        print(f"  [!] Could not query MX records: {e}")
    return potential_ips


def subdomain_scan_worker(target_domain, subdomain_queue, found_ips_set, lock):
    """Worker thread that checks a single subdomain for its IP address."""
    while not subdomain_queue.empty():
        subdomain = subdomain_queue.get()
        full_domain = f"{subdomain}.{target_domain}"
        try:
            answers = dns.resolver.resolve(full_domain, 'A')
            for ip in answers:
                with lock:
                    if str(ip) not in found_ips_set:
                        print(f"  [+] Subdomain Hit: {full_domain} -> {ip}")
                        found_ips_set.add(str(ip))
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
            pass
        finally:
            subdomain_queue.task_done()


def find_origin_ip_by_subdomains(target_domain, threads=50):
    """Performs a multi-threaded subdomain scan to find non-proxied servers."""
    print(f"[RECON] Scanning for common subdomains on {target_domain}...")
    found_ips = set()
    lock = threading.Lock()
    subdomain_queue = Queue()

    for sub in COMMON_SUBDOMAINS:
        subdomain_queue.put(sub)

    for _ in range(threads):
        t = threading.Thread(target=subdomain_scan_worker, args=(target_domain, subdomain_queue, found_ips, lock))
        t.daemon = True
        t.start()

    subdomain_queue.join()
    return found_ips