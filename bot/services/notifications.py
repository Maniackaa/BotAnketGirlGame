"""Сервис для отправки уведомлений администратору"""
from datetime import datetime
from typing import Optional
from aiogram import Bot
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import ORDERS_CHAT_ID
from bot.database.models import Order, User, Profile, Game
from bot.database.repositories import OrderRepository
from bot.services.payment import format_price_calculation


async def send_new_order_notification(
    bot: Bot,
    order: Order,
    user: User,
    profile: Profile,
    game: Optional[Game] = None
) -> Message:
    """
    Отправка уведомления админу о новом заказе
    
    Args:
        bot: Экземпляр бота
        order: Заказ
        user: Пользователь
        profile: Анкета
        game: Игра (опционально)
    
    Returns:
        Отправленное сообщение
    """
    if not ORDERS_CHAT_ID:
        raise ValueError("ORDERS_CHAT_ID не установлен в конфигурации")
    
    username = f"@{user.username}" if user.username else "Не указан"
    
    format_emoji = "🎧" if order.format_type == "audio" else "🎥"
    format_name = "Аудио-чат" if order.format_type == "audio" else "Видео-чат"
    
    game_name = game.name if game else order.game_name or "Не указана"
    
    calculation = {
        'base_price': order.base_price,
        'additional_participants_price': order.additional_participants_price,
        'total_price': order.total_price
    }
    
    price_per_hour = order.base_price / order.duration_hours
    
    text = (
        f"🆕 Новый заказ!\n\n"
        f"Заказ номер: {order.order_number}\n"
        f"Пользователь: {username}\n"
        f"ID: {user.telegram_id}\n"
        f"Время оформления заказа: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"{format_emoji} Формат: {format_name}\n"
        f"🎮 Игра: {game_name}\n"
        f"📅 Дата: {order.date.strftime('%d.%m.%Y')}\n"
        f"⏰ Время: {order.date.strftime('%H:%M')}\n"
        f"⏱️ Продолжительность: {order.duration_hours:.0f} ч.\n"
        f"👥 Участников: {order.participants_count}\n\n"
        f"{format_price_calculation(price_per_hour, order.duration_hours, order.participants_count, calculation)}"
    )
    
    return await bot.send_message(
        chat_id=ORDERS_CHAT_ID,
        text=text
    )


async def send_payment_check_notification(
    bot: Bot,
    order: Order
) -> Message:
    """
    Уведомление админу о необходимости проверить оплату
    
    Отправляется через 15 минут после статуса "processing"
    """
    if not ORDERS_CHAT_ID:
        raise ValueError("ORDERS_CHAT_ID не установлен в конфигурации")
    
    text = f"⏰ Заказ {order.order_number} проверить оплату"
    
    return await bot.send_message(
        chat_id=ORDERS_CHAT_ID,
        text=text
    )


async def send_unpaid_order_notification(
    bot: Bot,
    order: Order
) -> Message:
    """
    Уведомление админу о неоплаченном заказе
    
    Отправляется через 30 минут после статуса "not_paid"
    """
    if not ORDERS_CHAT_ID:
        raise ValueError("ORDERS_CHAT_ID не установлен в конфигурации")
    
    text = f"❌ Заказ {order.order_number} не оплачен"
    
    return await bot.send_message(
        chat_id=ORDERS_CHAT_ID,
        text=text
    )


async def send_order_cancellation_to_user(
    bot: Bot,
    order: Order,
    payment_status: str
) -> Message:
    """
    Отправка уведомления пользователю об отмене заказа
    
    Args:
        bot: Экземпляр бота
        order: Заказ
        payment_status: Статус оплаты на момент отмены
    """
    user = order.user
    
    if payment_status == "paid":
        text = (
            "К сожалению, ваш заказ был отменён.\n\n"
            "Возврат денежных средств уже инициирован, срок зачисления до 5 рабочих дней, "
            "в зависимости от Вашего банка.\n\n"
            "Если остались вопросы - напишите нам."
        )
    elif payment_status == "not_paid":
        text = (
            "К сожалению, ваш заказ был отменён.\n\n"
            "Если остались вопросы - напишите нам."
        )
    else:
        # processing - не должно происходить, но на всякий случай
        text = (
            "К сожалению, ваш заказ был отменён.\n\n"
            "Если остались вопросы - напишите нам."
        )
    
    return await bot.send_message(
        chat_id=user.telegram_id,
        text=text
    )

