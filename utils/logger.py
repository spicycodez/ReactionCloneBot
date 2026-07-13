import logging
import sys
from logging.handlers import RotatingFileHandler

def get_logger(name: str):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # avoid duplicate handlers on reload

    logger.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    logger.addHandler(console)

    file_handler = RotatingFileHandler(
        "bot.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    # Reduce noise from pyrogram internals
    logging.getLogger("pyrogram").setLevel(logging.WARNING)

    return logger
