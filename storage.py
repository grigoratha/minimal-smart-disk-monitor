import json

from logger import *
from datetime import datetime
from config import LATEST_FILE, ARCHIVE_FILE

def update_latest(devices: dict):

    payload = {
        "timestamp": datetime.now().isoformat(),
        "devices": devices
    }

    with open(LATEST_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4)

    logger.info("Report file has been updated")

def update_archive(devices: dict):

    payload = {
        "timestamp": datetime.now().isoformat(),
        "devices": devices
    }

    archive = []

    if ARCHIVE_FILE.exists():

        try:
            with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
                archive = json.load(f)

        except json.JSONDecodeError:
            archive = []

    archive.append(payload)

    with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(archive, f, indent=4)

    logger.info("Archive file has been updated")