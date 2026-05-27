import sys

from loguru import logger

logger.remove()

# STDOUT Logging
logger.add(
    sys.stdout,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

# FILE Logging
logger.add("logs/app.log", level="INFO", rotation="1 MB", retention="7 days", compression="zip")