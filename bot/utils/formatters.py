"""Форматирование сообщений"""
from datetime import datetime
from typing import Optional, List
import pytz

from bot.config import TIMEZONE
from bot.database.models import Order, Profile, Game


def format_profile_message(
    profile: Profile,
    games: Optional[List[Game]] = None,
    show_navigation: bool = True,
    current_index: Optional[int] = None,
    total_count: Optional[int] = None
) -> str:
    """
    Форматирование сообщения с анкетой девушки
    
    Args:
        profile: Анкета
        games: Список игр
        show_navigation: Показывать ли навигацию
        current_index: Текущий индекс (для навигации)
        total_count: Общее количество (для навигации)
    
    Returns:
        Отформатированное сообщение
    """
    lines = []
    
    # Имя и возраст
    age_str = f" ({profile.age} лет)" if profile.age else ""
    lines.append(f"💃 {profile.name}{age_str}")
    
    # Описание
    if profile.description:
        lines.append(f"\n📝 {profile.description}")
    
    # Игры
    if games:
        game_names = [game.name for game in games]
        lines.append(f"\n🎮 Игры: {', '.join(game_names)}")
    
    # Тарифы
    lines.append(f"\n💰 Тарифы на общение:")
    lines.append(f"• Аудио-чат — {profile.audio_chat_price:.0f} ₽/час")
    lines.append(f"• Видео-чат — {profile.video_chat_price:.0f} ₽/час")
    
    if profile.private_price:
        lines.append(f"• Приватка — {profile.private_price:.0f} ₽")
    
    # Канал
    if profile.channel_link:
        lines.append(f"\n🔗 Канал: {profile.channel_link}")
    
    # Навигация
    if show_navigation and current_index is not None and total_count:
        nav_parts = []
        if current_index > 0:
            nav_parts.append("<-Предыдущая")
        if current_index < total_count - 1:
            nav_parts.append("Следующая->")
        if nav_parts:
            lines.append(f"\n{' | '.join(nav_parts)}")
    
    return "\n".join(lines)


def format_order_message(order: Order, include_connection_link: bool = False) -> str:
    """
    Форматирование сообщения с заказом
    
    Args:
        order: Заказ
        include_connection_link: Включать ли ссылку на подключение
    
    Returns:
        Отформатированное сообщение
    """
    format_emoji = "🎧" if order.format_type == "audio" else "🎥"
    format_name = "Аудио-чат" if order.format_type == "audio" else "Видео-чат"
    
    lines = [
        f"📄 Заказ {order.order_number}",
        f"🎀 Модель: {order.profile.channel_link or 'Не указана'}",
        f"📋 Тип: Заказ",
        f"💰 Сумма: {order.total_price:.0f} ₽",
        f"{format_emoji} Формат: {format_name}",
        f"⏱️ Продолжительность: {order.duration_hours:.0f} ч.",
        f"📅 Дата: {order.date.strftime('%d %B %Y')}",
        f"⏰ Время: {order.date.strftime('%H:%M')}",
        f"👥 Участников: {order.participants_count}",
        f"📅 Создан: {order.created_at.strftime('%d.%m.%Y %H:%M')}"
    ]
    
    if include_connection_link and order.conference_link:
        lines.append(f"\n—--------")
        lines.append(f"Комментарий как подключиться: {order.conference_link}")
    
    return "\n".join(lines)


def format_order_summary(order: Order) -> str:
    """
    Форматирование итогового сообщения о заказе
    
    Returns:
        Отформатированное сообщение
    """
    format_emoji = "🎧" if order.format_type == "audio" else "🎥"
    format_name = "Аудио-чат" if order.format_type == "audio" else "Видео-чат"
    
    from bot.services.payment import format_price_calculation
    
    price_per_hour = order.base_price / order.duration_hours
    calculation = {
        'base_price': order.base_price,
        'additional_participants_price': order.additional_participants_price,
        'total_price': order.total_price
    }
    
    lines = [
        "✅ Заказ оформлен!",
        f"{format_emoji} Формат: {format_name}",
        f"🎮 Игра: {order.game_name or 'Не указана'}",
        f"📅 Дата: {order.date.strftime('%d.%m.%Y')}",
        f"⏰ Время: {order.date.strftime('%H:%M')}",
        f"⏱️ Продолжительность: {order.duration_hours:.0f} ч.",
        f"👥 Участников: {order.participants_count}",
        "",
        format_price_calculation(price_per_hour, order.duration_hours, order.participants_count, calculation),
        "",
        "Пожалуйста, подождите с Вами свяжется администратор для завершения заказа."
    ]
    
    return "\n".join(lines)


def format_date_for_display(date: datetime) -> str:
    """
    Форматирование даты для отображения
    
    Args:
        date: Дата
    
    Returns:
        Отформатированная строка
    """
    tz = pytz.timezone(TIMEZONE)
    if date.tzinfo is None:
        date = tz.localize(date)
    
    # Русские названия месяцев
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    
    return f"{date.day} {months[date.month - 1]} {date.year}"

