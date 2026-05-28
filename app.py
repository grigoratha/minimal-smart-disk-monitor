import time
import threading

from typing import Any
from tray import run_tray
from config import *
from storage import *
from monitor import *
from logger import *

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

def background_disk_monitor():
    while True:
        logger.info("Running scheduled SMART scan . . .")

        try:
            devices = smartctl_scan_smart_report()

            logger.info("========================================DISK SMART REPORT=========================================")
            for device in devices:
                log_disk_info(device)
            logger.info("==================================================================================================")

            update_latest(devices)
            update_archive(devices)
            
        except Exception as e:
            logger.error(f"Background SMART scan failed: {e}")

        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    threading.Thread(
        target=background_disk_monitor,
        daemon=True
    ).start()

    run_tray()