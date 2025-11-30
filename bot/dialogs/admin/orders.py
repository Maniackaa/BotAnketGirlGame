"""Диалог управления заказами"""
from datetime import datetime
from typing import Optional
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import (
    Button, Row, Column, ScrollingGroup, SwitchTo, 
    Back, Cancel, Group, ListGroup
)
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram.types import Message, CallbackQuery
from aiogram_dialog.api.entities import ShowMode
import pytz

from bot.dialogs.admin import states
from bot.database.database import async_session_maker
from bot.database.repositories import OrderRepository
from bot.database.models import Order
from bot.services.notifications import send_order_cancellation_to_user
from bot.utils.formatters import format_order_message
from bot.config import TIMEZONE
from sqlalchemy import select


async def get_orders_data(dialog_manager: DialogManager, **kwargs):
    """Получение списка заказов для отображения"""
    # Очищаем старые данные при открытии главного окна
    if "selected_order_id" in dialog_manager.dialog_data:
        del dialog_manager.dialog_data["selected_order_id"]
    if "message_user_id" in dialog_manager.dialog_data:
        del dialog_manager.dialog_data["message_user_id"]
    if "message_order_id" in dialog_manager.dialog_data:
        del dialog_manager.dialog_data["message_order_id"]
    
    async with async_session_maker() as session:
        orders = await OrderRepository.get_all(session)
        has_orders = len(orders) > 0 if orders else False
        return {
            "orders": orders or [],
            "has_orders": has_orders,
            "orders_text": "Выберите заказ:" if has_orders else "❌ Заказов пока нет",
        }


async def get_order_detail_data(dialog_manager: DialogManager, **kwargs):
    """Получение деталей заказа"""
    order_id = dialog_manager.dialog_data.get("selected_order_id")
    if not order_id:
        return {
            "order": None,
            "order_number": "N/A",
            "user_username": "N/A",
            "user_id": "N/A",
            "profile_name": "N/A",
            "format_emoji": "N/A",
            "format_name": "N/A",
            "game_name": "N/A",
            "date": "N/A",
            "time": "N/A",
            "duration": "N/A",
            "participants": "N/A",
            "total_price": "N/A",
            "payment_status": "N/A",
            "conference_link": "N/A",
            "created_at": "N/A",
        }
    
    async with async_session_maker() as session:
        order = await OrderRepository.get_by_id(session, order_id)
        if order:
            format_emoji = "🎧" if order.format_type == "audio" else "🎥"
            format_name = "Аудио-чат" if order.format_type == "audio" else "Видео-чат"
            
            payment_status_text = {
                "not_paid": "❌ Не оплачено",
                "processing": "⏳ В обработке",
                "paid": "✅ Оплачено",
            }.get(order.payment_status, order.payment_status)
            
            return {
                "order_number": order.order_number,
                "user_username": f"@{order.user.username}" if order.user.username else "Не указан",
                "user_id": order.user.telegram_id,
                "profile_name": order.profile.name,
                "format_emoji": format_emoji,
                "format_name": format_name,
                "game_name": order.game_name or "Не указана",
                "date": order.date.strftime("%d.%m.%Y"),
                "time": order.date.strftime("%H:%M"),
                "duration": f"{order.duration_hours:.0f} ч.",
                "participants": order.participants_count,
                "total_price": f"{order.total_price:.0f} ₽",
                "payment_status": payment_status_text,
                "conference_link": order.conference_link or "Не указана",
                "created_at": order.created_at.strftime("%d.%m.%Y %H:%M"),
            }
        return {
            "order": None,
            "order_number": "N/A",
            "user_username": "N/A",
            "user_id": "N/A",
            "profile_name": "N/A",
            "format_emoji": "N/A",
            "format_name": "N/A",
            "game_name": "N/A",
            "date": "N/A",
            "time": "N/A",
            "duration": "N/A",
            "participants": "N/A",
            "total_price": "N/A",
            "payment_status": "N/A",
            "conference_link": "N/A",
            "created_at": "N/A",
        }


async def on_order_select(c: CallbackQuery, button: Button, manager: DialogManager):
    """Выбор заказа"""
    # В ListGroup item_id передается через callback_data
    if c.data:
        parts = c.data.split(":")
        item_id = parts[-1] if len(parts) >= 3 else (parts[-1] if parts else None)
    else:
        item_id = button.widget_id.split(":")[-1] if ":" in button.widget_id else None
    
    if not item_id:
        await c.answer("❌ Ошибка: не удалось получить ID заказа", show_alert=True)
        return
    
    order_id = int(item_id)
    manager.dialog_data["selected_order_id"] = order_id
    await manager.switch_to(states.AdminOrders.DETAIL)


async def on_change_datetime(c: CallbackQuery, button: Button, manager: DialogManager):
    """Изменение даты и времени заказа"""
    await manager.switch_to(states.AdminOrders.CHANGE_DATETIME)


async def on_change_payment_status(c: CallbackQuery, button: Button, manager: DialogManager):
    """Изменение статуса оплаты"""
    await manager.switch_to(states.AdminOrders.CHANGE_PAYMENT_STATUS)


async def on_add_conference_link(c: CallbackQuery, button: Button, manager: DialogManager):
    """Добавление ссылки на конференцию"""
    await manager.switch_to(states.AdminOrders.ADD_CONFERENCE_LINK)


async def on_cancel_order(c: CallbackQuery, button: Button, manager: DialogManager):
    """Отмена заказа"""
    await manager.switch_to(states.AdminOrders.CANCEL)


async def on_message_user(c: CallbackQuery, button: Button, manager: DialogManager):
    """Написать пользователю"""
    order_id = manager.dialog_data.get("selected_order_id")
    if not order_id:
        await c.answer("❌ Заказ не выбран", show_alert=True)
        return
    
    async with async_session_maker() as session:
        order = await OrderRepository.get_by_id(session, order_id)
        if order:
            user_id = order.user.telegram_id
            manager.dialog_data["message_user_id"] = user_id
            manager.dialog_data["message_order_id"] = order_id
            await manager.switch_to(states.AdminOrders.MESSAGE_USER)
        else:
            await c.answer("❌ Заказ не найден", show_alert=True)


async def on_message_girl(c: CallbackQuery, button: Button, manager: DialogManager):
    """Написать девушке"""
    order_id = manager.dialog_data.get("selected_order_id")
    if not order_id:
        await c.answer("❌ Заказ не выбран", show_alert=True)
        return
    
    async with async_session_maker() as session:
        order = await OrderRepository.get_by_id(session, order_id)
        if order and order.payment_status == "paid":
            # TODO: Добавить telegram_id девушки в модель Profile
            await c.answer("⚠️ Функция будет доступна после добавления telegram_id девушки в профиль", show_alert=True)
        else:
            await c.answer("❌ Заказ должен быть оплачен", show_alert=True)


async def on_payment_status_select(c: CallbackQuery, button: Button, manager: DialogManager):
    """Выбор статуса оплаты"""
    status = button.widget_id
    order_id = manager.dialog_data.get("selected_order_id")
    
    if not order_id:
        await c.answer("❌ Заказ не выбран", show_alert=True)
        return
    
    async with async_session_maker() as session:
        order = await OrderRepository.get_by_id(session, order_id)
        if not order:
            await c.answer("❌ Заказ не найден", show_alert=True)
            return
        
        # Обновляем статус
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one()
        order.payment_status = status
        await session.commit()
        
        await c.answer(f"✅ Статус изменен на: {status}")
        await manager.switch_to(states.AdminOrders.DETAIL)


async def on_conference_link_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода ссылки на конференцию"""
    order_id = manager.dialog_data.get("selected_order_id")
    if not order_id:
        await message.answer("❌ Заказ не выбран")
        return
    
    async with async_session_maker() as session:
        from bot.database.models import Order as OrderModel
        from sqlalchemy import select
        
        result = await session.execute(
            select(OrderModel).where(OrderModel.id == order_id)
        )
        order = result.scalar_one()
        order.conference_link = text.strip()
        await session.commit()
        
        await message.answer("✅ Ссылка на конференцию добавлена")
        await manager.switch_to(states.AdminOrders.DETAIL)


async def on_cancel_confirm(c: CallbackQuery, button: Button, manager: DialogManager):
    """Подтверждение отмены заказа"""
    order_id = manager.dialog_data.get("selected_order_id")
    if not order_id:
        await c.answer("❌ Заказ не выбран", show_alert=True)
        return
    
    async with async_session_maker() as session:
        order = await OrderRepository.get_by_id(session, order_id)
        if not order:
            await c.answer("❌ Заказ не найден", show_alert=True)
            return
        
        payment_status = order.payment_status
        
        if payment_status == "processing":
            await c.answer("❌ Невозможно отменить заказ со статусом 'В обработке'. Сначала измените статус оплаты.", show_alert=True)
            return
        
        # Удаляем заказ
        result = await session.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one()
        
        # Отправляем уведомление пользователю
        from aiogram import Bot
        from bot.config import BOT_TOKEN
        bot = Bot(token=BOT_TOKEN)
        await send_order_cancellation_to_user(bot, order, payment_status)
        
        # Удаляем заказ
        await session.delete(order)
        await session.commit()
        
        await c.answer("✅ Заказ отменен")
        await manager.switch_to(states.AdminOrders.LIST)


async def on_user_message_sent(message: Message, widget: MessageInput, manager: DialogManager):
    """Отправка сообщения пользователю"""
    user_id = manager.dialog_data.get("message_user_id")
    order_id = manager.dialog_data.get("message_order_id")
    
    if not user_id:
        await message.answer("❌ Пользователь не найден")
        return
    
    async with async_session_maker() as session:
        order = await OrderRepository.get_by_id(session, order_id)
        if not order:
            await message.answer("❌ Заказ не найден")
            return
        
        # Формируем сообщение
        text = (
            f"Спасибо! Ваш заказ {order.order_number} оформлен.\n\n"
            f"Сумма: {order.total_price:.0f} рублей\n\n"
            f"Мы приступаем к обработке заказа. В течение пары минут Вы получите ссылку на оплату.\n\n"
            f"Если есть вопросы напишите в ответ на это сообщение!"
        )
        
        # Отправляем сообщение пользователю
        from aiogram import Bot
        from bot.config import BOT_TOKEN
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=user_id, text=text)
        
        await message.answer("✅ Сообщение отправлено пользователю")
        await manager.switch_to(states.AdminOrders.DETAIL)


async def get_change_datetime_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна изменения даты и времени"""
    return {}


async def get_change_payment_status_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна изменения статуса оплаты"""
    return {}


async def get_add_conference_link_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна добавления ссылки на конференцию"""
    return {}


async def get_message_user_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна отправки сообщения пользователю"""
    return {}


orders_dialog = Dialog(
    Window(
        Format("📋 <b>Управление заказами</b>\n\n{orders_text}"),
        Group(
            ScrollingGroup(
                ListGroup(
                    Button(
                        Format("{item.order_number} - {item.total_price:.0f}₽ - {item.payment_status}"),
                        id="order_btn",
                        on_click=on_order_select,
                    ),
                    id="orders_list",
                    item_id_getter=lambda item: str(item.id),
                    items="orders",
                ),
                id="orders_scroll",
                width=1,
                height=10,
            ),
            when="has_orders",
        ),
        Cancel(Const("🔙 Назад")),
        getter=get_orders_data,
        state=states.AdminOrders.MAIN,
    ),
    
    Window(
        Format(
            "📄 <b>Заказ {order_number}</b>\n\n"
            "👤 Пользователь: {user_username}\n"
            "🆔 ID: {user_id}\n"
            "🎀 Модель: {profile_name}\n"
            "{format_emoji} Формат: {format_name}\n"
            "🎮 Игра: {game_name}\n"
            "📅 Дата: {date}\n"
            "⏰ Время: {time}\n"
            "⏱️ Продолжительность: {duration}\n"
            "👥 Участников: {participants}\n"
            "💰 Сумма: {total_price}\n"
            "💳 Статус оплаты: {payment_status}\n"
            "🔗 Ссылка на конференцию: {conference_link}\n"
            "📅 Создан: {created_at}\n"
        ),
        Column(
            SwitchTo(
                Const("📅 Изменить дату и время"),
                id="change_datetime",
                state=states.AdminOrders.CHANGE_DATETIME,
            ),
            SwitchTo(
                Const("💳 Изменить статус оплаты"),
                id="change_payment",
                state=states.AdminOrders.CHANGE_PAYMENT_STATUS,
            ),
            SwitchTo(
                Const("🔗 Добавить ссылку на конференцию"),
                id="add_link",
                state=states.AdminOrders.ADD_CONFERENCE_LINK,
            ),
            SwitchTo(
                Const("✉️ Написать пользователю"),
                id="message_user",
                state=states.AdminOrders.MESSAGE_USER,
            ),
            SwitchTo(
                Const("👤 Написать девушке"),
                id="message_girl",
                state=states.AdminOrders.MESSAGE_GIRL,
            ),
            SwitchTo(
                Const("❌ Отменить заказ"),
                id="cancel",
                state=states.AdminOrders.CANCEL,
            ),
            Back(Const("🔙 Назад")),
        ),
        getter=get_order_detail_data,
        state=states.AdminOrders.DETAIL,
    ),
    
    Window(
        Const("📅 <b>Изменить дату и время</b>\n\nФункция в разработке"),
        Back(Const("🔙 Назад")),
        getter=get_change_datetime_data,
        state=states.AdminOrders.CHANGE_DATETIME,
    ),
    
    Window(
        Const("💳 <b>Изменить статус оплаты</b>\n\nВыберите новый статус:"),
        Column(
            Button(
                Const("❌ Не оплачено"),
                id="not_paid",
                on_click=on_payment_status_select,
            ),
            Button(
                Const("⏳ В обработке"),
                id="processing",
                on_click=on_payment_status_select,
            ),
            Button(
                Const("✅ Оплачено"),
                id="paid",
                on_click=on_payment_status_select,
            ),
            Back(Const("🔙 Назад")),
        ),
        getter=get_change_payment_status_data,
        state=states.AdminOrders.CHANGE_PAYMENT_STATUS,
    ),
    
    Window(
        Const("🔗 <b>Добавить ссылку на конференцию</b>\n\nВведите ссылку:"),
        TextInput(
            id="conference_link",
            on_success=on_conference_link_input,
        ),
        Back(Const("🔙 Назад")),
        getter=get_add_conference_link_data,
        state=states.AdminOrders.ADD_CONFERENCE_LINK,
    ),
    
    Window(
        Format("❓ <b>Подтверждение отмены</b>\n\nВы уверены, что хотите отменить заказ {order_number}?"),
        Row(
            Button(
                Const("✅ Да, отменить"),
                id="confirm_cancel",
                on_click=on_cancel_confirm,
            ),
            Button(
                Const("❌ Отмена"),
                id="cancel_cancel",
                on_click=lambda c, b, m: m.switch_to(states.AdminOrders.DETAIL),
            ),
        ),
        getter=get_order_detail_data,
        state=states.AdminOrders.CANCEL,
    ),
    
    Window(
        Const("✉️ <b>Написать пользователю</b>\n\nОтправьте сообщение:"),
        MessageInput(
            func=on_user_message_sent,
        ),
        Back(Const("🔙 Назад")),
        getter=get_message_user_data,
        state=states.AdminOrders.MESSAGE_USER,
    ),
)

