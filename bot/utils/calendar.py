"""Утилиты для работы с календарем aiogram-dialog"""
from datetime import datetime, timedelta
from typing import Optional
import pytz
from aiogram_dialog.widgets.kbd import Calendar
from aiogram_dialog.widgets.text import CalendarScopeText

from bot.config import TIMEZONE


def get_calendar_widget(
    id_prefix: str = "calendar",
    on_date_selected: Optional[callable] = None
) -> Calendar:
    """
    Создание виджета календаря для aiogram-dialog
    
    Args:
        id_prefix: Префикс для ID виджета
        on_date_selected: Callback при выборе даты
    
    Returns:
        Виджет календаря
    """
    calendar = Calendar(
        id=f"{id_prefix}_calendar",
        on_date_selected=on_date_selected,
        on_scope_changed=None,
    )
    return calendar


def get_min_date() -> datetime:
    """Получить минимальную дату для календаря (сегодня)"""
    tz = pytz.timezone(TIMEZONE)
    return datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)


def get_max_date() -> datetime:
    """Получить максимальную дату для календаря (через 3 месяца)"""
    tz = pytz.timezone(TIMEZONE)
    return (datetime.now(tz) + timedelta(days=90)).replace(
        hour=23, minute=59, second=59, microsecond=0
    )


def combine_date_time(date: datetime, hours: int, minutes: int) -> datetime:
    """
    Объединение даты и времени
    
    Args:
        date: Дата
        hours: Часы
        minutes: Минуты
    
    Returns:
        Объединенная дата и время
    """
    tz = pytz.timezone(TIMEZONE)
    if date.tzinfo is None:
        date = tz.localize(date)
    
    return date.replace(hour=hours, minute=minutes, second=0, microsecond=0)


def format_time_for_display(hours: int, minutes: int) -> str:
    """
    Форматирование времени для отображения
    
    Args:
        hours: Часы
        minutes: Минуты
    
    Returns:
        Отформатированная строка (HH:MM)
    """
    return f"{hours:02d}:{minutes:02d}"

