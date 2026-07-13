import asyncio
import random

import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

from config import Config
from database.reaction_db import ReactionDB
from utils.rate_limiter import RateLimiter
from utils.logger import get_logger

logger = get_logger("auto_react")
reaction_db = ReactionDB()
limiter = RateLimiter(max_calls=Config.MAX_REACTIONS_PER_MINUTE, per_seconds=60)


def get_bot_id(client: Client) -> int:
    return getattr(client, "bot_id", None) or client.me.id


def get_bot_token(client: Client) -> str:
    """Pyrogram stores the token it logged in with as client.bot_token."""
    token = getattr(client, "bot_token", None)
    if not token:
        raise RuntimeError("bot_token not found on client, can't call Bot API")
    return token


async def send_bot_api_reaction(client: Client, chat_id: int, message_id: int, emojis: list[str]):
    """
    IMPORTANT: bots can NOT call the raw MTProto method messages.sendReaction
    (that's what Pyrogram's client.send_reaction() uses under the hood) -
    Telegram rejects it for bot accounts with 400 BOT_METHOD_INVALID, no
    matter which MTProto library you use. This is a hard platform
    restriction, not a bug in this code.

    Reactions for bots only work through the HTTP Bot API's
    setMessageReaction endpoint (added in Bot API 7.0), so we call that
    directly instead of going through Pyrogram's MTProto layer.
    """
    token = get_bot_token(client)
    url = f"https://api.telegram.org/bot{token}/setMessageReaction"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reaction": [{"type": "emoji", "emoji": e} for e in emojis],
        "is_big": False,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            data = await resp.json()
            if not data.get("ok"):
                raise RuntimeError(data.get("description", "Unknown Bot API error"))
            return data


@Client.on_message(filters.group | filters.channel, group=1)
async def auto_react_handler(client: Client, message: Message):
    """
    Fires on every incoming channel/group message.
    Looks up per-chat settings for this clone and reacts accordingly.
    """
    try:
        clone_id = get_bot_id(client)
        chat_id = message.chat.id

        settings = await reaction_db.get_chat_settings(clone_id, chat_id)
        if not settings:
            # Auto-register chat with default settings the first time bot sees a message
            settings = await reaction_db.register_chat(
                clone_id, chat_id, message.chat.title or str(chat_id),
                Config.DEFAULT_EMOJIS, Config.DEFAULT_DELAY
            )

        if not settings.get("enabled", True):
            return

        delay = settings.get("delay", Config.DEFAULT_DELAY)
        emojis = settings.get("emojis") or Config.DEFAULT_EMOJIS
        multi = settings.get("multi_reaction", False)

        if delay > 0:
            await asyncio.sleep(delay)

        # Rate limit guard - keyed per clone to protect the whole bot from flood bans
        await limiter.acquire(str(clone_id))

        chosen = (
            random.sample(emojis, k=min(len(emojis), random.randint(1, 3)))
            if multi else [random.choice(emojis)]
        )

        try:
            await send_bot_api_reaction(client, chat_id, message.id, chosen)
            await reaction_db.increment_reaction_count(clone_id, chat_id)

        except RuntimeError as e:
            err = str(e)
            if "Too Many Requests" in err or "flood" in err.lower():
                logger.warning("Rate limited reacting in chat %s: %s", chat_id, err)
                await asyncio.sleep(5)
            elif "REACTION_INVALID" in err:
                logger.warning("Emoji %s not allowed by Telegram in chat %s", chosen, chat_id)
            elif "message to react not found" in err.lower() or "chat not found" in err.lower():
                pass  # message deleted / chat inaccessible, safely ignore
            else:
                logger.error("Unexpected error reacting in chat %s: %s", chat_id, err)
        except Exception as e:
            logger.error("Unexpected error reacting in chat %s: %s", chat_id, e)

    except Exception as e:
        logger.error("auto_react_handler crashed: %s", e, exc_info=True)
