"""
Collection: bot_sessions
Schema:
{
    "_id": str,               # e.g. "master"
    "session_string": str,
}

Used to persist the master bot's Pyrogram session across restarts, so it
resumes instead of re-running the bot-token login flow every deploy
(Heroku's filesystem is ephemeral, so a file-based session never
survives a restart anyway).
"""
from database.mongo import Mongo


class SessionStore:
    def __init__(self):
        self.col = Mongo.db()["bot_sessions"]

    async def get(self, name: str):
        doc = await self.col.find_one({"_id": name})
        return doc["session_string"] if doc else None

    async def save(self, name: str, session_string: str):
        await self.col.update_one(
            {"_id": name},
            {"$set": {"session_string": session_string}},
            upsert=True,
        )
