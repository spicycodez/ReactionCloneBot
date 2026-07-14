"""
Collection: extra_owners
Schema:
{
    "_id": <user_id int>,
    "added_by": <user_id int>,
    "added_at": datetime,
}

Config.OWNER_IDS (from the Heroku/.env config var) are "super owners" -
they can never be removed via bot commands, and only they are allowed to
add/remove entries here. Anyone stored in this collection gets the same
master-bot owner powers (addclone, broadcast, etc.) as a super owner,
except the ability to manage other owners.
"""
from datetime import datetime, timezone
from database.mongo import Mongo


class OwnerDB:
    def __init__(self):
        self.col = Mongo.db()["extra_owners"]

    async def add_owner(self, user_id: int, added_by: int):
        await self.col.update_one(
            {"_id": user_id},
            {"$set": {"added_by": added_by, "added_at": datetime.now(timezone.utc)}},
            upsert=True,
        )

    async def remove_owner(self, user_id: int):
        await self.col.delete_one({"_id": user_id})

    async def is_owner(self, user_id: int) -> bool:
        return await self.col.find_one({"_id": user_id}) is not None

    async def list_owners(self):
        return [o async for o in self.col.find({})]
