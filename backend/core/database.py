# backend/app/core/database.py
"""Инициализация базы данных.

Основной движок для работы с базой данных.
"""

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import settings
from .exceptions import DatabaseException
from .logger import logger

Base = declarative_base()


# Создание движка с настройками из конфига
try:
    # Дополнительные параметры подключения
    connect_args = {}
    if settings.DB_USE_SSL:
        connect_args["ssl"] = "require"

    database_engine = create_async_engine(
        str(settings.SQLALCHEMY_DATABASE_URL),
        echo=settings.DEBUG,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE,
        connect_args=connect_args,
    )

except Exception as e:
    logger.error(f"Database connection error: {str(e)}", exc_info=True)
    raise DatabaseException(operation="database engine creation", reason=str(e)) from e

# Создаем фабрику асинхронных сессий
async_session_factory = async_sessionmaker(
    bind=database_engine, autoflush=False, expire_on_commit=False, class_=AsyncSession
)


async def check_database_connection() -> None:
    """Проверяет подключение к базе данных"""
    logger.info("Checking database connection...")
    async with database_engine.connect() as conn:
        try:
            # Выполняем простой запрос для проверки соединения
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection established")
        except Exception as e:
            logger.critical("Database connection failed", error=str(e))
            raise DatabaseException(
                operation="database connection check", reason=str(e)
            ) from e


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость для получения асинхронной сессии"""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise DatabaseException(operation="session operation", reason=str(e)) from e
        finally:
            await session.close()
