import asyncio
from pyrogram import Client
from pyrogram.errors import ApiIdInvalid, AccessTokenInvalid, FloodWait

from config import Config
from database.clone_db import CloneDB
from utils.logger import get_logger
from utils.startup_log import send_startup_log

logger = get_logger("clone_manager")


class CloneManager:
    """
    Holds all running clone Client instances in memory.
    key   -> bot_id (int)
    value -> pyrogram.Client instance
    """

    def __init__(self):
        self.active_clones: dict[int, Client] = {}
        self.clone_db = CloneDB()

    async def start_clone(self, bot_token: str, owner_id: int, from_plugins_dir="plugins"):
        existing = await self.clone_db.find_by_token(bot_token)
        session_string = existing.get("session_string") if existing else None

        # Resume from a cached session string when we have one, instead of
        # re-running the bot-token login flow on every restart - Heroku's
        # filesystem is ephemeral so a plain file session never survives a
        # restart, and repeated logins on the same token (e.g. one
        # redeploy = one full re-login) can hit Telegram's FLOOD_WAIT on
        # auth.ImportBotAuthorization. This also removes the old separate
        # "validate token" pre-check, which used to log in a second time
        # just to fetch bot info before the real client logged in again.
        client_kwargs = dict(
            name=f"clone_{bot_token[:8]}",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            plugins=dict(root=from_plugins_dir),
            in_memory=True,
        )
        if session_string:
            client_kwargs["session_string"] = session_string
        else:
            client_kwargs["bot_token"] = bot_token

        client = Client(**client_kwargs)

        try:
            await client.start()
        except (ApiIdInvalid, AccessTokenInvalid) as e:
            raise ValueError(f"Invalid token/credentials: {e}")
        except FloodWait as e:
            raise ValueError(f"Telegram flood wait: retry after {e.value} seconds")

        me = await client.get_me()

        if not existing:
            await self.clone_db.add_clone(
                bot_id=me.id,
                bot_token=bot_token,
                bot_username=me.username,
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                owner_id=owner_id,
                default_delay=Config.DEFAULT_DELAY,
                default_emojis=Config.DEFAULT_EMOJIS,
            )
        else:
            await self.clone_db.set_status(me.id, "running")

        if not session_string:
            new_session_string = await client.export_session_string()
            await self.clone_db.set_session_string(me.id, new_session_string)

        client.bot_id = me.id  # attach for handlers to reference
        client.bot_token = bot_token  # used by auto_react.py for the Bot API reactions call
        client.is_clone = True

        self.active_clones[me.id] = client
        logger.info("Clone started: @%s (id=%s)", me.username, me.id)
        await send_startup_log(client, me, label=f"Clone (@{me.username})")
        return me

    async def stop_clone(self, bot_id: int):
        client = self.active_clones.get(bot_id)
        if client:
            await client.stop()
            del self.active_clones[bot_id]
        await self.clone_db.set_status(bot_id, "stopped")
        logger.info("Clone stopped: id=%s", bot_id)

    async def delete_clone(self, bot_id: int):
        await self.stop_clone(bot_id) if bot_id in self.active_clones else None
        await self.clone_db.remove_clone(bot_id)
        logger.info("Clone deleted: id=%s", bot_id)

    async def restart_all_clones(self, plugins_dir="plugins"):
        """Called on startup to auto-resume clones that were running before restart."""
        clones = await self.clone_db.get_running_clones()
        for c in clones:
            try:
                await self.start_clone(c["bot_token"], c["owner_id"], plugins_dir)
                await asyncio.sleep(1)  # small stagger to avoid flood on boot
            except Exception as e:
                logger.error("Failed to restart clone %s: %s", c.get("bot_username"), e)

    def get_clone(self, bot_id: int):
        return self.active_clones.get(bot_id)

    def list_active(self):
        return list(self.active_clones.keys())


clone_manager = CloneManager()
