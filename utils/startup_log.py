import aiohttp
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

    Uses the Bot API HTTP endpoint (like auto_react.py does for
    reactions) instead of Pyrogram's MTProto send_message. Pyrogram
    needs the target chat's "peer" already cached in its local session
    before it can message it, which a freshly (re)started bot often
    doesn't have yet for a channel with no recent activity - that's
    what causes PEER_ID_INVALID even though the bot is genuinely a
    member/admin there. The HTTP Bot API resolves chat_id server-side,
    so it works immediately after startup.
    """
    if not Config.LOG_CHANNEL:
        return

    token = getattr(client, "bot_token", None)
    if not token:
        logger.warning("No bot_token on client, skipping startup log")
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    text = (
        f"✅ **{label} Started**\n\n"
        f"Username: @{me.username}\n"
        f"ID: `{me.id}`\n"
        f"Time: {now} UTC"
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": Config.LOG_CHANNEL, "text": text, "parse_mode": "Markdown"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    raise RuntimeError(data.get("description", "Unknown Bot API error"))
    except Exception as e:
        logger.warning("Could not send startup log to LOG_CHANNEL (%s): %s", Config.LOG_CHANNEL, e)
