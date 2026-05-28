import pystray
import threading

from PIL import Image
from pathlib import Path
from pystray import MenuItem as Item

from toast import show_notification
from config import APP_NAME
from monitor import *
from logger import *

BASE_DIR = Path(__file__).resolve().parent
ICON_PATH = BASE_DIR / "assets" / "hdd.png"

def log_disk_info(device: dict):
    dev_name = device.get("device", "N/A")
    protocol = device.get("protocol", "N/A")
    model = device.get("model_name", "N/A")
    temp_raw = device.get("temperature", "N/A")
    temperature = f"{temp_raw}°C" if temp_raw is not None else "N/A"
    smart_status_passed = device.get("smart_status_passed")
    
    if protocol == 'NVMe':
        health = estimate_nvme_disk_health(device)
    else:
        health = estimate_sata_disk_health(device)

    logger.info(f"{dev_name:<10} | {protocol:<8} | {model:<30} | {temperature:<14} | {smart_status_passed:<10} | {health}")

# Menu events
def on_show_info(icon, item):
    show_notification("Disk Monitor", "\n💽 Scanning disks . . .")

    threading.Thread(
        target=run_smart_scan, 
        daemon=True
    ).start()

def run_smart_scan():
    devices = smartctl_scan_smart_report()

    lines = []

    for device in devices:
        model = device.get("model_name", "Unknown")
        temperature = device.get("temperature", "N/A")
        smart_status_passed = device.get("smart_status_passed")

        status = "PASS" if smart_status_passed else "FAIL"
        status_icon = "✅" if smart_status_passed else "⚠️"

        if device.get("protocol") == "NVMe":
            health = estimate_nvme_disk_health(device)
        else:
            health = estimate_sata_disk_health(device)

        lines.append(
            f"{status_icon} {model} • {health}% • {temperature}°C"
        )

        log_disk_info(device)

    message = "\n".join(lines)

    show_notification("SMART Information", message)

def on_exit(icon, item):
    print("Exiting Disk Monitor...")
    icon.stop()

def load_icon():
    return Image.open(ICON_PATH).convert("RGBA")

def run_tray():
    icon = pystray.Icon(
        name="pyDiskMonitor",
        icon=load_icon(),
        title=APP_NAME,
        menu=pystray.Menu(
            Item("SMART Info", on_show_info),
            pystray.Menu.SEPARATOR,
            Item("Exit", on_exit),
        ),
    )

    icon.run()