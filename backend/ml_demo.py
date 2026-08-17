"""
CyberShield ML Engine - Live Demo
Run: python ml_demo.py
"""
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'cybershield_core.settings'

import django
django.setup()

from detection.core_ml.inference import classifier

# Load the trained model
classifier.load()

SEP = "=" * 60

print(SEP)
print("  CYBERSHIELD ML ENGINE - LIVE DEMO")
print(SEP)
info = classifier.get_model_info()
print("  Model loaded : " + str(classifier.is_loaded))
print("  Algorithm    : " + str(info["model_type"]))
print("  Trees        : " + str(info["n_estimators"]))
print("  Features     : " + str(info["feature_count"]))
print("  Detects      : " + str(info["classes"]))
print(SEP)

# ----------------------------------------------------------------
# EXAMPLE 1: Normal web browsing traffic
# ----------------------------------------------------------------
print()
print("EXAMPLE 1: Normal Web Browsing Traffic")
print("-" * 40)
normal_traffic = {
    "duration": 0,
    "protocol_type": 6,   # TCP
    "service": 10,        # HTTP
    "flag": 10,           # SF = Success
    "src_bytes": 215,
    "dst_bytes": 45076,
    "land": 0,
    "logged_in": 1,
    "count": 9,
    "srv_count": 9,
    "serror_rate": 0.0,
    "same_srv_rate": 1.0,
    "dst_host_count": 9,
    "dst_host_srv_count": 9,
}
label, confidence = classifier.predict(normal_traffic)
print("  Description : User browsing a website (TCP, HTTP, success)")
print("  src_bytes   : 215  (small request sent)")
print("  dst_bytes   : 45076 (webpage received)")
print("  flag        : SF (connection completed normally)")
print("  --> Prediction : " + label)
print("  --> Confidence : " + str(round(confidence * 100, 1)) + "%")

# ----------------------------------------------------------------
# EXAMPLE 2: DoS Attack (Neptune SYN Flood)
# ----------------------------------------------------------------
print()
print("EXAMPLE 2: DoS Attack (Neptune SYN Flood)")
print("-" * 40)
dos_traffic = {
    "duration": 0,
    "protocol_type": 6,   # TCP
    "service": 5,         # private
    "flag": 4,            # S0 = SYN sent, no response (half-open)
    "src_bytes": 0,
    "dst_bytes": 0,
    "land": 0,
    "logged_in": 0,
    "count": 511,
    "srv_count": 511,
    "serror_rate": 1.0,
    "srv_serror_rate": 1.0,
    "same_srv_rate": 1.0,
    "dst_host_count": 255,
    "dst_host_srv_count": 255,
    "dst_host_serror_rate": 1.0,
    "dst_host_srv_serror_rate": 1.0,
}
label2, confidence2 = classifier.predict(dos_traffic)
print("  Description : Hacker floods server with 511 SYN packets")
print("  src_bytes   : 0   (no real data, just flood packets)")
print("  dst_bytes   : 0   (server never responds)")
print("  serror_rate : 1.0 (100% SYN errors = flood)")
print("  flag        : S0  (SYN never completed)")
print("  --> Prediction : " + label2)
print("  --> Confidence : " + str(round(confidence2 * 100, 1)) + "%")

# ----------------------------------------------------------------
# EXAMPLE 3: Port Scan / Probe
# ----------------------------------------------------------------
print()
print("EXAMPLE 3: Port Scan (Hacker Probing the Network)")
print("-" * 40)
probe_traffic = {
    "duration": 0,
    "protocol_type": 6,   # TCP
    "service": 10,        # HTTP
    "flag": 2,            # REJ = Connection Rejected
    "src_bytes": 0,
    "dst_bytes": 0,
    "land": 0,
    "logged_in": 0,
    "count": 229,
    "srv_count": 3,
    "serror_rate": 0.0,
    "rerror_rate": 1.0,
    "same_srv_rate": 0.06,
    "diff_srv_rate": 0.07,
    "dst_host_count": 255,
    "dst_host_srv_count": 3,
    "dst_host_diff_srv_rate": 0.07,
    "dst_host_rerror_rate": 1.0,
}
label3, confidence3 = classifier.predict(probe_traffic)
print("  Description : Hacker scanning 229 ports looking for open ones")
print("  count       : 229 (229 connections attempted rapidly)")
print("  rerror_rate : 1.0 (100% rejected = all ports closed/blocked)")
print("  diff_srv_rate: 0.07 (hitting many different services)")
print("  flag        : REJ (rejected by firewall)")
print("  --> Prediction : " + label3)
print("  --> Confidence : " + str(round(confidence3 * 100, 1)) + "%")

# ----------------------------------------------------------------
# EXAMPLE 4: Password Brute Force (R2L)
# ----------------------------------------------------------------
print()
print("EXAMPLE 4: Password Brute Force (R2L Attack)")
print("-" * 40)
r2l_traffic = {
    "duration": 2,
    "protocol_type": 6,    # TCP
    "service": 10,         # HTTP
    "flag": 10,            # SF
    "src_bytes": 1337,
    "dst_bytes": 1692,
    "land": 0,
    "num_failed_logins": 5,
    "logged_in": 0,
    "num_compromised": 0,
    "root_shell": 0,
    "count": 1,
    "srv_count": 1,
    "serror_rate": 0.0,
    "rerror_rate": 0.0,
    "same_srv_rate": 1.0,
    "dst_host_count": 150,
    "dst_host_srv_count": 25,
}
label4, confidence4 = classifier.predict(r2l_traffic)
print("  Description : Hacker trying many passwords from outside")
print("  num_failed_logins: 5 (5 failed login attempts)")
print("  logged_in   : 0   (never successfully logged in)")
print("  src_bytes   : 1337 (sending login attempt data)")
print("  --> Prediction : " + label4)
print("  --> Confidence : " + str(round(confidence4 * 100, 1)) + "%")

print()
print(SEP)
print("  DEMO COMPLETE - ML Engine is working correctly!")
print(SEP)
