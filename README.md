# William's Battery - A Multi-Vector DoS Toolkit

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Educational Use](https://img.shields.io/badge/purpose-educational-lightgrey.svg)

William's Battery is a powerful, multi-threaded Python-based toolkit designed for demonstrating and researching various Denial of Service (DoS) attack vectors. It can launch blended, simultaneous attacks and features an adaptive mode that intelligently adjusts the attack based on the target's status.

## ⚠️ Legal & Ethical Disclaimer

> **This tool is intended for educational and research purposes ONLY.**
>
> Using this software to attack any server, network, or service that you do **not** have explicit, written permission to test is **illegal**. The author is not responsible for any damage, harm, or legal consequences resulting from the misuse of this tool.
>
> **Always respect the law and ethical principles. Use responsibly in a controlled lab environment.**

## 🚀 Features

-   **Blended, Multi-Threaded Attacks:** Launches UDP, TCP SYN, ICMP, and HTTP floods simultaneously.
-   **Efficient Worker Pool Model:** Uses a professional, fixed-thread-pool model for high performance and low resource consumption.
-   **Multiple Flood Vectors:** UDP, TCP SYN, ICMP, and HTTP GET floods.
-   **Configurable Attack Profiles:**
    -   **Full Scale (Siege):** A prolonged, high-volume attack across a wide range of vectors.
    -   **Fast Scale (Surgical Strike):** A short, intense, and focused attack on critical services.
    -   **Adaptive (Smart Strike):** An intelligent attack that monitors the target's status, automatically pausing the flood when the target is down and resuming it upon recovery. This maximizes efficiency and conserves attacker resources.

## ⚙️ Prerequisites & Installation

-   Python 3.8 or newer.
-   `pip` for installing packages.
-   **Root or Administrator privileges** to craft and send raw packets with Scapy.

**Installation Steps:**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/qing10101/WilliamsBattery.git
    cd WilliamsBattery
    ```

2. **Install requirements:**
    ```bash
    pip install -r requirements.txt
    ```

## 🕹️ Usage

The script must be run with `sudo` (on Linux/macOS) or as an Administrator (on Windows).

```bash
sudo python3 main.py
```

The script will then guide you through selecting a target and an attack profile.

## 🛡️ Attack Profiles Explained

### 1. Full Scale Counterstrike (Siege)
A sustained, overwhelming assault designed to test long-term infrastructure resilience.

### 2. Fast Counterstrike (Surgical Strike)
A quick, high-impact burst on critical services to simulate a hit-and-run attack.

### 3. Adaptive Counterstrike (Smart Strike)
The most advanced profile. It launches an attack and a background controller that periodically checks the target's health.
-   **If Target is UP:** The attack continues at full force.
-   **If Target is DOWN:** The attack automatically pauses, saving your bandwidth and CPU.
-   **If Target Recovers:** The attack instantly resumes.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.