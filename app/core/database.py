import logging
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.core.config import settings
from app.models.goal import Goal
from app.models.record import Record
from app.models.user import User

logger = logging.getLogger(__name__)

async def init_db():
    client = AsyncIOMotorClient(settings.DOCUMENT_DB_CONNECTION_STR)
    await init_beanie(
        database=client[settings.DOCUMENT_DATABASE_NAME],
        document_models=[
            User,
            Record,
            Goal
        ]
    )
    logger.info("DB 연결 성공 (database=%s)", settings.DOCUMENT_DATABASE_NAME)