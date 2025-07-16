# William's Battery - A Multi-Vector DoS Toolkit

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Educational Use](https://img.shields.io/badge/purpose-educational-lightgrey.svg)

William's Battery is a powerful, multi-threaded Python-based toolkit for demonstrating and researching a wide array of Denial of Service (DoS) attack vectors. It launches sophisticated, blended attacks to simulate complex cyber-attack scenarios for security testing and network infrastructure stress-testing.

## ⚠️ Legal & Ethical Disclaimer

> **This tool is intended for educational and research purposes ONLY.**
>
> Using this software to attack any server, network, or service that you do **not** have explicit, written permission to test is **illegal**. The author is not responsible for any damage, harm, or legal consequences resulting from the misuse of this tool.
>
> **Always respect the law and ethical principles. Use responsibly in a controlled lab environment.**

## 🚀 Features

-   **Blended, Multi-Threaded Attacks:** Launches multiple attack vectors simultaneously to create a complex and effective attack simulation.
-   **Intelligent & Adaptive Modes:**
    -   **Adaptive Controller:** Monitors the target's status, automatically pausing the attack when the target is down and resuming it upon recovery to maximize efficiency.
    -   **Recon-led Strikes:** Can perform a pre-attack port scan and then launch a surgical assault targeting only the discovered open services.
    -   **Origin IP Discovery:** Includes tools to find a server's real IP address behind common proxy services by scanning MX records and subdomains.
-   **Anonymity via Tor:** Integrates with the Tor network to route application-layer attacks through a SOCKS proxy, masking the operator's real IP address for those vectors.
-   **Auto-Detect Network Interface:** Automatically identifies the correct network interface for Scapy-based attacks, preventing silent failures in complex network environments.
-   **Comprehensive Attack Vectors:**
    -   **Layer 7 (Application):** HTTP/2 Rapid Reset, HTTP POST Flood, Cache-Busting GET Flood, WebSocket Flood, Slowloris, DNS Query Flood.
    -   **Layer 3/4 (Network & Transport):** TCP SYN, ACK, & XMAS Floods, TCP Fragmentation Attack, UDP & ICMP Floods.

## ⚙️ Prerequisites & Installation

-   Python 3.8 or newer.
-   `pip` for installing packages.
-   **Root or Administrator privileges** to craft and send raw packets.
-   **Tor Service (Optional):** To use the anonymity feature, the Tor service must be installed and running.

**Installation Steps:**

1.  **Install the Tor Service (Optional):**
    *   **On macOS (via Homebrew):** `brew install tor && brew services start tor`
    *   **On Debian/Ubuntu:** `sudo apt update && sudo apt install tor && sudo systemctl start tor`

2.  **Clone the project repository and set up the environment:**
    ```bash
    git clone https://github.com/qing10101/WilliamsBattery.git
    cd WilliamsBattery
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 🕹️ Usage

The script must be run with `sudo` (on Linux/macOS) or as an Administrator (on Windows).

1.  **Activate your virtual environment:** `source .venv/bin/activate`
2.  **Run the main script:** `sudo python3 main.py`

The script will guide you through selecting a target and an action, such as launching an attack profile or running reconnaissance.

## 🛡️ Attack Profiles Explained

The toolkit offers several distinct strategic profiles, each combining different attack vectors with carefully tuned thread counts for optimal performance.

### 1. Full Scale Counterstrike (The Siege)

This profile is a comprehensive, "kitchen sink" assault designed for maximum pressure across the entire technology stack. It is a long-running siege meant to test long-term resilience. **Warning: This profile is extremely resource-intensive on the attacking machine.**

-   **Strategy:** Overwhelm everything at once with a massive, but sustainable, number of concurrent threads.
-   **Includes:** Nearly all implemented attack vectors, from L3 volumetric floods to sophisticated L7 application-layer assaults.

### 2. Fast Counterstrike (The Surgical Strike)

This profile is a short, intense burst designed for maximum impact in minimum time. It prioritizes the most efficient and modern attack vectors.

-   **Strategy:** Cripple the target's services quickly and effectively.
-   **Includes:** `DNS Query Flood`, `SYN Flood`, `HTTP POST Flood`, and `HTTP/2 Rapid Reset`.

### 3. Level 2 Penetrator (The Hardened Target Assault)

A specially designed profile to overwhelm servers with intermediate defenses like basic rate-limiting. It focuses on high-intensity L7 attacks and spoofed L4 floods.

-   **Strategy:** Bypass common, simple defenses with more sophisticated techniques.
-   **Includes:** `H2 Rapid Reset`, `Tor-routed POST and Slowloris floods`, and spoofed `SYN` and `TCP Fragmentation` attacks.

*(Note: Other profiles like Adaptive Strike and Recon-led Strike are also available.)*

## 📄 `requirements.txt`

Your `requirements.txt` file should contain:
```
scapy
h2
pysocks
netifaces
dnspython
websockets
```
*(Note: Use `pip freeze > requirements.txt` to generate a file with pinned versions for reproducible builds.)*

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.