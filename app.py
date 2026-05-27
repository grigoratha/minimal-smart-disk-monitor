import json

from typing import Any
from monitor import *
from logger import *

def log_disk_info(device: dict):
    dev_name = device.get("device", "N/A")
    protocol = device.get("protocol", "N/A")
    model = device.get("model_name", "N/A")
    temp_raw = device.get("temperature", "N/A")
    temperature = f"{temp_raw}°C" if temp_raw is not None else "N/A"
    smart_status_passed = device.get("smart_status_passed")
    
    if protocol == 'NVme':
        health = estimate_nvme_disk_health(device)
    else:
        health = estimate_sata_disk_health(device)

    logger.info(f"{dev_name:<10} | {protocol:<8} | {model:<30} | {temperature:<14} | {smart_status_passed:<10} | {health}")

def main():
    devices = smartctl_scan_smart_report();

    logger.info("========================================DISK SMART REPORT=========================================")
    logger.info(f"{'DEVICE':<10} | {'PROTOCOL':<8} | {'MODEL':<30} | {'TEMPERATURE':<14} | {'SMART STATUS':<10} | {'HEALTH SCORE'}")
    logger.info(f"-------------------------------------------------------------------------------------------------")
    for device in devices:
        log_disk_info(device)
    logger.info("==================================================================================================")


if __name__ == "__main__":
    main()