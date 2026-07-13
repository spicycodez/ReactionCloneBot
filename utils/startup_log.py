from datetime import datetime, timezone

from config import Config
from utils.logger import get_logger

logger = get_logger("startup_log")


async def send_startup_log(client, me, label: str = "Bot"):
    """
    Posts a small 'I'm alive' message to Config.LOG_CHANNEL (if set)
    whenever the master bot or a clone starts up. Safe to call even if
    LOG_CHANNEL isn't configured, or if this particular bot isn't a
    member/admin of that chat - failures are just logged, never raised,
    so a broken log channel can never stop the bot from starting.
    """
    if not Config.LOG_CHANNEL:
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    text = (
        f"✅ **{label} Started**\n\n"
        f"Username: @{me.username}\n"
        f"ID: `{me.id}`\n"
        f"Time: {now} UTC"
    )
    try:
        await client.send_message(Config.LOG_CHANNEL, text)
    except Exception as e:
        logger.warning("Could not send startup log to LOG_CHANNEL (%s): %s", Config.LOG_CHANNEL, e)
