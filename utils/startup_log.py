import aiohttp
from datetime import datetime, timezone

from config import Config
from utils.logger import get_logger
from utils.markdown import escape_markdown

logger = get_logger("startup_log")


async def send_startup_log(client, me, label: str = "Bot"):
    """
    Posts a small 'I'm alive' message to Config.LOG_CHANNEL (if set)
    whenever the master bot or a clone starts up. Safe to call even if
    LOG_CHANNEL isn't configured, or if this particular bot isn't a
    member/admin of that chat - failures are just logged, never raised,
    so a broken log channel can never stop the bot from starting.

    Always sends using the MASTER bot's token (Config.BOT_TOKEN), never
    the calling clone's own token. Every clone is its own separate
    Telegram bot account and is almost never added as admin to the
    owner's private log channel, which caused "Bad Request: chat not
    found" for every clone startup. Only the master bot needs to be a
    member/admin of LOG_CHANNEL for this to work for master AND clones.

    Uses the Bot API HTTP endpoint (like auto_react.py does for
    reactions) instead of Pyrogram's MTProto send_message, since
    Pyrogram needs the target chat's "peer" already cached locally
    before it can message it - the HTTP Bot API resolves chat_id
    server-side instead.
    """
    if not Config.LOG_CHANNEL or not Config.BOT_TOKEN:
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    text = (
        f"✅ **{escape_markdown(label)} Started**\n\n"
        f"Username: @{escape_markdown(me.username)}\n"
        f"ID: `{me.id}`\n"
        f"Time: {now} UTC"
    )
    url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/sendMessage"
    payload = {"chat_id": Config.LOG_CHANNEL, "text": text, "parse_mode": "Markdown"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
                if not data.get("ok"):
                    raise RuntimeError(data.get("description", "Unknown Bot API error"))
    except Exception as e:
        logger.warning("Could not send startup log to LOG_CHANNEL (%s): %s", Config.LOG_CHANNEL, e)
