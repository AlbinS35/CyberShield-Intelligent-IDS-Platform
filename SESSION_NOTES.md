# CyberShield IDS Session Summary

**Date:** October 7, 2026

## 1. System Admin Roles Fix 
**Issue:** Users created with the role `Analyst` in the System Admin Playbook Manager were unable to log in properly and faced a blank sidebar.
**Fix:** The frontend codebase was updated to make role handling fully case-insensitive. Specifically:
- **`ProtectedRoute.jsx`**: Automatically uppercases the user's role before verifying dashboard access.
- **`Sidebar.jsx`**: Automatically uppercases the user's role before matching it to the navigation configuration dictionary.
- **`PlaybookManager.jsx`**: Updated the new user creation dropdown to default to the correct uppercase constant values (`ANALYST`, `INVESTIGATOR`, `SYS_ADMIN`, `ORG_MANAGER`).
*These changes were pushed to the `main` branch and are now live in production.*

---

## 2. Streaming Live Data from Suricata
**Issue:** The Ubuntu 24.04 `sudo` policy was stripping environment variables from the `watcher.py` script, causing it to fail with a `DEFAULT_TENANT_ID is not set` error when trying to stream data to the Render backend.

**Permanent Fix (Foolproof Method):**
To completely bypass `sudo` restrictions and stream live events to your dashboard, you must run the script as the native `root` user:

```bash
# 1. Switch to root user
sudo su

# 2. Export variables directly into root memory
export CYBERSHIELD_API_URL="https://cybershield-backend-15ro.onrender.com"
export SURICATA_API_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxODE5NjI4MzM5LCJpYXQiOjE3ODgwOTIzMzksImp0aSI6IjFlM2QxODRmYWQ5YzQyZTQ4M2ZjOWY5OGU1Mzk5Mzc3IiwidXNlcl9pZCI6ImNlMmQwN2M5LTZjYzEtNGNkMS1iNzJmLWM0NmZjOTEwMmYwZSJ9.4mpuIt45LZdndRamCqaqlM7wDNIP4SBDLkcjYDqY16s"
export DEFAULT_TENANT_ID="40f13b4f-e140-404f-a6af-8142f59f1c33"

# 3. Start the watcher (Leave this terminal open and running)
python3 watcher.py
```

---

## 3. Triggering Live Alerts
When the `watcher.py` script is running successfully, the dashboard will only update when a *new* attack is detected. If your VirtualBox network is secure, no events will be pushed.

**How to test the Live Dashboard:**
Make sure your VirtualBox VM has an active internet connection (check NAT/Bridged Adapter settings). Then open a second terminal and run either of these harmless commands to trick Suricata into logging a high-severity alert:

*Test 1 (Simulate malicious file download):*
```bash
curl http://testmynids.org/uid/index.html
```

*Test 2 (Simulate malicious vulnerability scanner):*
```bash
curl -A "ZmEu" http://1.1.1.1
```

Within a second of running either command, the watcher will transmit the alert and your Vercel dashboard will instantly visualize the threat.
