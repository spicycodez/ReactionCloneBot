from pyrogram import Client, filters
from pyrogram.types import Message

from config import Config
from database.reaction_db import ReactionDB
from plugins.auto_react import get_bot_id
from utils.markdown import escape_markdown

reaction_db = ReactionDB()

START_TEXT = """👋 **Namaste {name}!**

Main ek **Auto Reaction Bot** hoon. Mujhe apne group/channel me admin bana kar add karo, main automatically har naye message par reaction laga dunga.

**Commands:**
/setreaction 👍❤️🔥 - reaction emojis set karo (space se alag)
/setdelay 5 - reaction delay seconds me set karo
/togglereact - reaction on/off karo is chat ke liye
/mysettings - current settings dekho
/clone - apna khud ka reaction bot banwane ke baare me jaano
/help - sab commands dekho
"""

HELP_TEXT_CHAT_ADMIN = """**📋 Commands List**

**Chat Admin Commands (group/channel me use karo):**
/setreaction <emojis> - Reaction emojis set karo. Example: `/setreaction 👍 ❤️ 🔥`
/setdelay <seconds> - Reaction se pehle wait time. Example: `/setdelay 3`
/togglereact - Reaction on/off toggle
/multireact on|off - Ek message par multiple emoji reaction bhejo
/mysettings - Is chat ki current settings dekho
/clone - apna khud ka reaction bot banwane ke baare me jaano
"""

HELP_TEXT_MASTER_OWNER = """
**Bot Owner Commands:**
/addclone <bot_token> - Naya clone bot banao
/listclones - Sab clones dekho
/removeclone <bot_id> - Clone delete karo
/clonestats <bot_id> - Clone ka stats dekho
/broadcast <message> - (reply karke) master + sab active clones ke users ko ek saath bhejo
"""

CLONE_PROMO_TEXT = """🤖 **Want your own Reaction Bot?**

This bot is a clone — anyone can get their own personal reaction bot built just like this one, fully branded for their own group or channel.

To get your own bot made, contact: @{contact}
"""


@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    clone_id = get_bot_id(client)
    await reaction_db.add_user(clone_id, message.from_user.id)
    name = escape_markdown(message.from_user.first_name) or "Dost"
    await message.reply_text(START_TEXT.format(name=name))


@Client.on_message(filters.command("help"))
async def help_cmd(client: Client, message: Message):
    text = HELP_TEXT_CHAT_ADMIN
    is_master = not getattr(client, "is_clone", False)

    if is_master and message.from_user.id in Config.OWNER_IDS:
        text += HELP_TEXT_MASTER_OWNER

    await message.reply_text(text)


@Client.on_message(filters.command("clone"))
async def clone_promo_cmd(client: Client, message: Message):
    await message.reply_text(CLONE_PROMO_TEXT.format(contact=Config.CONTACT_USERNAME))
