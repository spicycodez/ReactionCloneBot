import asyncio
import sys

from pyrogram import Client

from config import Config
from database.mongo import Mongo
from database.session_store import SessionStore
from clone.clone_manager import clone_manager
from utils.logger import get_logger
from utils.startup_log import send_startup_log

logger = get_logger("main")
session_store = SessionStore()

if sys.platform != "win32":
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass


async def main():
    # 1. Connect DB first
    Mongo.connect()

    # 2. Start master bot (this itself is a working reaction bot + admin panel)
    # Resume from a cached session string when we have one, instead of
    # re-running the bot-token login flow on every restart - Heroku's
    # filesystem is ephemeral so a plain file session never survives a
    # restart, and repeated logins on the same token can hit Telegram's
    # FLOOD_WAIT on auth.ImportBotAuthorization.
    saved_session = await session_store.get("master")
    client_kwargs = dict(
        name="master_bot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        plugins=dict(root="plugins"),
        in_memory=True,
    )
    if saved_session:
        client_kwargs["session_string"] = saved_session
    else:
        client_kwargs["bot_token"] = Config.BOT_TOKEN

    master = Client(**client_kwargs)
    master.bot_id = None  # will resolve to client.me.id via get_bot_id()
    master.bot_token = Config.BOT_TOKEN  # used by auto_react.py for the Bot API reactions call
    await master.start()

    if not saved_session:
        await session_store.save("master", await master.export_session_string())

    me = await master.get_me()
    master.bot_id = me.id
    logger.info("Master bot started: @%s", me.username)
    await send_startup_log(master, me, label="Master Bot")

    # 3. Resume any clones that were running before restart
    await clone_manager.restart_all_clones()

    logger.info("All systems operational. Listening for messages...")

    # Keep the master bot alive
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
