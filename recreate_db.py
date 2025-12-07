"""Скрипт для пересоздания базы данных"""
import asyncio
import os
from pathlib import Path
from bot.config import DATABASE_URL
from bot.database.database import engine, init_db
from bot.database.models import Base

async def recreate_database():
    """Пересоздание базы данных"""
    # Удаляем существующую базу данных, если она есть
    if "sqlite" in DATABASE_URL:
        db_path = DATABASE_URL.split("///")[-1] if "///" in DATABASE_URL else DATABASE_URL.split(":///")[-1]
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"[OK] Deleted database file: {db_path}")
    
    # Создаем новую базу данных
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Удаляем все таблицы
        await conn.run_sync(Base.metadata.create_all)  # Создаем заново
    
    print("[OK] Database recreated successfully")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(recreate_database())

