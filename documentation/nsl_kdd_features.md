# NSL-KDD Dataset — Feature Engineering Notes

## Overview

CyberShield's ML classification pipeline is trained on the **NSL-KDD dataset**, a refined version of the KDD Cup 1999 dataset. This document explains how each of the 41 features is interpreted and how they map to real-world network packet behaviors. This is essential context for evaluating the ML model's classification decisions.

---

## Feature Categories

The 41 NSL-KDD features are grouped into four categories:

### Category 1 — Basic Connection Features (Features 1–9)
These are derived directly from the raw TCP/IP packet header fields.

| # | Feature | Type | Description |
|---|---------|------|-------------|
| 1 | `duration` | Continuous | Length (in seconds) of the connection |
| 2 | `protocol_type` | Categorical | Protocol: TCP, UDP, ICMP |
| 3 | `service` | Categorical | Network service on the destination (e.g., http, ftp, ssh) |
| 4 | `flag` | Categorical | Connection status flag (e.g., SF=normal, S0=SYN with no reply) |
| 5 | `src_bytes` | Continuous | Bytes sent from source to destination |
| 6 | `dst_bytes` | Continuous | Bytes sent from destination to source |
| 7 | `land` | Binary | 1 if source and destination IPs/ports are identical (land attack) |
| 8 | `wrong_fragment` | Continuous | Count of wrong fragments in the connection |
| 9 | `urgent` | Continuous | Count of urgent packets |

> **Example — Normal vs. DoS:** In a normal HTTP connection, `src_bytes` and `dst_bytes` will both be moderate (e.g., request=500B, response=5KB). In a DoS SYN flood, `src_bytes` is very high, `dst_bytes` is near zero (server never responds), and `flag` = S0.

---

### Category 2 — Content Features (Features 10–22)
These are derived from the application layer content of the packet payload.

| # | Feature | Type | Description |
|---|---------|------|-------------|
| 10 | `hot` | Continuous | Count of "hot" indicators (e.g., access to system files) |
| 11 | `num_failed_logins` | Continuous | Number of failed login attempts |
| 12 | `logged_in` | Binary | 1 if successfully logged in |
| 13 | `num_compromised` | Continuous | Count of "compromised" conditions |
| 14 | `root_shell` | Binary | 1 if root shell obtained |
| 15 | `su_attempted` | Binary | 1 if `su root` command was attempted |
| 16 | `num_root` | Continuous | Count of root accesses |
| 17 | `num_file_creations` | Continuous | Count of file creation operations |
| 18 | `num_shells` | Continuous | Count of shell prompts opened |
| 19 | `num_access_files` | Continuous | Count of operations on access control files |
| 20 | `num_outbound_cmds` | Continuous | Count of outbound commands in an FTP session |
| 21 | `is_host_login` | Binary | 1 if login belongs to the `host` list |
| 22 | `is_guest_login` | Binary | 1 if login is a guest login |

> **Example — U2R vs. Normal:** A U2R attack is strongly indicated by `root_shell=1`, `su_attempted=1`, `num_root > 0`. A normal user session has all of these at 0.

---

### Category 3 — Time-Based Traffic Features (Features 23–31)
Computed over a 2-second time window of connections to the **same destination host**.

| # | Feature | Type | Description |
|---|---------|------|-------------|
| 23 | `count` | Continuous | Connections to the same host in past 2 seconds |
| 24 | `srv_count` | Continuous | Connections to the same service in past 2 seconds |
| 25 | `serror_rate` | Continuous | % of connections with SYN errors |
| 26 | `srv_serror_rate` | Continuous | % of same-service connections with SYN errors |
| 27 | `rerror_rate` | Continuous | % of connections with REJ errors |
| 28 | `srv_rerror_rate` | Continuous | % of same-service connections with REJ errors |
| 29 | `same_srv_rate` | Continuous | % of connections to same service |
| 30 | `diff_srv_rate` | Continuous | % of connections to different services |
| 31 | `srv_diff_host_rate` | Continuous | % of connections to different hosts for same service |

> **Example — Probe vs. Normal:** A port scan (PROBE) shows `count` very high, `diff_srv_rate` very high (scanning many ports), and `same_srv_rate` near 0. Normal browsing shows low `count` and `same_srv_rate` near 1.

---

### Category 4 — Host-Based Traffic Features (Features 32–41)
Computed over a window of 100 connections to the **same destination host**.

| # | Feature | Type | Description |
|---|---------|------|-------------|
| 32 | `dst_host_count` | Continuous | Connections to same destination host |
| 33 | `dst_host_srv_count` | Continuous | Connections to same service on destination host |
| 34 | `dst_host_same_srv_rate` | Continuous | % of connections to same service |
| 35 | `dst_host_diff_srv_rate` | Continuous | % of connections to different services |
| 36 | `dst_host_same_src_port_rate` | Continuous | % of connections with same source port |
| 37 | `dst_host_srv_diff_host_rate` | Continuous | % of connections from different source hosts |
| 38 | `dst_host_serror_rate` | Continuous | % of connections with SYN errors (host level) |
| 39 | `dst_host_srv_serror_rate` | Continuous | % of service connections with SYN errors |
| 40 | `dst_host_rerror_rate` | Continuous | % of connections with REJ errors (host level) |
| 41 | `dst_host_srv_rerror_rate` | Continuous | % of service connections with REJ errors |

---

## Attack Classification Summary

| Attack Class | Key Feature Indicators | Real-World Example |
|---|---|---|
| **NORMAL** | Low counts, flag=SF, no errors | HTTP browsing, email, DNS |
| **DoS** | Very high `count`, `serror_rate` near 1.0, `dst_bytes` ≈ 0 | SYN flood, Ping of Death |
| **Probe** | High `diff_srv_rate`, high `dst_host_count`, low `dst_bytes` | Nmap port scan, IPSweep |
| **R2L** | `num_failed_logins` > 0, `logged_in=0`, high `src_bytes` | Brute-force SSH, FTP write |
| **U2R** | `root_shell=1`, `su_attempted=1`, `num_root` > 0 | Buffer overflow, rootkit install |
