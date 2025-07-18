# recon_helper.py - Reconnaissance and Discovery Toolkit

import socket
import threading
from queue import Queue
import dns.resolver
import re
from ipwhois import IPWhois
import counter_strike_helper  # For get_target_ips

# --- 1. PORT SCANNING MODULE ---
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

def run_port_scan(target_url, ports_to_scan, threads=200):
    """Manages a multi-threaded TCP port scan to find open ports."""
    ips = counter_strike_helper.get_target_ips(target_url)
    if not ips:
        print(f"[RECON] Could not resolve {target_url}. Aborting scan.")
        return []
    target_ip = ips[0]
    print(f"[RECON] Starting TCP port scan on {target_ip} for {len(ports_to_scan)} ports...")
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
        for record in mx_records:
            mail_server = str(record.exchange).rstrip('.')
            mail_ips = counter_strike_helper.resolve_to_ipv4(mail_server)
            potential_ips.update(mail_ips)
    except Exception as e:
        print(f"  [!] Could not query MX records: {e}")
    return potential_ips


def load_subdomains(filename="subdomains.txt"):
    """Loads a list of subdomains from a wordlist file."""
    try:
        with open(filename, 'r') as f:
            subdomains = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        if not subdomains: return []
        print(f"[INFO] Loaded {len(subdomains)} subdomains from wordlist.")
        return subdomains
    except FileNotFoundError:
        print(f"[ERROR] Subdomain wordlist not found: {filename}")
        return []

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
    """Performs a multi-threaded subdomain scan using a wordlist file."""
    print(f"[RECON] Preparing to scan for subdomains on {target_domain}...")
    subdomains_to_check = load_subdomains()
    if not subdomains_to_check: return set()
    found_ips, lock, subdomain_queue = set(), threading.Lock(), Queue()
    for sub in subdomains_to_check: subdomain_queue.put(sub)
    for _ in range(threads):
        t = threading.Thread(target=subdomain_scan_worker, args=(target_domain, subdomain_queue, found_ips, lock))
        t.daemon = True
        t.start()
    subdomain_queue.join()
    return found_ips


def _parse_spf_record(domain, found_ips_set, recursion_depth=0):
    if recursion_depth > 5:
        return
    try:
        txt_records = dns.resolver.resolve(domain, 'TXT')
        for record in txt_records:
            record_str = record.strings[0].decode('utf-8')
            if record_str.startswith("v=spf1"):
                ipv4s = re.findall(r'ip4:([0-9\./]+)', record_str)
                for ip in ipv4s:
                    found_ips_set.add(ip)
                includes = re.findall(r'include:(\S+)', record_str)
                for included_domain in includes:
                    _parse_spf_record(included_domain, found_ips_set, recursion_depth + 1)
    except Exception:
        pass


def find_origin_ip_by_spf(target_domain):
    """Finds potential origin IPs by recursively parsing a domain's SPF records."""
    print(f"[RECON] Analyzing SPF records for {target_domain}...")
    found_ips = set()
    _parse_spf_record(target_domain, found_ips)
    return {ip.split('/')[0] for ip in found_ips}

def get_ip_asn(ip_address):
    """Performs a lookup to find the ASN and description for an IP address."""
    try:
        obj = IPWhois(ip_address)
        results = obj.lookup_rdap()
        return f"AS{results.get('asn', 'N/A')} - {results.get('asn_description', 'Unknown')}"
    except Exception:
        return "ASN Lookup Failed"