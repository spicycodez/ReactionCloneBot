import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    API_ID = int(os.environ.get("API_ID", "0"))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

    MONGO_URI = os.environ.get("MONGO_URI", "")
    DB_NAME = os.environ.get("DB_NAME", "reaction_bot")

    OWNER_IDS = [int(x) for x in os.environ.get("OWNER_IDS", "").split(",") if x.strip()]

    # Shown by /clone as the contact for getting a bot like this made.
    # Set CONTACT_USERNAME in your .env/Heroku config vars (without the @).
    CONTACT_USERNAME = os.environ.get("CONTACT_USERNAME", "SexyProfessor")

    DEFAULT_EMOJIS = os.environ.get("DEFAULT_EMOJIS", "👍,❤️,🔥").split(",")
    DEFAULT_DELAY = int(os.environ.get("DEFAULT_DELAY", "1"))
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0")) if os.environ.get("LOG_CHANNEL") else None

    # Allowed Telegram reaction emojis (subset most commonly enabled)
    ALLOWED_EMOJIS = [
        "👍", "👎", "❤️", "🔥", "🥰", "👏", "😁", "🤔",
        "🤯", "😱", "🤬", "😢", "🎉", "🤩", "🤮", "💩",
        "🙏", "👌", "🕊", "🤡", "🥱", "🥴", "😍", "🐳",
        "❤️‍🔥", "🌚", "🌭", "💯", "🤣", "⚡", "🍌", "🏆",
        "💔", "🤨", "😐", "🍓", "🍾", "💋", "🖕", "😈",
        "😴", "😭", "🤓", "👻", "👨‍💻", "👀", "🎃", "🙈",
        "😇", "😨", "🤝", "✍️", "🤗", "🫡", "🎅", "🎄",
        "☃️", "💅", "🤪", "🗿", "🆒", "💘", "🙉", "🦄",
        "😘", "💊", "🙊", "😎", "👾", "🤷", "😡"
    ]

    # Rate limit protection (per clone)
    MAX_REACTIONS_PER_MINUTE = 20
