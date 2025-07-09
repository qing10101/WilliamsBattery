William's Battery - A Multi-Vector DoS Toolkit

![alt text](https://img.shields.io/badge/python-3.8%2B-blue)


![alt text](https://img.shields.io/badge/License-MIT-yellow.svg)


![alt text](https://img.shields.io/badge/purpose-educational-lightgrey.svg)

William's Battery is a powerful, multi-threaded Python-based toolkit designed for demonstrating and researching various Denial of Service (DoS) attack vectors. It can launch blended, simultaneous attacks to simulate a complex cyber-attack scenario for security testing and network infrastructure stress-testing.

The project was intended to serve as the "counterstrike" branch for an email scam identification software of a college SWE project.

⚠️ Legal & Ethical Disclaimer

This tool is intended for educational and research purposes ONLY.

Using this software to attack any server, network, or service that you do not have explicit, written permission to test is illegal. The author is not responsible for any damage, harm, or legal consequences resulting from the misuse of this tool.

Always respect the law and ethical principles. Use responsibly in a controlled lab environment.

🚀 Features

Blended, Multi-Threaded Attacks: Launches UDP, TCP SYN, ICMP, and HTTP floods simultaneously to create a complex and effective attack simulation.

Multiple Flood Vectors:

UDP Flood: Saturates bandwidth and exhausts UDP-based services.

TCP SYN Flood: Aims to exhaust the server's connection state table.

ICMP Flood: A classic "Ping Flood" to saturate the network.

HTTP GET Flood: Overwhelms web server applications (Layer 7).

Configurable Attack Profiles:

Full Scale Counterstrike (Siege): A prolonged, high-volume attack across a wide range of ports and vectors.

Fast Counterstrike (Surgical Strike): A short, intense, and focused attack on the most critical services for maximum immediate impact.

Modular and Readable Code: The attack logic is separated into a helper module for clarity and easy extension.

⚙️ Prerequisites & Installation

To run this tool, you will need:

Python 3.8 or newer.

pip for installing packages.

Root or Administrator privileges to craft and send raw packets with Scapy.

Installation Steps:

Clone the repository:

Generated bash
git clone https://github.com/your-username/williams-battery.git
cd williams-battery


Create a requirements.txt file in the project directory with the following content:

Generated code
scapy
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END

Install the required Python packages:

Generated bash
pip install -r requirements.txt
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END
🕹️ Usage

The script is run from the command line and will prompt you for the target and attack profile.

IMPORTANT: You must run the script with sudo (on Linux/macOS) or as an Administrator (on Windows) for the SYN and ICMP floods to work correctly.

Generated bash
sudo python3 main.py
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

The script will then guide you through the process:

Generated text
------------------------------------------------------------
WELCOME TO WILLIAM'S BATTERY ---- A CONVENIENT COUNTERSTRIKE TOOL
------------------------------------------------------------
This tool is for educational purposes ONLY. Use responsibly and legally.
Please Enter The Domain Name Of Your Target: example.com
Target: example.com

Select an attack profile:
  1: Full Scale Counterstrike (Long-running siege, all vectors)
  2: Fast Counterstrike (Short, intense, focused attack)

Please enter your option: 2
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Text
IGNORE_WHEN_COPYING_END
🛡️ Attack Profiles Explained
1. Full Scale Counterstrike (Siege)

This profile is designed for a sustained, overwhelming assault.

Duration: Long (e.g., 360 seconds per UDP attack).

Volume: Extremely high packet and request counts.

Scope: Broad. It targets a wide range of common ports for SYN floods and performs a UDP flood scan across the first 1024 ports.

Use Case: Simulating a persistent, large-scale DoS attack to test the long-term resilience of network infrastructure and mitigation systems.

2. Fast Counterstrike (Surgical Strike)

This profile is designed for a quick, high-impact burst.

Duration: Short (e.g., 60 seconds per UDP attack).

Volume: High, but lower than the siege profile, optimized for a fast-and-done attack.

Scope: Focused. It targets only the most critical service ports (Web, SSH, RDP, DNS) to maximize the chance of immediate disruption.

Use Case: Simulating a hit-and-run style attack or performing a quick stress test on primary services.

🏗️ Code Architecture

The project is structured for clarity and maintainability:

main.py: The entry point of the application. It handles user interaction (getting the target and profile choice) and calls the appropriate attack function.

counter_strike_helper.py: A module containing the core logic for each individual attack vector (attack_UDP, synflood, icmpflood, attack_http_flood). This separation of concerns makes the code easier to manage and extend.

🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

📄 License

This project is licensed under the MIT License. See the LICENSE file for details.
