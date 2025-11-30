"""Фильтр для проверки администратора"""
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from bot.config import is_admin


class AdminFilter(BaseFilter):
    """Фильтр для проверки, является ли пользователь администратором"""
    
    async def __call__(self, obj: Message | CallbackQuery) -> bool:
        """Проверка прав администратора"""
        user_id = obj.from_user.id if hasattr(obj, 'from_user') else None
        if not user_id:
            return False
        
        return is_admin(user_id)

