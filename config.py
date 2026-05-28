from pathlib import Path

APP_NAME = "Disk Monitor"

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

LATEST_FILE = DATA_DIR / "latest.json"
ARCHIVE_FILE = DATA_DIR / "archive.json"

SMARTCTL_PATH = r"C:\Program Files\Utilities\SmartCTL\bin\smartctl.exe"

# Interval in seconds
CHECK_INTERVAL = 43200 

# Temperature thresholds
SATA_TEMP_WARNING = 50
SATA_TEMP_CRITICAL = 55

NVME_TEMP_WARNING = 60
NVME_TEMP_CRITICAL = 70