# recon_helper.py - Reconnaissance and Discovery Toolkit

from ipwhois import IPWhois  # NEW: Import the ipwhois library
import re # NEW: Import the regular expression module
import socket
import threading
from queue import Queue
import dns.resolver
import counter_strike_helper  # We still need this for the IP resolution helper

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


def load_subdomains(filename="subdomains.txt"):
    """Loads a list of subdomains from a wordlist file."""
    try:
        with open(filename, 'r') as f:
            subdomains = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        if not subdomains:
            print(f"[ERROR] Subdomain wordlist '{filename}' is empty or not found.")
            return []
        print(f"[INFO] Loaded {len(subdomains)} subdomains from wordlist.")
        return subdomains
    except FileNotFoundError:
        print(f"[ERROR] Subdomain wordlist not found: {filename}")
        print("[HINT]  Download a wordlist and save it as 'subdomains.txt' in your project directory.")
        return []


def subdomain_scan_worker(target_domain, subdomain_queue, found_ips_set, lock):
    """Worker thread that checks a single subdomain for its IP address."""
    # This worker function is already perfect and needs no changes.
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


# --- THIS IS THE UPDATED FUNCTION ---
def find_origin_ip_by_subdomains(target_domain, threads=50):
    """
    Performs a multi-threaded subdomain scan using a wordlist file
    to find non-proxied servers.
    """
    print(f"[RECON] Preparing to scan for subdomains on {target_domain} using wordlist...")

    # Load subdomains from the file instead of a hardcoded list
    subdomains_to_check = load_subdomains("subdomains.txt")
    if not subdomains_to_check:
        return set()  # Return an empty set if the wordlist couldn't be loaded

    found_ips = set()
    lock = threading.Lock()
    subdomain_queue = Queue()

    for sub in subdomains_to_check:
        subdomain_queue.put(sub)

    print(f"[RECON] Starting scan with {threads} threads...")
    for _ in range(threads):
        t = threading.Thread(
            target=subdomain_scan_worker,
            args=(target_domain, subdomain_queue, found_ips, lock)
        )
        t.daemon = True
        t.start()

    subdomain_queue.join()
    return found_ips


# --- NEW: SPF RECORD ANALYSIS MODULE ---

def _parse_spf_record(domain, found_ips_set, recursion_depth=0):
    """
    A recursive helper function to parse an SPF record, following 'include'
    directives and extracting IPv4 addresses.
    """
    # Protect against infinite recursion loops in misconfigured SPF records
    if recursion_depth > 5:
        return

    try:
        # Query for TXT records for the given domain
        txt_records = dns.resolver.resolve(domain, 'TXT')

        for record in txt_records:
            record_str = record.strings[0].decode('utf-8')

            # Check if this TXT record is actually an SPF record
            if record_str.startswith("v=spf1"):
                print(f"  [+] Found SPF record for {domain}: {record_str[:60]}...")

                # Use regular expressions to find all ip4 addresses
                ipv4s = re.findall(r'ip4:([0-9\./]+)', record_str)
                for ip in ipv4s:
                    found_ips_set.add(ip)  # Note: this might include CIDR ranges like /24

                # Find all 'include' mechanisms and recursively parse them
                includes = re.findall(r'include:(\S+)', record_str)
                for included_domain in includes:
                    _parse_spf_record(included_domain, found_ips_set, recursion_depth + 1)

    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
        # It's normal for sub-domains in the include chain not to have TXT records
        pass
    except Exception as e:
        print(f"  [!] Error parsing SPF for {domain}: {e}")


def find_origin_ip_by_spf(target_domain):
    """
    Finds potential origin IPs by recursively parsing a domain's SPF records.

    :param target_domain: The domain to investigate.
    :return: A set of potential IP addresses found.
    """
    print(f"[RECON] Analyzing SPF records for {target_domain}...")
    found_ips = set()
    _parse_spf_record(target_domain, found_ips)

    # Clean up the results - some SPF records use CIDR notation (e.g., 1.2.3.0/24).
    # For simplicity, we'll just take the base IP. A more advanced tool might expand the range.
    final_ips = {ip.split('/')[0] for ip in found_ips}

    return final_ips


# --- NEW: ASN (NETWORK OWNER) LOOKUP MODULE ---
def get_ip_asn(ip_address):
    """
    Performs a lookup to find the ASN (Autonomous System Number) and
    description for an IP address. This reveals the owner of the network block.

    :param ip_address: The IP address string to look up.
    :return: A formatted string like "AS15169 - GOOGLE", or "N/A".
    """
    try:
        # Create an IPWhois object for the target IP
        obj = IPWhois(ip_address)
        # Perform the lookup. lookup_rdap() is modern and recommended.
        results = obj.lookup_rdap()

        # Extract the ASN and its description
        asn = results.get('asn', 'N/A')
        description = results.get('asn_description', 'Unknown')

        return f"AS{asn} - {description}"

    except Exception:
        # If the lookup fails for any reason, return gracefully.
        return "ASN Lookup Failed"
