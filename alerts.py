from logger import logger
from storage import read_latest

from config import (
    SATA_TEMP_WARNING,
    SATA_TEMP_CRITICAL,
    NVME_TEMP_WARNING,
    NVME_TEMP_CRITICAL
)


def detect_degradation(current_devices: dict):
    latest = read_latest()

    if latest is None:
        return []

    old_devices = latest.get("devices", {})

    alerts = []

    for serial, current in current_devices.items():

        old = old_devices.get(serial)

        if old is None:
            continue

        model = current.get("model_name", serial)

        current_health = current.get("health")
        old_health = old.get("health")

        current_temp = current.get("temperature")
        old_temp = old.get("temperature")

        current_status = current.get("smart_status_passed")
        old_status = old.get("smart_status_passed")

        protocol = current.get("protocol", "ATA")

        # Health comparison
        if (
            old_health is not None
            and current_health is not None
            and current_health < old_health
        ):

            alerts.append(f"⚠️ {model} health dropped from {old_health}% to {current_health}%")

        # SMART Status
        if old_status and not current_status:
            alerts.append(f"🚨 {model} SMART status FAILED")

        # Temperature
        if current_temp is not None:

            if protocol == "NVMe":
                warning = NVME_TEMP_WARNING
                critical = NVME_TEMP_CRITICAL

            else:
                warning = SATA_TEMP_WARNING
                critical = SATA_TEMP_CRITICAL

            # Critical threshold crossing
            if (old_temp < critical and current_temp >= critical):
                alerts.append(f"🚨 {model} critical temperature reached {current_temp}°C")

            # Warning threshold crossing
            elif (old_temp < warning and current_temp >= warning):
                alerts.append(f"⚠️ {model} temperature exceeded {warning}°C")

    if alerts:
        logger.warning(f"{len(alerts)} alert(s) detected")

        for alert in alerts:
            logger.warning(alert)

    else:
        logger.info("✅️ No disk alerts")

    return alerts