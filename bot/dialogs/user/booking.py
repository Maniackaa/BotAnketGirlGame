"""Диалог бронирования встречи"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
import dateparser
import pytz
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Column, Row, ListGroup, Group
from aiogram_dialog.widgets.input import TextInput
from aiogram.types import CallbackQuery, Message

from bot.dialogs.user.states import UserBooking
from bot.database.database import async_session_maker
from bot.database.repositories import (
    ProfileRepository, GameRepository, OrderRepository, UserRepository
)
from bot.services.payment import calculate_order_price, format_price_calculation
from bot.services.notifications import send_new_order_notification
from bot.config import TIMEZONE
from aiogram import Bot

logger = logging.getLogger(__name__)

# Часовой пояс
tz = pytz.timezone(TIMEZONE)


async def on_booking_start(start_data, dialog_manager: DialogManager):
    """Обработчик запуска диалога - сохраняем данные из start_data в dialog_data"""
    if start_data:
        logger.info(f"[on_booking_start] Получены данные из start_data: {start_data}")
        if isinstance(start_data, dict):
            dialog_manager.dialog_data.update(start_data)
            logger.info(f"[on_booking_start] Данные сохранены в dialog_data: {dict(dialog_manager.dialog_data)}")
        else:
            logger.warning(f"[on_booking_start] start_data не является словарем: {type(start_data)}")
    else:
        logger.warning(f"[on_booking_start] start_data пуст или None")


async def get_confirm_format_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для подтверждения формата"""
    # В aiogram-dialog данные из data при start() автоматически попадают в dialog_data
    profile_id = dialog_manager.dialog_data.get("selected_profile_id")
    format_type = dialog_manager.dialog_data.get("format_type", "audio")
    
    logger.info(f"[get_confirm_format_data] Начало. profile_id = {profile_id}, format_type = {format_type}")
    logger.info(f"[get_confirm_format_data] dialog_data keys = {list(dialog_manager.dialog_data.keys())}")
    logger.info(f"[get_confirm_format_data] dialog_data = {dict(dialog_manager.dialog_data)}")
    
    # Если данных нет, это критическая ошибка - данные должны были быть переданы
    if not profile_id:
        logger.error(f"[get_confirm_format_data] КРИТИЧЕСКАЯ ОШИБКА: profile_id не найден в dialog_data!")
        logger.error(f"[get_confirm_format_data] dialog_data полностью: {dict(dialog_manager.dialog_data)}")
        return {
            "format_emoji": "🎧",
            "format_name": "Аудио-чат",
            "price": "0 ₽/час",
            "description": "Ошибка: данные анкеты не найдены. Пожалуйста, попробуйте выбрать формат еще раз.",
        }
    
    if not profile_id:
        logger.warning(f"[get_confirm_format_data] profile_id не найден в dialog_data")
        return {
            "format_emoji": "🎧",
            "format_name": "Аудио-чат",
            "price": "0 ₽/час",
            "description": "",
        }
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            logger.error(f"[get_confirm_format_data] Профиль с id {profile_id} не найден в БД")
            return {
                "format_emoji": "🎧",
                "format_name": "Аудио-чат",
                "price": "0 ₽/час",
                "description": "",
            }
        
        logger.info(f"[get_confirm_format_data] Профиль найден: {profile.name}, audio_price = {profile.audio_chat_price}, video_price = {profile.video_chat_price}")
        
        if format_type == "audio":
            format_emoji = "🎧"
            format_name = "Аудио-чат"
            price = f"{profile.audio_chat_price:.0f} ₽/час"
            description = "В аудио-чате вы сможете поговорить в реальном времени, поиграть вместе и просто классно провести время."
        elif format_type == "video":
            format_emoji = "🎥"
            format_name = "Видео-чат"
            price = f"{profile.video_chat_price:.0f} ₽/час"
            description = "В видео-чате вы сможете видеть друг друга, поговорить в реальном времени, поиграть вместе и просто классно провести время."
        else:  # private
            format_emoji = "💎"
            format_name = "Приватка"
            price = f"{profile.private_price:.0f} ₽" if profile.private_price else "0 ₽"
            description = "Приватка - это особый формат общения с расширенными возможностями."
        
        logger.info(f"[get_confirm_format_data] Возвращаем: format_name = {format_name}, price = {price}")
        
        return {
            "format_emoji": format_emoji,
            "format_name": format_name,
            "price": price,
            "description": description,
        }


async def on_confirm_format_yes(c: CallbackQuery, button: Button, manager: DialogManager):
    """Подтверждение формата - переход к выбору игры"""
    logger.info(f"[on_confirm_format_yes] Пользователь {c.from_user.id} подтвердил формат")
    await manager.switch_to(UserBooking.SELECT_GAME)


async def get_select_game_data(dialog_manager: DialogManager, **kwargs):
    """Получение списка игр для выбора"""
    profile_id = dialog_manager.dialog_data.get("selected_profile_id")
    format_type = dialog_manager.dialog_data.get("format_type", "audio")
    
    format_names = {
        "audio": "Аудио-чат",
        "video": "Видео-чат",
        "private": "Приватка",
    }
    format_name = format_names.get(format_type, "Аудио-чат")
    
    if not profile_id:
        return {
            "games": [],
            "has_games": False,
            "format_name": format_name,
        }
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            return {
                "games": [],
                "has_games": False,
                "format_name": format_name,
            }
        
        games = [pg.game for pg in profile.games if pg.game]
        
        return {
            "games": games,
            "has_games": len(games) > 0,
            "format_name": format_name,
        }


async def on_game_select(c: CallbackQuery, button: Button, manager: DialogManager):
    """Выбор игры"""
    item_id = getattr(manager, 'item_id', None)
    
    if item_id is None:
        if c.data:
            parts = c.data.split(":")
            if len(parts) >= 3:
                item_id = parts[-1]
            else:
                item_id = parts[-1] if parts else None
    
    if not item_id:
        await c.answer("❌ Ошибка: не удалось получить ID игры", show_alert=True)
        return
    
    try:
        game_id = int(item_id)
    except ValueError:
        await c.answer("❌ Ошибка: неверный формат ID игры", show_alert=True)
        return
    
    manager.dialog_data["selected_game_id"] = game_id
    logger.info(f"[on_game_select] Выбрана игра {game_id}")
    await manager.switch_to(UserBooking.INPUT_DATE)


async def get_input_date_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для ввода даты"""
    return {}


async def on_date_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода даты"""
    text = text.strip()
    
    # Парсим дату с помощью dateparser
    parsed_date = dateparser.parse(text, languages=['ru', 'en'], settings={
        'TIMEZONE': TIMEZONE,
        'RELATIVE_BASE': datetime.now(tz),
    })
    
    if not parsed_date:
        await message.answer("❌ Не удалось распознать дату. Попробуйте еще раз (например: 14 июня, 26.11.2025)")
        return
    
    # Убеждаемся, что дата в будущем
    now = datetime.now(tz)
    if parsed_date.replace(tzinfo=tz) < now:
        await message.answer("❌ Дата должна быть в будущем. Попробуйте еще раз")
        return
    
    # Сохраняем только дату (без времени)
    manager.dialog_data["order_date"] = parsed_date.date().isoformat()
    logger.info(f"[on_date_input] Дата установлена: {parsed_date.date()}")
    await manager.switch_to(UserBooking.INPUT_TIME)


async def get_input_time_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для ввода времени"""
    return {}


async def on_time_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода времени"""
    text = text.strip()
    
    # Парсим время (формат HH:MM)
    try:
        time_parts = text.split(":")
        if len(time_parts) != 2:
            raise ValueError
        
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        
        if not (0 <= hours < 24 and 0 <= minutes < 60):
            raise ValueError
        
        # Объединяем дату и время
        order_date_str = manager.dialog_data.get("order_date")
        if not order_date_str:
            await message.answer("❌ Ошибка: дата не установлена")
            return
        
        from datetime import date
        order_date = date.fromisoformat(order_date_str)
        order_datetime = tz.localize(datetime.combine(order_date, datetime.min.time().replace(hour=hours, minute=minutes)))
        
        # Проверяем, что дата и время в будущем
        now = datetime.now(tz)
        if order_datetime < now:
            await message.answer("❌ Время должно быть в будущем. Попробуйте еще раз")
            return
        
        manager.dialog_data["order_datetime"] = order_datetime.isoformat()
        logger.info(f"[on_time_input] Время установлено: {order_datetime}")
        await manager.switch_to(UserBooking.INPUT_DURATION)
        
    except (ValueError, IndexError):
        await message.answer("❌ Неверный формат времени. Используйте формат ЧЧ:ММ (например: 19:00)")


async def get_input_duration_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для ввода продолжительности"""
    format_type = dialog_manager.dialog_data.get("format_type", "audio")
    
    if format_type == "private":
        # Для приватки продолжительность не нужна, пропускаем этот шаг
        dialog_manager.dialog_data["duration_hours"] = 1.0
        # Переключаемся на ввод участников
        await dialog_manager.switch_to(UserBooking.INPUT_PARTICIPANTS)
        return {}
    
    return {}


async def on_duration_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода продолжительности"""
    try:
        duration = float(text.strip())
        if duration < 1:
            await message.answer("❌ Продолжительность должна быть не менее 1 часа")
            return
        manager.dialog_data["duration_hours"] = duration
        logger.info(f"[on_duration_input] Продолжительность установлена: {duration} часов")
        await manager.switch_to(UserBooking.INPUT_PARTICIPANTS)
    except ValueError:
        await message.answer("❌ Введите число (например: 2)")


async def get_input_participants_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для ввода количества участников"""
    return {}


async def on_participants_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода количества участников"""
    try:
        participants = int(text.strip())
        if participants < 1:
            await message.answer("❌ Количество участников должно быть не менее 1")
            return
        manager.dialog_data["participants_count"] = participants
        logger.info(f"[on_participants_input] Количество участников установлено: {participants}")
        await manager.switch_to(UserBooking.CONFIRM_ORDER)
    except ValueError:
        await message.answer("❌ Введите число (например: 5)")


async def get_confirm_order_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для подтверждения заказа"""
    profile_id = dialog_manager.dialog_data.get("selected_profile_id")
    format_type = dialog_manager.dialog_data.get("format_type", "audio")
    game_id = dialog_manager.dialog_data.get("selected_game_id")
    order_datetime_str = dialog_manager.dialog_data.get("order_datetime")
    duration_hours = dialog_manager.dialog_data.get("duration_hours", 1.0)
    participants_count = dialog_manager.dialog_data.get("participants_count", 1)
    
    if not profile_id or not order_datetime_str:
        return {
            "format_emoji": "🎧",
            "format_name": "Аудио-чат",
            "game_name": "Не указана",
            "date": "Не указана",
            "time": "Не указано",
            "duration": "0 ч.",
            "participants": 0,
            "calculation_text": "",
        }
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            return {
                "format_emoji": "🎧",
                "format_name": "Аудио-чат",
                "game_name": "Не указана",
                "date": "Не указана",
                "time": "Не указано",
                "duration": "0 ч.",
                "participants": 0,
                "calculation_text": "",
            }
        
        # Получаем игру
        game_name = "Не указана"
        if game_id:
            game = await GameRepository.get_by_id(session, game_id)
            if game:
                game_name = game.name
        
        # Парсим дату и время
        order_datetime = datetime.fromisoformat(order_datetime_str)
        date_str = order_datetime.strftime("%d.%m.%Y")
        time_str = order_datetime.strftime("%H:%M")
        
        # Определяем формат и цену
        if format_type == "audio":
            format_emoji = "🎧"
            format_name = "Аудио-чат"
            price_per_hour = profile.audio_chat_price
        elif format_type == "video":
            format_emoji = "🎥"
            format_name = "Видео-чат"
            price_per_hour = profile.video_chat_price
        else:  # private
            format_emoji = "💎"
            format_name = "Приватка"
            # Для приватки цена фиксированная, не по часам
            price_per_hour = profile.private_price or 0
            duration_hours = 1.0  # Для расчета используем 1 час
        
        # Рассчитываем стоимость
        if format_type == "private":
            # Для приватки просто фиксированная цена
            calculation = {
                "base_price": price_per_hour,
                "additional_participants_price": 0,
                "total_price": price_per_hour,
            }
            calculation_text = f"💰 Стоимость: {price_per_hour:.0f}₽"
        else:
            calculation = calculate_order_price(price_per_hour, duration_hours, participants_count)
            calculation_text = format_price_calculation(price_per_hour, duration_hours, participants_count, calculation)
        
        # Сохраняем расчет в dialog_data для создания заказа
        dialog_manager.dialog_data["calculation"] = calculation
        dialog_manager.dialog_data["price_per_hour"] = price_per_hour
        
        # Формируем краткое сообщение для подтверждения (БЕЗ "✅ Заказ оформлен!")
        if format_type == "private":
            order_preview = (
                f"{format_emoji} Формат: {format_name}\n"
                f"🎮 Игра: {game_name}\n"
                f"📅 Дата: {date_str}\n"
                f"⏰ Время: {time_str}\n"
                f"👥 Участников: {participants_count}\n\n"
                f"{calculation_text}"
            )
        else:
            order_preview = (
                f"{format_emoji} Формат: {format_name}\n"
                f"🎮 Игра: {game_name}\n"
                f"📅 Дата: {date_str}\n"
                f"⏰ Время: {time_str}\n"
                f"⏱️ Продолжительность: {duration_hours:.0f} ч.\n"
                f"👥 Участников: {participants_count}\n\n"
                f"{calculation_text}"
            )
        
        # Сохраняем полное итоговое сообщение для отправки после подтверждения
        if format_type == "private":
            order_summary = (
                f"✅ Заказ оформлен!\n"
                f"{format_emoji} Формат: {format_name}\n"
                f"🎮 Игра: {game_name}\n"
                f"📅 Дата: {date_str}\n"
                f"⏰ Время: {time_str}\n"
                f"👥 Участников: {participants_count}\n\n"
                f"{calculation_text}\n\n"
                f"Пожалуйста, подождите с Вами свяжется администратор для завершения заказа."
            )
        else:
            order_summary = (
                f"✅ Заказ оформлен!\n"
                f"{format_emoji} Формат: {format_name}\n"
                f"🎮 Игра: {game_name}\n"
                f"📅 Дата: {date_str}\n"
                f"⏰ Время: {time_str}\n"
                f"⏱️ Продолжительность: {duration_hours:.0f} ч.\n"
                f"👥 Участников: {participants_count}\n\n"
                f"{calculation_text}\n\n"
                f"Пожалуйста, подождите с Вами свяжется администратор для завершения заказа."
            )
        
        dialog_manager.dialog_data["order_summary"] = order_summary
        
        return {
            "format_emoji": format_emoji,
            "format_name": format_name,
            "game_name": game_name,
            "date": date_str,
            "time": time_str,
            "duration": f"{duration_hours:.0f} ч.",
            "participants": participants_count,
            "calculation_text": calculation_text,
            "order_preview": order_preview,
        }


async def on_confirm_order_cancel(c: CallbackQuery, button: Button, manager: DialogManager):
    """Отмена заказа"""
    logger.info(f"[on_confirm_order_cancel] Пользователь {c.from_user.id} отменил заказ")
    await c.answer("❌ Заказ отменен")
    await manager.done()


async def on_confirm_order_yes(c: CallbackQuery, button: Button, manager: DialogManager):
    """Создание заказа"""
    logger.info(f"[on_confirm_order_yes] Пользователь {c.from_user.id} подтверждает заказ")
    
    profile_id = manager.dialog_data.get("selected_profile_id")
    format_type = manager.dialog_data.get("format_type", "audio")
    game_id = manager.dialog_data.get("selected_game_id")
    order_datetime_str = manager.dialog_data.get("order_datetime")
    duration_hours = manager.dialog_data.get("duration_hours", 1.0)
    participants_count = manager.dialog_data.get("participants_count", 1)
    calculation = manager.dialog_data.get("calculation", {})
    order_summary = manager.dialog_data.get("order_summary", "")
    
    if not profile_id or not order_datetime_str:
        await c.answer("❌ Ошибка: не все данные заполнены", show_alert=True)
        return
    
    # Получаем бота из события
    bot: Bot = manager.event.bot
    
    async with async_session_maker() as session:
        # Получаем или создаем пользователя
        user = await UserRepository.get_or_create(
            session,
            telegram_id=c.from_user.id,
            username=c.from_user.username,
            first_name=c.from_user.first_name
        )
        
        # Получаем профиль
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            await c.answer("❌ Анкета не найдена", show_alert=True)
            return
        
        # Получаем игру
        game = None
        game_name = None
        if game_id:
            game = await GameRepository.get_by_id(session, game_id)
            if game:
                game_name = game.name
        
        # Парсим дату и время
        order_datetime = datetime.fromisoformat(order_datetime_str)
        if order_datetime.tzinfo is None:
            order_datetime = tz.localize(order_datetime)
        
        # Создаем заказ
        order_data = {
            "user_id": user.id,
            "profile_id": profile_id,
            "format_type": format_type,
            "game_id": game_id,
            "game_name": game_name,
            "date": order_datetime,
            "duration_hours": duration_hours,
            "participants_count": participants_count,
            "base_price": calculation.get("base_price", 0),
            "additional_participants_price": calculation.get("additional_participants_price", 0),
            "total_price": calculation.get("total_price", 0),
        }
        
        order = await OrderRepository.create(session, order_data)
        logger.info(f"[on_confirm_order_yes] Заказ создан: {order.order_number}")
        
        # Отправляем уведомление админу
        try:
            await send_new_order_notification(bot, order, user, profile, game)
            logger.info(f"[on_confirm_order_yes] Уведомление админу отправлено")
        except Exception as e:
            logger.error(f"[on_confirm_order_yes] Ошибка при отправке уведомления админу: {e}")
        
        # Сохраняем итоговое сообщение перед закрытием диалога
        order_summary = manager.dialog_data.get("order_summary", "")
        
        await c.answer("✅ Заказ создан!")
        
        # Закрываем диалог
        await manager.done()
        
        # Отправляем итоговое сообщение пользователю
        if order_summary:
            try:
                await bot.send_message(
                    chat_id=c.from_user.id,
                    text=order_summary
                )
                logger.info(f"[on_confirm_order_yes] Итоговое сообщение отправлено пользователю {c.from_user.id}")
            except Exception as e:
                logger.error(f"[on_confirm_order_yes] Ошибка при отправке итогового сообщения: {e}")


booking_dialog = Dialog(
    Window(
        Format(
            "Отличный выбор 😊\n"
            "{description}\n"
            "Стоимость: {price}\n"
            "Длительность: от 1 часа\n\n"
            "Готов забронировать? ⬇️"
        ),
        Column(
            Button(
                Const("Да"),
                id="confirm_yes",
                on_click=on_confirm_format_yes,
            ),
            Button(
                Const("Назад"),
                id="back",
                on_click=lambda c, b, m: m.done(),
            ),
        ),
        getter=get_confirm_format_data,
        state=UserBooking.CONFIRM_FORMAT,
    ),
    
    Window(
        Format("🎮 Заказ {format_name}\n\nВыберите игры:"),
        Group(
            ListGroup(
                Button(
                    Format("{item.name}"),
                    id="game_btn",
                    on_click=on_game_select,
                ),
                id="games_list",
                item_id_getter=lambda item: str(item.id),
                items="games",
            ),
            when="has_games",
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(UserBooking.CONFIRM_FORMAT),
        ),
        getter=get_select_game_data,
        state=UserBooking.SELECT_GAME,
    ),
    
    Window(
        Const("📅 Укажите дату проведения (пример: 14 июня):"),
        TextInput(
            id="date_input",
            on_success=on_date_input,
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(UserBooking.SELECT_GAME),
        ),
        getter=get_input_date_data,
        state=UserBooking.INPUT_DATE,
    ),
    
    Window(
        Const("⏰ Укажите точное время по МСК (пример: 19:00):"),
        TextInput(
            id="time_input",
            on_success=on_time_input,
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(UserBooking.INPUT_DATE),
        ),
        getter=get_input_time_data,
        state=UserBooking.INPUT_TIME,
    ),
    
    Window(
        Const("⏱️ Укажите количество часов (введите число):"),
        TextInput(
            id="duration_input",
            on_success=on_duration_input,
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(UserBooking.INPUT_TIME),
        ),
        getter=get_input_duration_data,
        state=UserBooking.INPUT_DURATION,
    ),
    
    Window(
        Const("👥 Укажите количество участников (введите число):"),
        TextInput(
            id="participants_input",
            on_success=on_participants_input,
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(UserBooking.INPUT_DURATION),
        ),
        getter=get_input_participants_data,
        state=UserBooking.INPUT_PARTICIPANTS,
    ),
    
    Window(
        Format("Проверьте данные заказа:\n\n{order_preview}\n\nПодтвердить заказ?"),
        Column(
            Button(
                Const("✅ Подтвердить"),
                id="confirm",
                on_click=on_confirm_order_yes,
            ),
            Button(
                Const("❌ Отменить"),
                id="cancel",
                on_click=on_confirm_order_cancel,
            ),
        ),
        getter=get_confirm_order_data,
        state=UserBooking.CONFIRM_ORDER,
    ),
    on_start=on_booking_start,
)

