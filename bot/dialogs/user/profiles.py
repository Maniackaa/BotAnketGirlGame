"""Диалог просмотра анкет для пользователя"""
import logging
from typing import List, Optional
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Row, Column
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram.enums import ContentType
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram.types import CallbackQuery

from bot.dialogs.user.states import UserProfiles
from bot.database.database import async_session_maker
from bot.database.repositories import ProfileRepository

logger = logging.getLogger(__name__)


async def get_profiles_list_data(dialog_manager: DialogManager, **kwargs):
    """Получение списка анкет"""
    async with async_session_maker() as session:
        profiles = await ProfileRepository.get_all(session)
        logger.info(f"[get_profiles_list_data] Найдено анкет: {len(profiles)}")
        
        # Сохраняем список ID анкет в dialog_data
        if profiles:
            profile_ids = [p.id for p in profiles]
            dialog_manager.dialog_data["profile_ids"] = profile_ids
            dialog_manager.dialog_data["current_profile_index"] = 0
            logger.info(f"[get_profiles_list_data] Сохранены ID анкет: {profile_ids}")
        
        return {
            "total_profiles": len(profiles),
            "has_profiles": len(profiles) > 0,
        }


async def on_start_viewing(c: CallbackQuery, button: Button, manager: DialogManager):
    """Начало просмотра анкет"""
    logger.info(f"[on_start_viewing] Пользователь {c.from_user.id} начинает просмотр")
    
    async with async_session_maker() as session:
        profiles = await ProfileRepository.get_all(session)
        if not profiles:
            await c.answer("❌ Анкеты не найдены", show_alert=True)
            return
        
        # Сохраняем список ID и начинаем с первой анкеты
        profile_ids = [p.id for p in profiles]
        manager.dialog_data["profile_ids"] = profile_ids
        manager.dialog_data["current_profile_index"] = 0
        manager.dialog_data["photo_index"] = 0
        
        logger.info(f"[on_start_viewing] Начинаем просмотр с анкеты {profile_ids[0]}")
        await manager.switch_to(UserProfiles.VIEW)


async def get_profile_view_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для просмотра анкеты"""
    profile_ids = dialog_manager.dialog_data.get("profile_ids", [])
    current_index = dialog_manager.dialog_data.get("current_profile_index", 0)
    photo_index = dialog_manager.dialog_data.get("photo_index", 0)
    
    logger.info(f"[get_profile_view_data] current_index = {current_index}, photo_index = {photo_index}, profile_ids = {profile_ids}")
    
    if not profile_ids or current_index >= len(profile_ids):
        logger.warning(f"[get_profile_view_data] Нет анкет для отображения")
        return {
            "profile_name": "Анкета не найдена",
            "profile_age": "",
            "profile_description": "",
            "games_list": "",
            "audio_price": "",
            "video_price": "",
            "private_price": "",
            "channel_link": "",
            "photo_file_id": None,
            "photo_media": None,
            "caption": "Анкеты не найдены",
            "has_prev_profile": False,
            "has_next_profile": False,
            "has_prev_photo": False,
            "has_next_photo": False,
            "photo_number": 0,
            "total_photos": 0,
            "profile_number": 0,
            "total_profiles": 0,
        }
    
    profile_id = profile_ids[current_index]
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            logger.error(f"[get_profile_view_data] Анкета с id {profile_id} не найдена")
            return {
                "profile_name": "Анкета не найдена",
                "profile_age": "",
                "profile_description": "",
                "games_list": "",
                "audio_price": "",
                "video_price": "",
                "private_price": "",
                "channel_link": "",
                "photo_file_id": None,
                "photo_media": None,
                "caption": "Анкета не найдена",
                "has_prev_profile": False,
                "has_next_profile": False,
                "has_prev_photo": False,
                "has_next_photo": False,
                "photo_number": 0,
                "total_photos": 0,
                "profile_number": 0,
                "total_profiles": 0,
            }
        
        # Формируем список игр
        games_names = [pg.game.name for pg in profile.games if pg.game]
        games_text = ", ".join(games_names) if games_names else "Нет игр"
        
        # Получаем фотографии
        photo_ids = profile.photo_ids or []
        total_photos = len(photo_ids)
        
        # Определяем текущую фотографию
        if total_photos > 0:
            current_photo_index = min(photo_index, total_photos - 1)
            current_photo_id = photo_ids[current_photo_index]
            
            # Создаем MediaAttachment для DynamicMedia виджета
            photo_media = MediaAttachment(
                ContentType.PHOTO,
                file_id=MediaId(current_photo_id),
            )
            
            caption = (
                f"👤 <b>{profile.name}</b>"
                + (f", {profile.age} лет" if profile.age else "")
                + f"\n\n📝 {profile.description or 'Нет описания'}\n\n"
                + f"🎮 <b>Игры:</b> {games_text}\n\n"
                + f"💰 <b>Тарифы:</b>\n"
                + f"🎧 Аудио-чат: {profile.audio_chat_price:.0f}₽/час\n"
                + f"🎥 Видео-чат: {profile.video_chat_price:.0f}₽/час"
                + (f"\n💎 Приватка: {profile.private_price:.0f}₽" if profile.private_price else "")
                + (f"\n\n📱 Канал: {profile.channel_link}" if profile.channel_link else "")
                + f"\n\n📷 Фото {current_photo_index + 1} из {total_photos}"
            )
        else:
            current_photo_id = None
            photo_media = None
            caption = (
                f"👤 <b>{profile.name}</b>"
                + (f", {profile.age} лет" if profile.age else "")
                + f"\n\n📝 {profile.description or 'Нет описания'}\n\n"
                + f"🎮 <b>Игры:</b> {games_text}\n\n"
                + f"💰 <b>Тарифы:</b>\n"
                + f"🎧 Аудио-чат: {profile.audio_chat_price:.0f}₽/час\n"
                + f"🎥 Видео-чат: {profile.video_chat_price:.0f}₽/час"
                + (f"\n💎 Приватка: {profile.private_price:.0f}₽" if profile.private_price else "")
                + (f"\n\n📱 Канал: {profile.channel_link}" if profile.channel_link else "")
                + "\n\n❌ Нет фотографий"
            )
        
        return {
            "profile_name": profile.name or "Не указано",
            "profile_age": f"{profile.age} лет" if profile.age else "Не указано",
            "profile_description": profile.description or "Нет описания",
            "games_list": games_text,
            "audio_price": f"{profile.audio_chat_price:.0f}₽/час",
            "video_price": f"{profile.video_chat_price:.0f}₽/час",
            "private_price": f"{profile.private_price:.0f}₽" if profile.private_price else "Не указана",
            "channel_link": profile.channel_link or "Не указан",
            "photo_file_id": current_photo_id,
            "photo_media": photo_media,
            "caption": caption,
            "has_prev_profile": current_index > 0,
            "has_next_profile": current_index < len(profile_ids) - 1,
            "has_prev_photo": total_photos > 0 and photo_index > 0,
            "has_next_photo": total_photos > 0 and photo_index < total_photos - 1,
            "photo_number": photo_index + 1 if total_photos > 0 else 0,
            "total_photos": total_photos,
            "profile_number": current_index + 1,
            "total_profiles": len(profile_ids),
        }


async def on_prev_photo(c: CallbackQuery, button: Button, manager: DialogManager):
    """Переход к предыдущей фотографии"""
    photo_index = manager.dialog_data.get("photo_index", 0)
    if photo_index > 0:
        manager.dialog_data["photo_index"] = photo_index - 1
        logger.info(f"[on_prev_photo] Переход к фото {photo_index - 1}")
        await manager.show()
    else:
        logger.warning(f"[on_prev_photo] Уже на первой фотографии")


async def on_next_photo(c: CallbackQuery, button: Button, manager: DialogManager):
    """Переход к следующей фотографии"""
    profile_ids = manager.dialog_data.get("profile_ids", [])
    current_index = manager.dialog_data.get("current_profile_index", 0)
    
    if not profile_ids or current_index >= len(profile_ids):
        await c.answer("❌ Ошибка: анкета не найдена", show_alert=True)
        return
    
    profile_id = profile_ids[current_index]
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            await c.answer("❌ Анкета не найдена", show_alert=True)
            return
        
        photo_ids = profile.photo_ids or []
        photo_index = manager.dialog_data.get("photo_index", 0)
        
        if photo_index < len(photo_ids) - 1:
            manager.dialog_data["photo_index"] = photo_index + 1
            logger.info(f"[on_next_photo] Переход к фото {photo_index + 1}")
            await manager.show()
        else:
            logger.warning(f"[on_next_photo] Уже на последней фотографии")


async def on_prev_profile(c: CallbackQuery, button: Button, manager: DialogManager):
    """Переход к предыдущей анкете"""
    current_index = manager.dialog_data.get("current_profile_index", 0)
    if current_index > 0:
        manager.dialog_data["current_profile_index"] = current_index - 1
        manager.dialog_data["photo_index"] = 0  # Сбрасываем индекс фото
        logger.info(f"[on_prev_profile] Переход к анкете {current_index - 1}")
        await manager.show()
    else:
        logger.warning(f"[on_prev_profile] Уже на первой анкете")


async def on_next_profile(c: CallbackQuery, button: Button, manager: DialogManager):
    """Переход к следующей анкете"""
    profile_ids = manager.dialog_data.get("profile_ids", [])
    current_index = manager.dialog_data.get("current_profile_index", 0)
    
    if current_index < len(profile_ids) - 1:
        manager.dialog_data["current_profile_index"] = current_index + 1
        manager.dialog_data["photo_index"] = 0  # Сбрасываем индекс фото
        logger.info(f"[on_next_profile] Переход к анкете {current_index + 1}")
        await manager.show()
    else:
        logger.warning(f"[on_next_profile] Уже на последней анкете")


async def on_book_audio(c: CallbackQuery, button: Button, manager: DialogManager):
    """Бронирование аудио-чата"""
    profile_ids = manager.dialog_data.get("profile_ids", [])
    current_index = manager.dialog_data.get("current_profile_index", 0)
    
    if not profile_ids or current_index >= len(profile_ids):
        await c.answer("❌ Ошибка: анкета не найдена", show_alert=True)
        return
    
    profile_id = profile_ids[current_index]
    
    logger.info(f"[on_book_audio] Пользователь {c.from_user.id} выбрал аудио-чат для анкеты {profile_id}")
    logger.info(f"[on_book_audio] Сохраняем данные в dialog_data перед запуском диалога")
    
    # Сохраняем данные в dialog_data перед запуском нового диалога
    manager.dialog_data["selected_profile_id"] = profile_id
    manager.dialog_data["format_type"] = "audio"
    
    from bot.dialogs.user.states import UserBooking
    from aiogram_dialog import StartMode
    # Передаем данные через параметр data для надежности
    await manager.start(
        UserBooking.CONFIRM_FORMAT, 
        mode=StartMode.NORMAL,
        data={
            "selected_profile_id": profile_id,
            "format_type": "audio",
        }
    )


async def on_book_video(c: CallbackQuery, button: Button, manager: DialogManager):
    """Бронирование видео-чата"""
    profile_ids = manager.dialog_data.get("profile_ids", [])
    current_index = manager.dialog_data.get("current_profile_index", 0)
    
    if not profile_ids or current_index >= len(profile_ids):
        await c.answer("❌ Ошибка: анкета не найдена", show_alert=True)
        return
    
    profile_id = profile_ids[current_index]
    
    logger.info(f"[on_book_video] Пользователь {c.from_user.id} выбрал видео-чат для анкеты {profile_id}")
    logger.info(f"[on_book_video] Сохраняем данные в dialog_data перед запуском диалога")
    
    # Сохраняем данные в dialog_data перед запуском нового диалога
    manager.dialog_data["selected_profile_id"] = profile_id
    manager.dialog_data["format_type"] = "video"
    
    from bot.dialogs.user.states import UserBooking
    from aiogram_dialog import StartMode
    # Передаем данные через параметр data для надежности
    await manager.start(
        UserBooking.CONFIRM_FORMAT, 
        mode=StartMode.NORMAL,
        data={
            "selected_profile_id": profile_id,
            "format_type": "video",
        }
    )


async def on_book_private(c: CallbackQuery, button: Button, manager: DialogManager):
    """Бронирование приватки"""
    profile_ids = manager.dialog_data.get("profile_ids", [])
    current_index = manager.dialog_data.get("current_profile_index", 0)
    
    if not profile_ids or current_index >= len(profile_ids):
        await c.answer("❌ Ошибка: анкета не найдена", show_alert=True)
        return
    
    profile_id = profile_ids[current_index]
    
    logger.info(f"[on_book_private] Пользователь {c.from_user.id} выбрал приватку для анкеты {profile_id}")
    logger.info(f"[on_book_private] Сохраняем данные в dialog_data перед запуском диалога")
    
    # Сохраняем данные в dialog_data перед запуском нового диалога
    manager.dialog_data["selected_profile_id"] = profile_id
    manager.dialog_data["format_type"] = "private"
    
    from bot.dialogs.user.states import UserBooking
    from aiogram_dialog import StartMode
    # Передаем данные через параметр data для надежности
    await manager.start(
        UserBooking.CONFIRM_FORMAT, 
        mode=StartMode.NORMAL,
        data={
            "selected_profile_id": profile_id,
            "format_type": "private",
        }
    )


profiles_dialog = Dialog(
    Window(
        Format("📋 <b>Просмотр анкет</b>\n\nВсего анкет: {total_profiles}"),
        Column(
            Button(
                Const("🔍 Начать просмотр"),
                id="start_viewing",
                on_click=on_start_viewing,
                when="has_profiles",
            ),
            Button(
                Const("🔙 Назад"),
                id="back",
                on_click=lambda c, b, m: m.done(),
            ),
        ),
        getter=get_profiles_list_data,
        state=UserProfiles.LIST,
    ),
    
    Window(
        DynamicMedia(
            "photo_media",
            when=lambda data, widget, manager: data.get("photo_file_id") is not None,
        ),
        Format("{caption}"),
        Row(
            Button(
                Const("◀️ Пред. фото"),
                id="prev_photo",
                on_click=on_prev_photo,
                when="has_prev_photo",
            ),
            Button(
                Const("След. фото ▶️"),
                id="next_photo",
                on_click=on_next_photo,
                when="has_next_photo",
            ),
        ),
        Row(
            Button(
                Const("◀️ Пред. анкета"),
                id="prev_profile",
                on_click=on_prev_profile,
                when="has_prev_profile",
            ),
            Button(
                Const("След. анкета ▶️"),
                id="next_profile",
                on_click=on_next_profile,
                when="has_next_profile",
            ),
        ),
        Column(
            Button(
                Format("🎧 Аудио-Чат ({audio_price})"),
                id="book_audio",
                on_click=on_book_audio,
            ),
            Button(
                Format("🎥 Видео-Чат ({video_price})"),
                id="book_video",
                on_click=on_book_video,
            ),
            Button(
                Format("💎 Приватка ({private_price})"),
                id="book_private",
                on_click=on_book_private,
                when=lambda data, widget, manager: data.get("private_price") != "Не указана",
            ),
            Button(
                Const("🔙 Назад"),
                id="back",
                on_click=lambda c, b, m: m.switch_to(UserProfiles.LIST),
            ),
        ),
        getter=get_profile_view_data,
        state=UserProfiles.VIEW,
    ),
)

