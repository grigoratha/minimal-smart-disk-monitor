# Python Disk Monitor Tool

A lightweight Windows tray application for monitoring disk SMART health, temperature, and degradation using `smartctl`.

The application performs scheduled SMART scans in the background, archives results, detects degradation events, 
and shows Windows toast notifications for critical changes.

---

# Features

* SMART monitoring for SATA and NVMe drives
* Background monitoring loop
* System tray integration
* Windows toast notifications
* Historical scan archive
* Health estimation algorithms
* Temperature threshold monitoring
* SMART failure detection
* Automatic degradation comparison against previous scans

---

# Requirements

* Windows
* Python 3.10+
* smartmontools

Download smartmontools:

https://www.smartmontools.org/

---

# Installation

## Clone repository

```bash
git clone <repository_url>
cd disk-monitor
```

## Install dependencies

```bash
pip install -r requirements.txt
```

---

# Configure smartctl path

In `config.py`:

```python
SMARTCTL_PATH = r"C:\Program Files\smartmontools\bin\smartctl.exe"
```


# Monitoring Logic

The application:

1. Scans all SMART-capable drives
2. Parses SMART data
3. Estimates device health
4. Compares against previous scan
5. Detects degradation events
6. Shows alerts if needed
7. Stores latest snapshot
8. Appends historical archive

# Alerts

The application currently detects:

* SMART status failures
* Health degradation
* SATA temperature threshold crossing
* NVMe temperature threshold crossing

# License

MIT License
