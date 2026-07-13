from motor.motor_asyncio import AsyncIOMotorClient
from config import Config
from utils.logger import get_logger

logger = get_logger("mongo")


class Mongo:
    _client: AsyncIOMotorClient = None
    _db = None

    @classmethod
    def connect(cls):
        if cls._client is None:
            cls._client = AsyncIOMotorClient(Config.MONGO_URI)
            cls._db = cls._client[Config.DB_NAME]
            logger.info("Connected to MongoDB -> %s", Config.DB_NAME)
        return cls._db

    @classmethod
    def db(cls):
        if cls._db is None:
            return cls.connect()
        return cls._db
