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


# --- NEW: ASN Blacklist for Impractical Targets ---
# Keywords (case-insensitive) for ASNs that are not worth attacking directly.
IMPRACTICAL_ASN_KEYWORDS = [
    "CLOUDFLARE",
    "GOOGLE",
    "AMAZON-02",  # AWS
    "MICROSOFT-CORP",  # Azure
    "AKAMAI",
    "FASTLY",
    "INCAPSULA",
    "OVH"
]


# ... (keep utility functions like resolve_to_ipv4)

# --- NEW: IP REPUTATION CHECKER ---
def check_ip_reputation(target_ip):
    """
    Checks if an IP belongs to a known, heavily protected network (e.g., Cloudflare).

    :param target_ip: The IP address to check.
    :return: A tuple (is_impractical, description_string).
    """
    try:
        obj = IPWhois(target_ip)
        results = obj.lookup_whois()
        asn_description = results.get('asn_description', '').upper()

        for keyword in IMPRACTICAL_ASN_KEYWORDS:
            if keyword in asn_description:
                return (True, asn_description)  # Impractical target found

        return (False, asn_description)  # Practical target
    except Exception:
        # If the lookup fails for any reason, assume it's a practical target
        # to avoid accidentally skipping a vulnerable server.
        return (False, "ASN Lookup Failed")


# --- UPDATED: PRE-ATTACK RECONNAISSANCE MODULE ---
# ... (keep port_scan_worker, open_ports, ports_lock)

def run_port_scan(target_url, ports_to_scan, threads=100):
    """
    Manages a multi-threaded TCP port scan and performs an ASN reputation check.

    :return: A dictionary of results, keyed by IP address.
    """
    ips = counter_strike_helper.get_target_ips(target_url)
    if not ips:
        print(f"[RECON] Could not resolve {target_url}. Aborting scan.")
        return {}

    scan_results = {}

    print("[RECON] Starting ASN reputation and port scan...")
    for ip in ips:
        # --- NEW: Perform reputation check first ---
        is_impractical, asn_desc = check_ip_reputation(ip)
        print(f"[RECON] IP: {ip} | ASN: {asn_desc} | Impractical: {is_impractical}")

        # Initialize results for this IP
        scan_results[ip] = {
            "is_impractical": is_impractical,
            "asn": asn_desc,
            "open_ports": []
        }

        # Skip the detailed port scan if the target is deemed impractical
        if is_impractical:
            print(f"[RECON] Skipping detailed port scan for impractical target {ip}.")
            continue

        # ... (The port scanning logic is the same)
        global open_ports
        open_ports = []
        port_queue = Queue()
        for port in ports_to_scan: port_queue.put(port)
        for _ in range(threads):
            t = threading.Thread(target=port_scan_worker, args=(ip, port_queue))
            t.daemon = True
            t.start()
        port_queue.join()

        scan_results[ip]["open_ports"] = sorted(open_ports)

    print("-" * 60)
    print("[RECON] Full reconnaissance complete.")
    return scan_results

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