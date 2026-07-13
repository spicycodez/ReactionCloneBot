from pyrogram import Client, filters
from pyrogram.types import Message

from config import Config
from database.clone_db import CloneDB
from database.reaction_db import ReactionDB
from clone.clone_manager import clone_manager

clone_db = CloneDB()
reaction_db = ReactionDB()

owner_filter = filters.user(Config.OWNER_IDS) if Config.OWNER_IDS else filters.user([])


@Client.on_message(filters.command("addclone") & filters.private & owner_filter)
async def add_clone_cmd(client: Client, message: Message):
    if len(message.command) != 2:
        return await message.reply_text("⚠️ Usage: `/addclone <bot_token>`")

    bot_token = message.command[1]
    status_msg = await message.reply_text("⏳ Token verify ho raha hai aur clone start ho raha hai...")

    try:
        me = await clone_manager.start_clone(bot_token, message.from_user.id)
        await status_msg.edit_text(
            f"✅ **Clone successfully created!**\n\n"
            f"Bot: @{me.username}\n"
            f"ID: `{me.id}`\n\n"
            f"Ab is bot ko apne group/channel me admin bana kar add karo."
        )
    except ValueError as e:
        await status_msg.edit_text(f"❌ Token invalid: {e}")
    except Exception as e:
        await status_msg.edit_text(f"❌ Clone start karne me error: {e}")


@Client.on_message(filters.command("listclones") & filters.private & owner_filter)
async def list_clones_cmd(client: Client, message: Message):
    clones = await clone_db.get_all_clones()
    if not clones:
        return await message.reply_text("ℹ️ Abhi koi clone nahi hai.")

    text = "**🤖 All Clones:**\n\n"
    for c in clones:
        running = c["_id"] in clone_manager.list_active()
        status_icon = "🟢" if running else "🔴"
        text += f"{status_icon} @{c['bot_username']} — `{c['_id']}` — {c['status']}\n"

    await message.reply_text(text)


@Client.on_message(filters.command("removeclone") & filters.private & owner_filter)
async def remove_clone_cmd(client: Client, message: Message):
    if len(message.command) != 2 or not message.command[1].isdigit():
        return await message.reply_text("⚠️ Usage: `/removeclone <bot_id>`")

    bot_id = int(message.command[1])
    clone = await clone_db.get_clone(bot_id)
    if not clone:
        return await message.reply_text("❌ Ye clone exist nahi karta.")

    await clone_manager.delete_clone(bot_id)
    await message.reply_text(f"✅ Clone @{clone['bot_username']} delete ho gaya.")


@Client.on_message(filters.command("stopclone") & filters.private & owner_filter)
async def stop_clone_cmd(client: Client, message: Message):
    if len(message.command) != 2 or not message.command[1].isdigit():
        return await message.reply_text("⚠️ Usage: `/stopclone <bot_id>`")

    bot_id = int(message.command[1])
    await clone_manager.stop_clone(bot_id)
    await message.reply_text("✅ Clone stop ho gaya (data safe hai, /addclone se dobara start karo).")


@Client.on_message(filters.command("clonestats") & filters.private & owner_filter)
async def clone_stats_cmd(client: Client, message: Message):
    if len(message.command) != 2 or not message.command[1].isdigit():
        return await message.reply_text("⚠️ Usage: `/clonestats <bot_id>`")

    bot_id = int(message.command[1])
    clone = await clone_db.get_clone(bot_id)
    if not clone:
        return await message.reply_text("❌ Ye clone exist nahi karta.")

    total_users = await reaction_db.count_users(bot_id)
    total_reactions = await reaction_db.get_total_reactions(bot_id)
    total_chats = len(await reaction_db.get_all_chats_for_clone(bot_id))

    text = (
        f"**📊 Stats — @{clone['bot_username']}**\n\n"
        f"Total Users: {total_users}\n"
        f"Total Chats: {total_chats}\n"
        f"Total Reactions Sent: {total_reactions}\n"
        f"Status: {clone['status']}"
    )
    await message.reply_text(text)


@Client.on_message(filters.command("stats") & filters.private & owner_filter)
async def global_stats_cmd(client: Client, message: Message):
    total_clones = await clone_db.count()
    active = len(clone_manager.list_active())
    await message.reply_text(
        f"**📊 Global Stats**\n\nTotal Clones: {total_clones}\nActive Clones: {active}"
    )
