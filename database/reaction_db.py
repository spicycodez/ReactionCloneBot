"""
Collection: chat_settings
Schema:
{
    "_id": f"{clone_id}_{chat_id}",   # composite key -> isolates data per clone
    "clone_id": int,
    "chat_id": int,
    "chat_title": str,
    "enabled": bool,
    "emojis": [str],          # list of emojis to randomly pick from
    "delay": int,             # seconds before reacting
    "multi_reaction": bool,   # if True, sends more than 1 emoji per message (big react)
    "added_at": datetime,
}

Collection: users
Schema:
{
    "_id": f"{clone_id}_{user_id}",
    "clone_id": int,
    "user_id": int,
    "joined_at": datetime,
}

Collection: stats
Schema:
{
    "_id": f"{clone_id}_{chat_id}_{yyyy_mm_dd}",
    "clone_id": int,
    "chat_id": int,
    "date": str,
    "reactions_sent": int,
}
"""
from datetime import datetime, timezone
from database.mongo import Mongo


class ReactionDB:
    def __init__(self):
        self.chats = Mongo.db()["chat_settings"]
        self.users = Mongo.db()["users"]
        self.stats = Mongo.db()["stats"]

    def _key(self, clone_id: int, chat_id: int):
        return f"{clone_id}_{chat_id}"

    async def register_chat(self, clone_id: int, chat_id: int, chat_title: str,
                             default_emojis, default_delay: int):
        key = self._key(clone_id, chat_id)
        existing = await self.chats.find_one({"_id": key})
        if existing:
            return existing
        doc = {
            "_id": key,
            "clone_id": clone_id,
            "chat_id": chat_id,
            "chat_title": chat_title,
            "enabled": True,
            "emojis": default_emojis,
            "delay": default_delay,
            "multi_reaction": False,
            "added_at": datetime.now(timezone.utc),
        }
        await self.chats.insert_one(doc)
        return doc

    async def get_chat_settings(self, clone_id: int, chat_id: int):
        return await self.chats.find_one({"_id": self._key(clone_id, chat_id)})

    async def set_emojis(self, clone_id: int, chat_id: int, emojis: list):
        await self.chats.update_one(
            {"_id": self._key(clone_id, chat_id)},
            {"$set": {"emojis": emojis}}
        )

    async def set_delay(self, clone_id: int, chat_id: int, delay: int):
        await self.chats.update_one(
            {"_id": self._key(clone_id, chat_id)},
            {"$set": {"delay": delay}}
        )

    async def toggle_enabled(self, clone_id: int, chat_id: int, enabled: bool):
        await self.chats.update_one(
            {"_id": self._key(clone_id, chat_id)},
            {"$set": {"enabled": enabled}}
        )

    async def set_multi_reaction(self, clone_id: int, chat_id: int, value: bool):
        await self.chats.update_one(
            {"_id": self._key(clone_id, chat_id)},
            {"$set": {"multi_reaction": value}}
        )

    async def get_all_chats_for_clone(self, clone_id: int):
        return [c async for c in self.chats.find({"clone_id": clone_id})]

    async def remove_chat(self, clone_id: int, chat_id: int):
        await self.chats.delete_one({"_id": self._key(clone_id, chat_id)})

    # ---------- users ----------
    async def add_user(self, clone_id: int, user_id: int):
        key = f"{clone_id}_{user_id}"
        await self.users.update_one(
            {"_id": key},
            {"$setOnInsert": {
                "clone_id": clone_id, "user_id": user_id,
                "joined_at": datetime.now(timezone.utc)
            }},
            upsert=True
        )

    async def count_users(self, clone_id: int):
        return await self.users.count_documents({"clone_id": clone_id})

    # ---------- stats ----------
    async def increment_reaction_count(self, clone_id: int, chat_id: int):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        key = f"{clone_id}_{chat_id}_{today}"
        await self.stats.update_one(
            {"_id": key},
            {
                "$inc": {"reactions_sent": 1},
                "$set": {"clone_id": clone_id, "chat_id": chat_id, "date": today}
            },
            upsert=True
        )

    async def get_total_reactions(self, clone_id: int):
        pipeline = [
            {"$match": {"clone_id": clone_id}},
            {"$group": {"_id": None, "total": {"$sum": "$reactions_sent"}}}
        ]
        result = [doc async for doc in self.stats.aggregate(pipeline)]
        return result[0]["total"] if result else 0
