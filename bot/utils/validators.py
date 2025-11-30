"""Валидация данных"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import pytz

from bot.config import TIMEZONE


def validate_duration_hours(duration: float) -> Tuple[bool, Optional[str]]:
    """
    Валидация продолжительности встречи
    
    Args:
        duration: Продолжительность в часах
    
    Returns:
        (is_valid, error_message)
    """
    if duration < 1:
        return False, "Минимальная продолжительность - 1 час"
    
    if duration > 24:
        return False, "Максимальная продолжительность - 24 часа"
    
    return True, None


def validate_participants_count(count: int) -> Tuple[bool, Optional[str]]:
    """
    Валидация количества участников
    
    Args:
        count: Количество участников
    
    Returns:
        (is_valid, error_message)
    """
    if count < 1:
        return False, "Минимальное количество участников - 1"
    
    if count > 50:
        return False, "Максимальное количество участников - 50"
    
    return True, None


def validate_meeting_datetime(
    date: datetime,
    min_hours_ahead: int = 1
) -> Tuple[bool, Optional[str]]:
    """
    Валидация даты и времени встречи
    
    Args:
        date: Дата и время встречи
        min_hours_ahead: Минимальное количество часов до встречи
    
    Returns:
        (is_valid, error_message)
    """
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    
    if date.tzinfo is None:
        date = tz.localize(date)
    
    if date < now:
        return False, "Нельзя выбрать прошедшую дату и время"
    
    min_datetime = now + timedelta(hours=min_hours_ahead)
    if date < min_datetime:
        return False, f"Встречу можно забронировать минимум за {min_hours_ahead} час(а) до начала"
    
    # Максимум на 3 месяца вперед
    max_datetime = now + timedelta(days=90)
    if date > max_datetime:
        return False, "Нельзя забронировать встречу более чем на 3 месяца вперед"
    
    return True, None


def validate_time_format(time_str: str) -> Tuple[bool, Optional[Tuple[int, int]]]:
    """
    Валидация формата времени (HH:MM)
    
    Args:
        time_str: Строка времени
    
    Returns:
        (is_valid, (hours, minutes) or None)
    """
    try:
        parts = time_str.split(':')
        if len(parts) != 2:
            return False, None
        
        hours = int(parts[0])
        minutes = int(parts[1])
        
        if not (0 <= hours < 24):
            return False, None
        
        if not (0 <= minutes < 60):
            return False, None
        
        return True, (hours, minutes)
    except (ValueError, AttributeError):
        return False, None

