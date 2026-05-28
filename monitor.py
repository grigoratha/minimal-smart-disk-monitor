import json
import subprocess

from config import SMARTCTL_PATH

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")

    return result.stdout


def smartctl_scan_drives():
    raw = run_cmd(f'"{SMARTCTL_PATH}" --scan --json')

    data = json.loads(raw)

    return [d["name"] for d in data.get("devices", [])]

def smartctl_device_smart_report(device):
    cmd = [SMARTCTL_PATH, "-a", "--json", device]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if result.returncode != 0 and not result.stdout:
            print(f"smartctl failed for {device}")
            print(result.stderr)
            return None

        data = json.loads(result.stdout)

        return parse_smartctl_report(data)

    except json.JSONDecodeError as e:
        print(f"JSON decode error for {device}: {e}")
        return None

    except Exception as e:
        print(f"Unexpected error for {device}: {e}")
        return None
    
def smartctl_scan_smart_report():
    devices = smartctl_scan_drives()

    results = []

    for device in devices:

        report = smartctl_device_smart_report(device)

        if report is not None:
            results.append(report)

    return results


def parse_sata_report(smart_report: dict):
    device = smart_report.get("device", {})

    attributes = {}

    model_name = smart_report.get("model_name")
    serial_number = smart_report.get("serial_number")
    form_factor = smart_report.get("form_factor", {}).get("name", [])

    power_on_hours = None
    for a in smart_report.get("ata_smart_attributes", {}).get("table", []):
        if a.get("name") == "Power_On_Hours":
            power_on_hours = a.get("raw", {}).get("value")
            break

    power_on_days = power_on_hours / 24 if isinstance(power_on_hours, (int, float)) else None
    power_on_months = power_on_days / 30 if power_on_days else None
    power_on_years = power_on_days / 365 if power_on_days else None

    temperature = smart_report.get("temperature", {}).get("current")

    smart_status_passed = smart_report.get("smart_status", {}).get("passed")

    # ATA attributes
    for a in smart_report.get("ata_smart_attributes", {}).get("table", []):
        name = a.get("name")
        if not name or "Unknown_Attribute" in name:
            continue

        value = a.get("raw", {}).get("value")
        if value is None:
            value = a.get("value")

        attributes[name] = value

    return {
        "device": device.get("name"),
        "model_name": model_name,
        "serial_number": serial_number,
        "form_factor": form_factor,
        "protocol": "ATA",
        "power_on_hours": power_on_hours,
        "power_on_days": power_on_days,
        "power_on_months": power_on_months,
        "power_on_years": power_on_years,
        "temperature": temperature,
        "smart_status_passed": smart_status_passed,
        "attributes": attributes
    }

def parse_nvme_report(smart_report: dict):
    device = smart_report.get("device", {})

    nvme_log = smart_report.get("nvme_smart_health_information_log", {})

    model_name = smart_report.get("model_name")
    serial_number = smart_report.get("serial_number")

    power_on_hours = nvme_log.get("power_on_hours")

    power_on_days = power_on_hours / 24 if isinstance(power_on_hours, (int, float)) else None
    power_on_months = power_on_days / 30 if power_on_days else None
    power_on_years = power_on_days / 365 if power_on_days else None

    temperature = smart_report.get("temperature", {}).get("current")

    endurance_used = smart_report.get("endurance_used", {}).get("current_percent")

    if isinstance(endurance_used, (int, float)):
        health_percentage = max(0, 100 - endurance_used)
    else:
        health_percentage = None

    smart_status_passed = smart_report.get("smart_status", {}).get("passed")

    attributes = {
        "critical_warning": nvme_log.get("critical_warning"),
        "available_spare": nvme_log.get("available_spare"),
        "percentage_used": nvme_log.get("percentage_used"),
        "unsafe_shutdowns": nvme_log.get("unsafe_shutdowns"),
        "media_errors": nvme_log.get("media_errors"),
    }

    attributes = {k: v for k, v in attributes.items() if v is not None}

    return {
        "device": device.get("name"),
        "model_name": model_name,
        "serial_number": serial_number,
        "protocol": "NVMe",
        "power_on_hours": power_on_hours,
        "power_on_days": power_on_days,
        "power_on_months": power_on_months,
        "power_on_years": power_on_years,
        "temperature": temperature,
        "smart_status_passed": smart_status_passed,
        "healthPercentage": health_percentage,
        "attributes": attributes
    }

def parse_smartctl_report(smart_report: dict):
    protocol = smart_report.get("device", {}).get("protocol")

    if protocol == "NVMe":
        return parse_nvme_report(smart_report)

    return parse_sata_report(smart_report)


def estimate_sata_disk_health(device: dict) -> float:
    """
    Evaluation criteria:
    - Reallocated / pending / uncorrectable sectors are critical indicators of disk failure
    - CRC errors indicate connection/controller issues
    - Unsafe shutdowns indicate power instability
    - SSD_Life_Left overrides other signals if present
    - SMART overall status acts as a global health limiter
    """

    health = 100.0
    smart_status_passed = device.get("smart_status_passed", False)
    attributes = device.get("attributes", {})

    if attributes.get("Reallocated_Sector_Ct", 0) > 0:
        health -= min(40, attributes["Reallocated_Sector_Ct"] * 2)

    if attributes.get("Current_Pending_Sector", 0) > 0:
        health -= 50

    if attributes.get("Offline_Uncorrectable", 0) > 0:
        health -= 50

    if attributes.get("Reported_Uncorrect", 0) > 0:
        health -= 10

    crc_errors = attributes.get("UDMA_CRC_Error_Count", 0)
    health -= min(20, crc_errors * 2)

    unsafe_shutdowns = attributes.get("Unsafe_Shutdown_Count", 0)
    health -= min(10, unsafe_shutdowns * 0.2)

    if "SSD_Life_Left" in attributes:
        health = min(health, float(attributes["SSD_Life_Left"]))

    if not smart_status_passed:
        health = min(health, 40.0)

    return round(max(0.0, min(100.0, health)), 2)

def estimate_nvme_disk_health(device: dict) -> float:
    """
    Evaluation criteria:
    - Percentage used is the primary wear indicator (0–100%)
    - Critical warnings indicate serious device issues
    - Available spare below threshold indicates degradation
    - Media errors indicate NAND/controller failures
    - High temperature reduces longevity
    - SMART status acts as a global health limiter
    """

    health = 100.0
    smart_status_passed = device.get("smart_status_passed", False)
    temperature = device.get("temperature", 100)
    attributes = device.get("attributes", {})

    percentage_used = attributes.get("percentage_used", 0)
    health -= percentage_used

    if attributes.get("critical_warning", 0):
        health -= 40

    spare = attributes.get("available_spare", 100)
    spare_thresh = attributes.get("available_spare_threshold", 10)

    if spare < spare_thresh:
        health -= 30
    elif spare < 20:
        health -= 10

    media_errors = attributes.get("media_errors", 0)
    health -= min(30, media_errors * 5)

   
    if temperature is not None:
        if temperature > 70:
            health -= 20
        elif temperature > 60:
            health -= 10

    if not smart_status_passed:
        health = min(health, 40.0)

    return round(max(0.0, min(100.0, health)), 2)
