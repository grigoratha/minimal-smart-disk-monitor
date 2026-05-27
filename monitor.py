import json
import subprocess
import re

from config import SMARTCTL_PATH

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout.strip()

def run_powershell(cmd: str):
    result = subprocess.run(
        ["powershell", "-Command", cmd],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return result.stdout.strip()

def parse_ps_json(raw):
    if not raw:
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    if isinstance(data, dict):
        return [data]

    return data if isinstance(data, list) else []

def ps_to_list(cmd):
    return parse_ps_json(run_powershell(cmd))


def get_disks():
    return ps_to_list("Get-Disk | ConvertTo-Json -Depth 4")

def get_volumes():
    return ps_to_list("Get-Volume | ConvertTo-Json")

def get_partitions():
    return ps_to_list("Get-Partition | ConvertTo-Json -Depth 4")

def map_smart_type(bus: str):
    if not bus:
        return None

    bus = bus.lower()

    if "nvme" in bus:
        return "nvme"

    if "sata" in bus or "ssd" in bus or "ata" in bus:
        return "ata"

    if "usb" in bus or "scsi" in bus:
        return "sat"

    # Fallback
    return "ata"  

def parse_smart_summary(raw: str):
    """
    Lightweight parser for quick health indicators.
    """

    summary = {
        "health": None,
        "temperature": None,
        "percentage_used": None,
        "raw": raw
    }

    # Health
    if "PASSED" in raw:
        summary["health"] = "PASSED"
    elif "FAILED" in raw or "FAILING" in raw:
        summary["health"] = "FAILED"

    # NVMe percentage used
    match = re.search(r"Percentage Used:\s+(\d+)", raw)
    if match:
        summary["percentage_used"] = int(match.group(1))

    # Temperature (generic)
    temp = re.search(r"Temperature.*?(\d+)\s*C", raw)
    if temp:
        summary["temperature"] = int(temp.group(1))

    return summary

def run_smartctl(disk_number: int, bus: str):
    dev_type = map_smart_type(bus)
    device = fr"\\.\PhysicalDrive{disk_number}"

    cmd = [SMARTCTL_PATH, "-a", "-d", dev_type, device]

    result = subprocess.run(cmd, capture_output=True, text=True)

    output = result.stdout.strip()
    error = result.stderr.strip()

    if not output:
        return {
            "health": None,
            "attributes": {},
            "raw": error
        }

    return parse_smart_summary(output)

def create_disks_report():
    disks = get_disks()
    partitions = get_partitions()
    volumes = get_volumes()

    # ------------------------
    # Volume map
    # ------------------------
    volume_map = {}

    for v in volumes:
        letter = v.get("DriveLetter")
        if letter:
            volume_map[str(letter).upper()] = {
                "letter": letter,
                "label": v.get("FileSystemLabel"),
                "fileSystem": v.get("FileSystem"),
                "size": v.get("Size"),
                "health": v.get("HealthStatus"),
            }

    # ------------------------
    # Disk base map
    # ------------------------
    disk_map = {}

    for d in disks:
        disk_number = d.get("Number")

        disk_map[disk_number] = {
            "number": disk_number,
            "name": d.get("FriendlyName"),
            "bus": d.get("BusType"),
            "partition": d.get("PartitionStyle"),
            "operation": d.get("OperationalStatus"),
            "health": d.get("HealthStatus"),
            "serial": str((d.get("SerialNumber"))).strip(),
            "boot": d.get("IsBoot"),
            "guid": d.get("Guid"),
            "volumes": [],
            "smart": {}
        }

    # ------------------------
    # Attach volumes
    # ------------------------
    for p in partitions:
        disk_number = p.get("DiskNumber")
        paths = p.get("AccessPaths") or []

        if disk_number not in disk_map:
            continue

        for path in paths:
            if isinstance(path, str) and len(path) >= 2 and path[1] == ":":
                letter = path[0].upper()

                if letter in volume_map:
                    disk_map[disk_number]["volumes"].append(volume_map[letter])

    # ------------------------
    # SMART enrichment (THIS IS THE IMPORTANT PART)
    # ------------------------
    for disk_number, disk in disk_map.items():
        try:
            smart_raw = run_smartctl(disk_number, disk["bus"])
            disk["smart"] = smart_raw
        except Exception as e:
            disk["smart"] = {
                "error": str(e),
                "health": None,
                "attributes": {},
            }

    return list(disk_map.values())

def main():
    data = create_disks_report()

    # Print results
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()