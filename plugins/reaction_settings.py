from pyrogram import Client, filters
from pyrogram.types import Message, ChatPrivileges
from pyrogram.enums import ChatMemberStatus

from config import Config
from database.reaction_db import ReactionDB
from plugins.auto_react import get_bot_id

reaction_db = ReactionDB()


async def is_chat_admin(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False


async def is_authorized(client: Client, message: Message) -> bool:
    """
    In channels every post is sent "as the channel" - Telegram sets
    message.from_user to None and message.sender_chat to the channel
    itself, so message.from_user.id crashes with AttributeError. The same
    thing happens in groups when an anonymous admin sends a command.
    There's no per-user id available in that case, so we treat "posted as
    the chat itself" as proof of admin rights (only admins can post/send
    messages as the channel/anonymously in the first place).
    """
    if message.from_user:
        return await is_chat_admin(client, message.chat.id, message.from_user.id)
    if message.sender_chat and message.sender_chat.id == message.chat.id:
        return True
    return False


@Client.on_message(filters.command("setreaction") & (filters.group | filters.channel))
async def set_reaction_cmd(client: Client, message: Message):
    if not await is_authorized(client, message):
        return await message.reply_text("❌ Sirf chat admins ye command use kar sakte hain.")

    if len(message.command) < 2:
        return await message.reply_text(
            "⚠️ Usage: `/setreaction 👍 ❤️ 🔥`\n\nAllowed emojis dekhne ke liye /allowedemojis bhejo."
        )

    emojis = message.command[1:]
    invalid = [e for e in emojis if e not in Config.ALLOWED_EMOJIS]
    if invalid:
        return await message.reply_text(
            f"❌ Ye emoji Telegram reactions me allowed nahi hain: {' '.join(invalid)}\n"
            f"/allowedemojis se pura list dekho."
        )

    clone_id = get_bot_id(client)
    settings = await reaction_db.get_chat_settings(clone_id, message.chat.id)
    if not settings:
        await reaction_db.register_chat(
            clone_id, message.chat.id, message.chat.title or str(message.chat.id),
            emojis, Config.DEFAULT_DELAY
        )
    else:
        await reaction_db.set_emojis(clone_id, message.chat.id, emojis)

    await message.reply_text(f"✅ Reaction emojis set ho gaye: {' '.join(emojis)}")


@Client.on_message(filters.command("setdelay") & (filters.group | filters.channel))
async def set_delay_cmd(client: Client, message: Message):
    if not await is_authorized(client, message):
        return await message.reply_text("❌ Sirf chat admins ye command use kar sakte hain.")

    if len(message.command) != 2 or not message.command[1].isdigit():
        return await message.reply_text("⚠️ Usage: `/setdelay 5` (0-60 seconds)")

    delay = int(message.command[1])
    if delay < 0 or delay > 60:
        return await message.reply_text("⚠️ Delay 0 se 60 seconds ke beech hona chahiye.")

    clone_id = get_bot_id(client)
    settings = await reaction_db.get_chat_settings(clone_id, message.chat.id)
    if not settings:
        await reaction_db.register_chat(
            clone_id, message.chat.id, message.chat.title or str(message.chat.id),
            Config.DEFAULT_EMOJIS, delay
        )
    else:
        await reaction_db.set_delay(clone_id, message.chat.id, delay)

    await message.reply_text(f"✅ Reaction delay set ho gaya: {delay} second(s)")


@Client.on_message(filters.command("togglereact") & (filters.group | filters.channel))
async def toggle_react_cmd(client: Client, message: Message):
    if not await is_authorized(client, message):
        return await message.reply_text("❌ Sirf chat admins ye command use kar sakte hain.")

    clone_id = get_bot_id(client)
    settings = await reaction_db.get_chat_settings(clone_id, message.chat.id)
    if not settings:
        await reaction_db.register_chat(
            clone_id, message.chat.id, message.chat.title or str(message.chat.id),
            Config.DEFAULT_EMOJIS, Config.DEFAULT_DELAY
        )
        new_state = True
    else:
        new_state = not settings.get("enabled", True)
        await reaction_db.toggle_enabled(clone_id, message.chat.id, new_state)

    status = "✅ ON" if new_state else "❌ OFF"
    await message.reply_text(f"Auto reaction ab **{status}** hai is chat ke liye.")


@Client.on_message(filters.command("multireact") & (filters.group | filters.channel))
async def multi_react_cmd(client: Client, message: Message):
    if not await is_authorized(client, message):
        return await message.reply_text("❌ Sirf chat admins ye command use kar sakte hain.")

    if len(message.command) != 2 or message.command[1].lower() not in ("on", "off"):
        return await message.reply_text("⚠️ Usage: `/multireact on` ya `/multireact off`")

    value = message.command[1].lower() == "on"
    clone_id = get_bot_id(client)
    await reaction_db.set_multi_reaction(clone_id, message.chat.id, value)
    await message.reply_text(f"✅ Multi-reaction mode: {'ON' if value else 'OFF'}")


@Client.on_message(filters.command("mysettings") & (filters.group | filters.channel))
async def my_settings_cmd(client: Client, message: Message):
    clone_id = get_bot_id(client)
    settings = await reaction_db.get_chat_settings(clone_id, message.chat.id)
    if not settings:
        return await message.reply_text("ℹ️ Is chat ke liye abhi default settings hain.")

    text = (
        f"**⚙️ Reaction Settings — {message.chat.title}**\n\n"
        f"Status: {'✅ ON' if settings.get('enabled') else '❌ OFF'}\n"
        f"Emojis: {' '.join(settings.get('emojis', []))}\n"
        f"Delay: {settings.get('delay')} second(s)\n"
        f"Multi-reaction: {'ON' if settings.get('multi_reaction') else 'OFF'}"
    )
    await message.reply_text(text)


@Client.on_message(filters.command("allowedemojis"))
async def allowed_emojis_cmd(client: Client, message: Message):
    await message.reply_text(
        "**Allowed reaction emojis:**\n\n" + " ".join(Config.ALLOWED_EMOJIS)
    )

