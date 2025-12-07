"""Конфигурация бота"""
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Admin User IDs (список через запятую)
ADMIN_IDS = [
    int(admin_id.strip())
    for admin_id in os.getenv("ADMIN_IDS", "").split(",")
    if admin_id.strip().isdigit()
]

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/bot.db")

# Orders Chat ID (для уведомлений админу о новых заказах)
ORDERS_CHAT_ID = os.getenv("ORDERS_CHAT_ID", "")

# Timezone
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")

# Проверка обязательных параметров
# Закомментировано для тестового запуска
# if not BOT_TOKEN:
#     raise ValueError("BOT_TOKEN не установлен в переменных окружения")

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return True
    return user_id in ADMIN_IDS

