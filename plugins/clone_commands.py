import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from database.reaction_db import ReactionDB
from database.clone_db import CloneDB
from plugins.auto_react import get_bot_id
from utils.logger import get_logger

logger = get_logger("broadcast")
reaction_db = ReactionDB()
clone_db = CloneDB()


@Client.on_message(filters.command("broadcast") & filters.private & filters.reply)
async def broadcast_cmd(client: Client, message: Message):
    clone_id = get_bot_id(client)
    clone = await clone_db.get_clone(clone_id)

    is_master_owner = message.from_user.id in __import__("config").Config.OWNER_IDS
    is_clone_owner = clone and clone.get("owner_id") == message.from_user.id

    if not (is_master_owner or is_clone_owner):
        return await message.reply_text("❌ Sirf bot owner ye command use kar sakta hai.")

    broadcast_msg = message.reply_to_message
    users = reaction_db.users.find({"clone_id": clone_id})

    sent, failed = 0, 0
    status = await message.reply_text("📤 Broadcast shuru ho raha hai...")

    async for user in users:
        try:
            await broadcast_msg.copy(user["user_id"])
            sent += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            try:
                await broadcast_msg.copy(user["user_id"])
                sent += 1
            except Exception:
                failed += 1
        except (UserIsBlocked, InputUserDeactivated):
            failed += 1
        except Exception as e:
            logger.warning("Broadcast failed for %s: %s", user["user_id"], e)
            failed += 1

    await status.edit_text(f"✅ Broadcast complete!\n\nSent: {sent}\nFailed: {failed}")
