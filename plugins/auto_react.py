import asyncio
import random

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, ReactionInvalid, MessageIdInvalid, PeerIdInvalid

from config import Config
from database.reaction_db import ReactionDB
from utils.rate_limiter import RateLimiter
from utils.logger import get_logger

logger = get_logger("auto_react")
reaction_db = ReactionDB()
limiter = RateLimiter(max_calls=Config.MAX_REACTIONS_PER_MINUTE, per_seconds=60)


def get_bot_id(client: Client) -> int:
    return getattr(client, "bot_id", None) or client.me.id


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

        emoji_choice = random.choice(emojis) if not multi else random.sample(
            emojis, k=min(len(emojis), random.randint(1, 3))
        )

        try:
            await client.send_reaction(
                chat_id=chat_id,
                message_id=message.id,
                emoji=emoji_choice if isinstance(emoji_choice, str) else emoji_choice[0],
                big=False,
            )
            await reaction_db.increment_reaction_count(clone_id, chat_id)

        except FloodWait as e:
            logger.warning("FloodWait %ss on clone %s, chat %s", e.value, clone_id, chat_id)
            await asyncio.sleep(e.value)
        except ReactionInvalid:
            logger.warning("Emoji '%s' not allowed by Telegram in chat %s", emoji_choice, chat_id)
        except (MessageIdInvalid, PeerIdInvalid):
            pass  # message deleted / chat inaccessible, safely ignore
        except Exception as e:
            logger.error("Unexpected error reacting in chat %s: %s", chat_id, e)

    except Exception as e:
        logger.error("auto_react_handler crashed: %s", e, exc_info=True)
