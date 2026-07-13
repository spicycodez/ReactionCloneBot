"""
Collection: clones
Schema:
{
    "_id": <bot_id int>,           # Telegram bot's own user id (unique)
    "bot_token": str,
    "bot_username": str,
    "api_id": int,
    "api_hash": str,
    "owner_id": int,               # Telegram user id who created this clone
    "status": "running"|"stopped",
    "created_at": datetime,
    "default_delay": int,
    "default_emojis": [str],
}
"""
from datetime import datetime, timezone
from database.mongo import Mongo


class CloneDB:
    def __init__(self):
        self.col = Mongo.db()["clones"]

    async def add_clone(self, bot_id: int, bot_token: str, bot_username: str,
                         api_id: int, api_hash: str, owner_id: int,
                         default_delay: int = 1, default_emojis=None):
        doc = {
            "_id": bot_id,
            "bot_token": bot_token,
            "bot_username": bot_username,
            "api_id": api_id,
            "api_hash": api_hash,
            "owner_id": owner_id,
            "status": "running",
            "created_at": datetime.now(timezone.utc),
            "default_delay": default_delay,
            "default_emojis": default_emojis or ["👍", "❤️", "🔥"],
        }
        await self.col.update_one({"_id": bot_id}, {"$set": doc}, upsert=True)
        return doc

    async def get_clone(self, bot_id: int):
        return await self.col.find_one({"_id": bot_id})

    async def get_all_clones(self):
        return [c async for c in self.col.find({})]

    async def get_running_clones(self):
        return [c async for c in self.col.find({"status": "running"})]

    async def set_status(self, bot_id: int, status: str):
        await self.col.update_one({"_id": bot_id}, {"$set": {"status": status}})

    async def remove_clone(self, bot_id: int):
        await self.col.delete_one({"_id": bot_id})

    async def find_by_token(self, bot_token: str):
        return await self.col.find_one({"bot_token": bot_token})

    async def count(self):
        return await self.col.count_documents({})

    async def set_session_string(self, bot_id: int, session_string: str):
        """
        Cache the Pyrogram session string after a clone's first successful
        login. On future restarts we resume from this instead of running
        the bot-token login flow again - repeating that flow too often
        (e.g. one redeploy = one full re-login) is what triggers Telegram's
        FLOOD_WAIT on auth.ImportBotAuthorization.
        """
        await self.col.update_one({"_id": bot_id}, {"$set": {"session_string": session_string}})
