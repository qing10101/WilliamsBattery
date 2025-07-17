# William's Battery - A Multi-Vector DoS Toolkit

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Educational Use](https://img.shields.io/badge/purpose-educational-lightgrey.svg)

William's Battery is a powerful, multi-threaded Python-based toolkit for demonstrating and researching a wide array of Denial of Service (DoS) attack vectors. It launches sophisticated, blended attacks and offers a suite of reconnaissance tools to simulate a complete cyber-attack scenario for security testing and network infrastructure stress-testing.

## ⚠️ Legal & Ethical Disclaimer

> **This tool is intended for educational and research purposes ONLY.**
>
> Using this software to attack any server, network, or service that you do **not** have explicit, written permission to test is **illegal**. The author is not responsible for any damage, harm, or legal consequences resulting from the misuse of this tool.
>
> **Always respect the law and ethical principles. Use responsibly in a controlled lab environment.**

## 🚀 Features

-   **Modular Architecture:** The tool is cleanly separated into attack (`counter_strike_helper.py`), reconnaissance (`recon_helper.py`), and control (`main.py`) modules for easy maintenance and extension.
-   **Blended, Multi-Threaded Attacks:** Launches multiple attack vectors simultaneously in pre-configured profiles (Siege, Surgical Strike, etc.).
-   **Advanced Intelligence & Reconnaissance:**
    -   **Origin IP Discovery:** Includes tools to find a server's real IP address behind common proxies by scanning MX records, SPF records, and a massive list of potential subdomains.
    -   **ASN Lookups:** Automatically enriches discovered IPs with network owner information to provide crucial context.
    -   **Port Scanning:** Can perform a pre-attack port scan to identify open services for more efficient, targeted attacks.
-   **Sophisticated Attack Vectors:**
    -   **Layer 7 (Application):**
        -   **Targeted "Heavy" POST Flood:** A surgical attack that allows the user to target a specific, computationally expensive endpoint (like a search API) with custom POST data.
        -   **HTTP/2 Rapid Reset:** A highly efficient attack exploiting the H2 protocol to cause maximum CPU load.
        -   **WebSocket Flood:** A state-exhaustion attack targeting modern real-time applications.
        -   And many more, including Slowloris, Cache-Busting GETs, and DNS Query Floods.
    -   **Layer 3/4 (Network & Transport):**
        -   A full suite of classic floods, including TCP SYN, ACK, XMAS, and Fragmentation attacks, plus UDP and ICMP floods.
-   **Anonymity & Evasion:** Integrates with the Tor network to route application-layer attacks through a SOCKS proxy, masking the operator's IP and bypassing simple blocks.

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

The script will then present a top-level menu allowing you to choose between launching a blended attack profile, running reconnaissance, or launching a targeted L7 attack.

## 📄 `requirements.txt`

Your `requirements.txt` file should contain:
```
scapy
h2
pysocks
netifaces
dnspython
websockets
ipwhois
```
*(Note: Use `pip freeze > requirements.txt` to generate a file with pinned versions for reproducible builds.)*

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.