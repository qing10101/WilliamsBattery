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
-   **Adaptive Attack Controller:** An intelligent mode that monitors the target's status, automatically pausing the attack when the target is down and resuming it upon recovery to maximize efficiency.
-   **Anonymity via Tor:** Integrates with the Tor network to route application-layer attacks (HTTP POST, Slowloris) through a SOCKS proxy, masking the operator's real IP address for those vectors.
-   **Comprehensive Attack Vectors:**
    -   **Layer 7 (Application):**
        -   **HTTP/2 Rapid Reset:** A highly efficient attack exploiting the H2 protocol to cause maximum CPU load with minimal bandwidth.
        -   **HTTP POST Flood:** Bypasses caches by sending randomized POST data, forcing expensive server-side processing.
        -   **Slowloris:** A stealthy "low and slow" attack that exhausts the server's connection pool with minimal traffic.
        -   **DNS Query Flood:** A smart attack that floods the target with valid but randomized DNS queries, overwhelming the DNS resolver application.
    -   **Layer 3/4 (Network & Transport):**
        -   **TCP SYN Flood:** The classic attack to exhaust the server's connection state table.
        -   **TCP Fragmentation Attack:** A memory exhaustion attack that targets firewalls and OS network stacks by sending incomplete packet fragments.
        -   **UDP Flood:** A volumetric attack to saturate network bandwidth.
        -   **ICMP Flood:** A classic "Ping Flood" for network saturation.
-   **Configurable Attack Profiles:** Choose from pre-configured strategies for different testing scenarios.

## ⚙️ Prerequisites & Installation

-   Python 3.8 or newer.
-   `pip` for installing packages.
-   **Root or Administrator privileges** to craft and send raw packets.
-   **Tor Service:** To use the anonymity feature, the Tor service must be installed and running on the machine.

**Installation Steps:**

1.  **Install the Tor Service:**
    *   **On macOS (via Homebrew):**
        ```bash
        brew install tor
        brew services start tor
        ```
    *   **On Debian/Ubuntu:**
        ```bash
        sudo apt update && sudo apt install tor
        sudo systemctl start tor
        ```

2.  **Clone the project repository:**
    ```bash
    git clone https://github.com/qing10101/WilliamsBattery.git
    cd WilliamsBattery
    ```

3.  **Create a virtual environment (Recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

4.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## 🕹️ Usage

The script must be run with `sudo` (on Linux/macOS) or as an Administrator (on Windows) for most attacks to function correctly.

1.  **Activate your virtual environment:**
    ```bash
    source .venv/bin/activate
    ```
2.  **Run the main script:**
    ```bash
    sudo python3 main.py
    ```

The script will then guide you through selecting a target, enabling Tor, and choosing an attack profile.

## 🛡️ Attack Profiles Explained

The toolkit offers three distinct strategic profiles, each combining different attack vectors.

### 1. Full Scale Counterstrike (The Siege)

This profile is a comprehensive, "kitchen sink" assault designed for maximum pressure across the entire technology stack. It is a long-running siege meant to test long-term resilience.

-   **Strategy:** Overwhelm everything at once.
-   **Includes:** `UDP Flood`, `SYN Flood`, `ICMP Flood`, `DNS Query Flood`, **`TCP Fragmentation`**, **`HTTP POST Flood`**, **`Slowloris`**, and **`HTTP/2 Rapid Reset`**.

### 2. Fast Counterstrike (The Surgical Strike)

This profile is a short, intense burst designed for maximum impact in minimum time. It prioritizes the most efficient and modern attack vectors.

-   **Strategy:** Cripple the target's services quickly and effectively.
-   **Includes:** `DNS Query Flood`, `SYN Flood`, **`HTTP POST Flood`**, and **`HTTP/2 Rapid Reset`**.

### 3. Adaptive Counterstrike (The Smart Strike)

This profile uses the potent "Fast Scale" vector set but adds an intelligent controller. It's designed for efficient, long-running tests where attacker resources are a consideration.

-   **Strategy:** Apply pressure only when the target is online, conserving resources when it's down.
-   **Includes:** The same powerful vector set as the Fast Counterstrike, managed by the adaptive controller.

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.