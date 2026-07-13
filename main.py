import asyncio
import sys

from pyrogram import Client

from config import Config
from database.mongo import Mongo
from clone.clone_manager import clone_manager
from utils.logger import get_logger
from utils.startup_log import send_startup_log

logger = get_logger("main")

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
    master = Client(
        name="master_bot",
        api_id=Config.API_ID,
        api_hash=Config.API_HASH,
        bot_token=Config.BOT_TOKEN,
        plugins=dict(root="plugins"),
    )
    master.bot_id = None  # will resolve to client.me.id via get_bot_id()
    master.bot_token = Config.BOT_TOKEN  # used by auto_react.py for the Bot API reactions call
    await master.start()
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
