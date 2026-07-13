import asyncio
from pyrogram import Client
from pyrogram.errors import ApiIdInvalid, AccessTokenInvalid, FloodWait

from config import Config
from database.clone_db import CloneDB
from utils.logger import get_logger

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

    async def validate_token(self, bot_token: str):
        """Quickly spins up a throwaway client to validate the token & fetch bot info."""
        temp = Client(
            name=f"validate_{bot_token[:8]}",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=bot_token,
            in_memory=True,
        )
        try:
            await temp.start()
            me = await temp.get_me()
            await temp.stop()
            return me
        except (ApiIdInvalid, AccessTokenInvalid) as e:
            raise ValueError(f"Invalid token/credentials: {e}")

    async def start_clone(self, bot_token: str, owner_id: int, from_plugins_dir="plugins"):
        me = await self.validate_token(bot_token)

        existing = await self.clone_db.find_by_token(bot_token)
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

        client = Client(
            name=f"clone_{me.id}",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=bot_token,
            plugins=dict(root=from_plugins_dir),
            in_memory=True,
        )
        client.bot_id = me.id  # attach for handlers to reference
        client.is_clone = True

        await client.start()
        self.active_clones[me.id] = client
        logger.info("Clone started: @%s (id=%s)", me.username, me.id)
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
