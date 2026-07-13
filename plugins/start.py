from pyrogram import Client, filters
from pyrogram.types import Message

from database.reaction_db import ReactionDB
from plugins.auto_react import get_bot_id

reaction_db = ReactionDB()

START_TEXT = """👋 **Namaste {name}!**

Main ek **Auto Reaction Bot** hoon. Mujhe apne group/channel me admin bana kar add karo, main automatically har naye message par reaction laga dunga.

**Commands:**
/setreaction 👍❤️🔥 - reaction emojis set karo (space se alag)
/setdelay 5 - reaction delay seconds me set karo
/togglereact - reaction on/off karo is chat ke liye
/mysettings - current settings dekho
/help - sab commands dekho
"""

HELP_TEXT = """**📋 Commands List**

**Chat Admin Commands (group/channel me use karo):**
/setreaction <emojis> - Reaction emojis set karo. Example: `/setreaction 👍 ❤️ 🔥`
/setdelay <seconds> - Reaction se pehle wait time. Example: `/setdelay 3`
/togglereact - Reaction on/off toggle
/multireact on|off - Ek message par multiple emoji reaction bhejo
/mysettings - Is chat ki current settings dekho

**Bot Owner Commands:**
/addclone <bot_token> - Naya clone bot banao
/listclones - Sab clones dekho
/removeclone <bot_id> - Clone delete karo
/clonestats <bot_id> - Clone ka stats dekho
/broadcast <message> - Sab clone users ko message bhejo
"""


@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    clone_id = get_bot_id(client)
    await reaction_db.add_user(clone_id, message.from_user.id)
    await message.reply_text(START_TEXT.format(name=message.from_user.first_name))


@Client.on_message(filters.command("help"))
async def help_cmd(client: Client, message: Message):
    await message.reply_text(HELP_TEXT)
