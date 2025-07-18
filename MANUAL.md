# William's Battery: Operational Manual & Strategic Guide
Version: 2.0 (As of Integration of Reconnaissance and Advanced L7 Attacks)

Author: qing10101

Classification: For Educational & Authorized Testing Use Only

## 1.0 Introduction
William's Battery is a modular, multi-threaded toolkit designed for advanced Denial of Service (DoS) simulation and network stress-testing. Unlike traditional DoS tools that focus on a single attack vector, this platform orchestrates a blended, multi-layered assault, targeting a subject's network infrastructure from Layer 3 (Network) to Layer 7 (Application) simultaneously.

This document outlines the tool's architecture, operational workflows, and the strategic purpose behind its various modules and attack profiles.

## 2.0 Core Architecture
The tool is built on a modular, three-part architecture to ensure maintainability and extensibility.

**main.py (The Control Panel)**: This is the user-facing entry point. It handles all user interaction, presents strategic options, and orchestrates the high-level execution of reconnaissance tasks and attack profiles. It acts as the "commander."

**recon_helper.py (The Intelligence Unit)**: This module contains all functions related to information gathering and pre-attack analysis. Its purpose is to build a clear picture of the target's infrastructure before an attack is launched.

Capabilities: Port Scanning, Origin IP Discovery (via Subdomain, MX, and SPF record analysis), and Network Owner (ASN) lookups.

**counter_strike_helper.py (The Arsenal)**: This module contains the core logic for every implemented attack vector. Each attack is designed as a self-contained, multi-threaded "worker pool" that can be launched, paused, and stopped on command.

Capabilities: A comprehensive suite of L3/L4 (SYN, ACK, XMAS, UDP, etc.) and L7 (H2 Reset, POST Flood, Slowloris, etc.) attack functions.

## 3.0 Operational Workflows
The tool offers two primary modes of operation, accessible from the main menu.

### 3.1 Workflow 1: Reconnaissance & Discovery
This workflow should be the first step in any engagement against an unknown or proxied target. Its goal is to unmask the target's true infrastructure.

**Procedure**:

Launch the tool and select Option 2: Run Reconnaissance / Discovery.

Select Option 2: Discover Origin IP.

The tool will execute a series of passive and active checks:

It resolves the target domain to identify the current public-facing IPs (likely a CDN/proxy).

It queries for MX and TXT (SPF) records to find associated infrastructure IPs.

It performs a high-speed, multi-threaded brute-force scan against a wordlist of common subdomains.

For every discovered IP, it performs an ASN lookup to identify the network owner (e.g., CLOUDFLARENET, AMAZON-02, COMCAST-7922).

**Analysis**: The tool presents a final report listing all IPs found that are not part of the known proxy network. An IP belonging to a standard cloud provider (AWS, GCP) or a business/residential ISP is a high-confidence candidate for the true origin server.

Action: The operator can then use this discovered IP as the direct target for an attack, completely bypassing the CDN/WAF defenses.

### 3.2 Workflow 2: Launching an Attack
This workflow executes the stress test or simulated attack.

**Procedure**:

Launch the tool and provide the target (either a domain name or a direct IP address discovered via recon).

Configure Anonymity (Optional): The tool will prompt to enable the SOCKS Proxy (Tor).

If Yes, it performs a connection check. If successful, all compatible L7 attacks (HTTP POST, Slowloris, WebSocket) will be routed through the Tor network, appearing to come from distributed global IPs.

If No, all attacks will originate from the operator's IP.

Select a Blended Attack Profile or a Targeted L7 Attack.

## 4.0 Attack Profiles & Strategic Purpose
The tool provides several pre-configured profiles, each designed for a specific strategic purpose.

### 4.1 Profile 1: Full Scale Counterstrike (The Siege)
**Objective**: To apply maximum, sustained, multi-layered pressure on a target to test its overall resilience and the effectiveness of its mitigation systems.

**Methodology**: Launches all available attack vectors simultaneously with a high (but sustainable) number of threads. It is a resource-intensive "kitchen sink" assault designed to find any possible weakness.

**Vectors Used**: UDP, SYN, ACK, XMAS, ICMP, TCP Fragmentation, DNS Query, Cache-Busting GET, POST, Slowloris, and H2 Rapid Reset.

**Best Use Case**: Comprehensive stress-testing of a hardened server in a lab environment.

### 4.2 Profile 2: Fast Counterstrike (The Surgical Strike)
**Objective**: To cause maximum disruption to a target's core services in the shortest possible time.

**Methodology**: Focuses exclusively on the most efficient and high-impact L7 and state-exhaustion attacks. It uses a moderate number of threads optimized for burst performance.

**Vectors Used**: DNS Query Flood, SYN Flood, HTTP POST Flood, and H2 Rapid Reset.

**Best Use Case**: Testing a server's immediate reaction to a sudden, intense application-layer assault.

### 4.3 Profile 3: Level 2 Penetrator
**Objective**: To defeat a server with intermediate hardening (e.g., basic rate-limiting and connection limits).

**Methodology**: A specialized profile that combines high-intensity L7 attacks (especially those routed through Tor to bypass IP-based rules) with spoofed L4 floods designed to stress firewall state tables.

**Best Use Case**: Simulating an advanced adversary attempting to circumvent common, non-proxy-based defenses.

### 4.4 Profile 4: Adaptive & Recon-led Strikes
**Adaptive Strike**: An intelligent mode that runs a "Fast Scale" attack but is managed by a controller that pauses the assault when the target is down and resumes it upon recovery. Ideal for long-duration, resource-efficient testing.

**Recon-led Strike**: A workflow that first performs a port scan and then launches a "Fast Scale" attack targeting only the discovered open ports, ensuring maximum efficiency.

## 5.0 Operational Best Practices
**Always Run with sudo**: The majority of the network-layer attacks require raw socket access, which necessitates root/administrator privileges.

**Use Virtual Environments**: Always run the tool within its dedicated Python virtual environment (venv) to ensure all dependencies are correct and isolated.

**Monitor Local Resources**: The "Full Scale" and "Level 2 Penetrator" profiles are extremely intensive. Monitor your own machine's CPU and memory usage to ensure the tool is not being bottlenecked by local resources.

**Use Tor for Evasion**: When testing a target with a WAF, enabling the Tor proxy is crucial for bypassing simple IP-based blocking rules and simulating a distributed attack. Ensure the Tor service is running before launching the tool.

**Recon First, Attack Second**: For any target behind a CDN or proxy, always run the Origin IP Discovery workflow first. Attacking the proxy directly is futile.