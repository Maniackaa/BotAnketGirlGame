"""Подключение к базе данных"""
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from bot.config import DATABASE_URL
from bot.database.models import Base

# Создание директории для БД, если её нет
if "sqlite" in DATABASE_URL:
    # Извлекаем путь к файлу БД из URL
    db_path = DATABASE_URL.split("///")[-1] if "///" in DATABASE_URL else DATABASE_URL.split(":///")[-1]
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        print(f"✅ Создана директория для БД: {db_dir}")

# Создание движка
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

# Создание фабрики сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Инициализация базы данных (создание таблиц)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Закрытие соединения с БД"""
    await engine.dispose()


async def get_session() -> AsyncSession:
    """Получение сессии БД"""
    async with async_session_maker() as session:
        yield session

