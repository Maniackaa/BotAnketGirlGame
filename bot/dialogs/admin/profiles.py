"""Диалог управления анкетами"""
import logging
from typing import List, Optional
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import (
    Button, Row, Column, ScrollingGroup, SwitchTo, 
    Back, Cancel, Group, ListGroup
)
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram.types import Message, CallbackQuery
from aiogram_dialog.api.entities import ShowMode

from bot.dialogs.admin import states
from bot.database.database import async_session_maker
from bot.database.repositories import ProfileRepository, GameRepository
from bot.database.models import Profile, Game

logger = logging.getLogger(__name__)


class ProfileDisplay:
    """Класс-обертка для отображения профиля с форматированным именем"""
    def __init__(self, profile):
        self.id = profile.id
        self.age = profile.age  # Сохраняем возраст для использования в формате
        if profile.age:
            self.name = f"{profile.name} {profile.age} лет"
        else:
            self.name = profile.name
        self.profile = profile


class GameDisplay:
    """Класс-обертка для отображения игры с индикатором выбора"""
    def __init__(self, game, is_selected: bool):
        self.id = game.id
        self.name = game.name
        self.game = game
        self.is_selected = is_selected
        # Форматируем название с галочкой или крестиком
        if is_selected:
            self.display_name = f"✅ {game.name}"
        else:
            self.display_name = f"❌ {game.name}"


async def get_profiles_data(dialog_manager: DialogManager, **kwargs):
    """Получение списка анкет для отображения"""
    # Очищаем старые данные при открытии списка
    if "selected_profile_id" in dialog_manager.dialog_data:
        del dialog_manager.dialog_data["selected_profile_id"]
    
    async with async_session_maker() as session:
        profiles = await ProfileRepository.get_all(session)
        # Форматируем профили для отображения (добавляем возраст к имени)
        formatted_profiles = [ProfileDisplay(profile) for profile in profiles]
        return {
            "profiles": formatted_profiles,
        }


async def get_main_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для главного окна (пустой dict)"""
    # Очищаем старые данные при открытии главного окна
    if "selected_profile_id" in dialog_manager.dialog_data:
        del dialog_manager.dialog_data["selected_profile_id"]
    if "new_profile" in dialog_manager.dialog_data:
        del dialog_manager.dialog_data["new_profile"]
    if "selected_games" in dialog_manager.dialog_data:
        del dialog_manager.dialog_data["selected_games"]
    return {}


async def get_games_for_profile(dialog_manager: DialogManager, **kwargs):
    """Получение списка игр для добавления в анкету"""
    async with async_session_maker() as session:
        games = await GameRepository.get_all(session, limit=100, offset=0)
        selected_games = dialog_manager.dialog_data.get("selected_games", [])
        
        # Форматируем игры с индикаторами выбора
        formatted_games = []
        selected_games_names = []
        
        for game in games:
            is_selected = game.id in selected_games
            formatted_games.append(GameDisplay(game, is_selected))
            if is_selected:
                selected_games_names.append(game.name)
        
        # Формируем текст со списком выбранных игр
        if selected_games_names:
            selected_list = "\n".join([f"• {name}" for name in selected_games_names])
            selected_text = f"\n\n<b>Выбранные игры:</b>\n{selected_list}"
        else:
            selected_text = "\n\n<b>Выбранные игры:</b>\n(нет выбранных)"
        
        return {
            "games": formatted_games,
            "selected_games": selected_games,
            "selected_count": len(selected_games),
            "selected_text": selected_text,
        }


async def get_photo_count_data(dialog_manager: DialogManager, **kwargs):
    """Получение количества загруженных фотографий"""
    photo_ids = dialog_manager.dialog_data.get("new_profile", {}).get("photo_ids", [])
    return {
        "photo_count": len(photo_ids),
    }


async def get_add_name_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна ввода имени"""
    return {}


async def get_add_age_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна ввода возраста"""
    return {}


async def get_add_description_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна ввода описания"""
    return {}


async def get_add_audio_price_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна ввода цены аудио-чата"""
    return {}


async def get_add_video_price_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна ввода цены видео-чата"""
    return {}


async def get_add_private_price_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна ввода цены приватки"""
    return {}


async def get_add_channel_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна ввода ссылки на канал"""
    return {}


# Getters для редактирования
async def get_edit_name_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна редактирования имени"""
    profile_id = dialog_manager.dialog_data.get("selected_profile_id")
    logger.info(f"[get_edit_name_data] profile_id = {profile_id}")
    if not profile_id:
        logger.warning("[get_edit_name_data] profile_id не найден")
        return {"current_name": "Не выбрана"}
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            logger.warning(f"[get_edit_name_data] Анкета с id {profile_id} не найдена")
            return {"current_name": "Анкета не найдена"}
        logger.info(f"[get_edit_name_data] Найдена анкета: {profile.name}")
        return {"current_name": profile.name if profile.name else "Не указано"}


async def get_edit_age_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна редактирования возраста"""
    profile_id = dialog_manager.dialog_data.get("selected_profile_id")
    logger.info(f"[get_edit_age_data] profile_id = {profile_id}")
    if not profile_id:
        logger.warning("[get_edit_age_data] profile_id не найден")
        return {"current_age": "Не выбрана"}
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            logger.warning(f"[get_edit_age_data] Анкета с id {profile_id} не найдена")
            return {"current_age": "Анкета не найдена"}
        logger.info(f"[get_edit_age_data] Возраст: {profile.age}")
        return {"current_age": str(profile.age) if profile.age is not None else "Не указан"}


async def get_edit_description_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна редактирования описания"""
    profile_id = dialog_manager.dialog_data.get("selected_profile_id")
    if not profile_id:
        return {"current_description": "Не выбрана"}
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            return {"current_description": "Анкета не найдена"}
        return {"current_description": profile.description if profile.description else "Не указано"}


async def get_edit_audio_price_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна редактирования цены аудио-чата"""
    profile_id = dialog_manager.dialog_data.get("selected_profile_id")
    logger.info(f"[get_edit_audio_price_data] profile_id = {profile_id}")
    if not profile_id:
        logger.warning("[get_edit_audio_price_data] profile_id не найден")
        return {"current_price": "Не выбрана"}
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            logger.warning(f"[get_edit_audio_price_data] Анкета с id {profile_id} не найдена")
            return {"current_price": "Анкета не найдена"}
        logger.info(f"[get_edit_audio_price_data] Цена аудио-чата: {profile.audio_chat_price}")
        return {"current_price": str(profile.audio_chat_price) if profile.audio_chat_price is not None else "Не указана"}


async def get_edit_video_price_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна редактирования цены видео-чата"""
    profile_id = dialog_manager.dialog_data.get("selected_profile_id")
    if not profile_id:
        return {"current_price": "Не выбрана"}
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            return {"current_price": "Анкета не найдена"}
        return {"current_price": str(profile.video_chat_price) if profile.video_chat_price is not None else "Не указана"}


async def get_edit_private_price_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна редактирования цены приватки"""
    profile_id = dialog_manager.dialog_data.get("selected_profile_id")
    if not profile_id:
        return {"current_price": "Не выбрана"}
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            return {"current_price": "Анкета не найдена"}
        return {"current_price": str(profile.private_price) if profile.private_price is not None else "Не указана"}


async def get_edit_channel_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна редактирования ссылки на канал"""
    profile_id = dialog_manager.dialog_data.get("selected_profile_id")
    if not profile_id:
        return {"current_channel": "Не выбрана"}
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            return {"current_channel": "Анкета не найдена"}
        return {"current_channel": profile.channel_link if profile.channel_link else "Не указана"}


async def get_edit_photo_count_data(dialog_manager: DialogManager, **kwargs):
    """Получение количества загруженных фотографий при редактировании"""
    profile_id = dialog_manager.dialog_data.get("selected_profile_id")
    if not profile_id:
        return {"photo_count": 0}
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            return {"photo_count": 0}
        photo_ids = profile.photo_ids or []
        return {"photo_count": len(photo_ids)}


async def get_profile_detail_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна деталей анкеты"""
    profile_id = dialog_manager.dialog_data.get("selected_profile_id")
    if not profile_id:
        return {
            "profile_name": "Не выбрана",
            "profile_age": "",
            "profile_description": "",
            "audio_price": "",
            "video_price": "",
            "private_price": "",
            "channel_link": "",
            "games_list": "",
        }
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            return {
                "profile_name": "Анкета не найдена",
                "profile_age": "",
                "profile_description": "",
                "audio_price": "",
                "video_price": "",
                "private_price": "",
                "channel_link": "",
                "games_list": "",
            }
        
        # Формируем список игр
        games_names = [pg.game.name for pg in profile.games if pg.game]
        games_text = ", ".join(games_names) if games_names else "Нет игр"
        
        # Информация о фотографиях
        photo_ids = profile.photo_ids or []
        photo_count = len(photo_ids)
        photo_info = f"{photo_count}/3" if photo_count > 0 else "Нет фотографий"
        
        return {
            "profile_name": profile.name or "Не указано",
            "profile_age": f"{profile.age} лет" if profile.age else "Не указано",
            "profile_description": profile.description or "Не указано",
            "audio_price": f"{profile.audio_chat_price:.0f}₽/час" if profile.audio_chat_price else "Не указано",
            "video_price": f"{profile.video_chat_price:.0f}₽/час" if profile.video_chat_price else "Не указано",
            "private_price": f"{profile.private_price:.0f}₽" if profile.private_price else "Не указано",
            "channel_link": profile.channel_link or "Не указано",
            "games_list": games_text,
            "photo_info": photo_info,
            "has_photos": photo_count > 0,
        }


async def on_profile_select(c: CallbackQuery, button: Button, manager: DialogManager):
    """Выбор анкеты"""
    # В aiogram_dialog для ListGroup item_id передается через manager.item_id
    # manager в ListGroup является SubManager, который содержит item_id текущего элемента
    item_id = getattr(manager, 'item_id', None)
    
    # Fallback: если item_id не найден в manager, пробуем из callback_data
    if item_id is None:
        if c.data:
            parts = c.data.split(":")
            if len(parts) >= 3:
                item_id = parts[-1]
            else:
                item_id = parts[-1] if parts else None
        else:
            item_id = button.widget_id.split(":")[-1] if ":" in button.widget_id else None
    
    if not item_id:
        await c.answer("❌ Ошибка: не удалось получить ID анкеты", show_alert=True)
        return
    
    try:
        profile_id = int(item_id)
    except ValueError:
        await c.answer("❌ Ошибка: неверный формат ID анкеты", show_alert=True)
        return
    
    manager.dialog_data["selected_profile_id"] = profile_id
    await manager.switch_to(states.AdminProfiles.DETAIL)


async def on_view_photos(c: CallbackQuery, button: Button, manager: DialogManager):
    """Начало просмотра фотографий анкеты"""
    profile_id = manager.dialog_data.get("selected_profile_id")
    if not profile_id:
        await c.answer("❌ Анкета не выбрана", show_alert=True)
        return
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            await c.answer("❌ Анкета не найдена", show_alert=True)
            return
        
        photo_ids = profile.photo_ids or []
        if not photo_ids:
            await c.answer("❌ У этой анкеты нет фотографий", show_alert=True)
            return
        
        # Инициализируем просмотр с первой фотографии
        manager.dialog_data["photo_index"] = 0
        
        # Отправляем первую фотографию
        try:
            await c.bot.send_photo(
                chat_id=c.from_user.id,
                photo=photo_ids[0],
                caption=f"📷 Фотография 1 из {len(photo_ids)}\nАнкета: {profile.name}"
            )
        except Exception as e:
            logger.error(f"[on_view_photos] Ошибка при отправке фотографии: {e}")
        
        await manager.switch_to(states.AdminProfiles.VIEW_PHOTOS)


async def get_view_photos_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для просмотра фотографий"""
    profile_id = dialog_manager.dialog_data.get("selected_profile_id")
    photo_index = dialog_manager.dialog_data.get("photo_index", 0)
    
    if not profile_id:
        return {
            "photo_index": 0,
            "total_photos": 0,
            "photo_number": 0,
            "has_prev": False,
            "has_next": False,
        }
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            return {
                "photo_index": 0,
                "total_photos": 0,
                "photo_number": 0,
                "has_prev": False,
                "has_next": False,
            }
        
        photo_ids = profile.photo_ids or []
        total_photos = len(photo_ids)
        
        if total_photos == 0:
            return {
                "photo_index": 0,
                "total_photos": 0,
                "photo_number": 0,
                "has_prev": False,
                "has_next": False,
            }
        
        return {
            "photo_index": photo_index,
            "total_photos": total_photos,
            "photo_number": photo_index + 1,
            "has_prev": photo_index > 0,
            "has_next": photo_index < total_photos - 1,
            "profile_name": profile.name,
        }


async def on_prev_photo(c: CallbackQuery, button: Button, manager: DialogManager):
    """Переход к предыдущей фотографии"""
    profile_id = manager.dialog_data.get("selected_profile_id")
    photo_index = manager.dialog_data.get("photo_index", 0)
    
    if photo_index > 0:
        manager.dialog_data["photo_index"] = photo_index - 1
        
        # Отправляем предыдущую фотографию
        async with async_session_maker() as session:
            profile = await ProfileRepository.get_by_id(session, profile_id)
            if profile:
                photo_ids = profile.photo_ids or []
                new_index = photo_index - 1
                if new_index < len(photo_ids):
                    try:
                        await c.bot.send_photo(
                            chat_id=c.from_user.id,
                            photo=photo_ids[new_index],
                            caption=f"📷 Фотография {new_index + 1} из {len(photo_ids)}\nАнкета: {profile.name}"
                        )
                    except Exception as e:
                        logger.error(f"[on_prev_photo] Ошибка при отправке фотографии: {e}")
        
        await manager.show()


async def on_next_photo(c: CallbackQuery, button: Button, manager: DialogManager):
    """Переход к следующей фотографии"""
    profile_id = manager.dialog_data.get("selected_profile_id")
    if not profile_id:
        await c.answer("❌ Анкета не выбрана", show_alert=True)
        return
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            await c.answer("❌ Анкета не найдена", show_alert=True)
            return
        
        photo_ids = profile.photo_ids or []
        photo_index = manager.dialog_data.get("photo_index", 0)
        
        if photo_index < len(photo_ids) - 1:
            manager.dialog_data["photo_index"] = photo_index + 1
            
            # Отправляем следующую фотографию
            new_index = photo_index + 1
            try:
                await c.bot.send_photo(
                    chat_id=c.from_user.id,
                    photo=photo_ids[new_index],
                    caption=f"📷 Фотография {new_index + 1} из {len(photo_ids)}\nАнкета: {profile.name}"
                )
            except Exception as e:
                logger.error(f"[on_next_photo] Ошибка при отправке фотографии: {e}")
            
            await manager.show()


async def on_replace_photo(c: CallbackQuery, button: Button, manager: DialogManager):
    """Начало замены фотографии"""
    profile_id = manager.dialog_data.get("selected_profile_id")
    photo_index = manager.dialog_data.get("photo_index", 0)
    
    if not profile_id:
        await c.answer("❌ Анкета не выбрана", show_alert=True)
        return
    
    # Сохраняем индекс фотографии для замены
    manager.dialog_data["replace_photo_index"] = photo_index
    await manager.switch_to(states.AdminProfiles.REPLACE_PHOTO)


async def get_replace_photo_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна замены фотографии"""
    profile_id = dialog_manager.dialog_data.get("selected_profile_id")
    photo_index = dialog_manager.dialog_data.get("replace_photo_index", 0)
    
    if not profile_id:
        return {
            "photo_index": 0,
            "total_photos": 0,
            "photo_number": 0,
        }
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            return {
                "photo_index": 0,
                "total_photos": 0,
                "photo_number": 0,
            }
        
        photo_ids = profile.photo_ids or []
        total_photos = len(photo_ids)
        
        return {
            "photo_index": photo_index,
            "total_photos": total_photos,
            "photo_number": photo_index + 1,
        }


async def on_replace_photo_received(message: Message, widget: MessageInput, manager: DialogManager):
    """Обработка получения новой фотографии для замены"""
    if not message.photo:
        await message.answer("❌ Отправьте фотографию")
        return
    
    profile_id = manager.dialog_data.get("selected_profile_id")
    photo_index = manager.dialog_data.get("replace_photo_index")
    
    if profile_id is None or photo_index is None:
        await message.answer("❌ Ошибка: не выбрана фотография для замены")
        return
    
    # Берем самое большое фото
    photo = message.photo[-1]
    new_photo_id = photo.file_id
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            await message.answer("❌ Анкета не найдена")
            return
        
        photo_ids = profile.photo_ids or []
        if photo_index >= len(photo_ids):
            await message.answer("❌ Ошибка: неверный индекс фотографии")
            return
        
        # Заменяем фотографию
        photo_ids[photo_index] = new_photo_id
        
        # Сохраняем в базу
        await ProfileRepository.update(session, profile_id, {"photo_ids": photo_ids})
        
        await message.answer(f"✅ Фотография {photo_index + 1} заменена")
        
        # Возвращаемся к просмотру фотографий
        manager.dialog_data["photo_index"] = photo_index
        await manager.switch_to(states.AdminProfiles.VIEW_PHOTOS)


async def on_add_profile(c: CallbackQuery, button: Button, manager: DialogManager):
    """Начало добавления анкеты"""
    # Инициализация данных для новой анкеты
    manager.dialog_data["new_profile"] = {
        "name": None,
        "age": None,
        "description": None,
        "audio_chat_price": None,
        "video_chat_price": None,
        "private_price": None,
        "channel_link": None,
        "photo_ids": [],
        "games": [],
    }
    await manager.switch_to(states.AdminProfiles.ADD_NAME)


async def on_delete_confirm(c: CallbackQuery, button: Button, manager: DialogManager):
    """Подтверждение удаления анкеты"""
    profile_id = manager.dialog_data.get("selected_profile_id")
    if not profile_id:
        await c.answer("❌ Анкета не выбрана", show_alert=True)
        return
    
    async with async_session_maker() as session:
        deleted = await ProfileRepository.delete(session, profile_id)
        if deleted:
            await c.answer("✅ Анкета удалена")
            await manager.switch_to(states.AdminProfiles.LIST)
        else:
            await c.answer("❌ Ошибка при удалении", show_alert=True)


async def get_edit_menu_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для меню редактирования анкеты"""
    profile_id = dialog_manager.dialog_data.get("selected_profile_id")
    if not profile_id:
        return {
            "profile_name": "Не выбрана",
            "profile_age": "",
            "profile_description": "",
            "audio_price": "",
            "video_price": "",
            "private_price": "",
            "channel_link": "",
            "games_list": "",
        }
    
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            return {
                "profile_name": "Анкета не найдена",
                "profile_age": "",
                "profile_description": "",
                "audio_price": "",
                "video_price": "",
                "private_price": "",
                "channel_link": "",
                "games_list": "",
            }
        
        # Обновляем данные для редактирования из базы (чтобы всегда были актуальные)
        edit_profile = dialog_manager.dialog_data.get("edit_profile", {})
        edit_profile.update({
            "name": profile.name,
            "age": profile.age,
            "description": profile.description,
            "audio_chat_price": profile.audio_chat_price,
            "video_chat_price": profile.video_chat_price,
            "private_price": profile.private_price,
            "channel_link": profile.channel_link,
            "photo_ids": profile.photo_ids or [],
            "games": [pg.game_id for pg in profile.games],
        })
        dialog_manager.dialog_data["edit_profile"] = edit_profile
        dialog_manager.dialog_data["selected_games"] = [pg.game_id for pg in profile.games]
        
        # Форматируем игры
        games_list = ", ".join([pg.game.name for pg in profile.games]) if profile.games else "Не указаны"
        
        # Форматируем цены
        audio_price = f"{profile.audio_chat_price}₽/час" if profile.audio_chat_price else "Не указана"
        video_price = f"{profile.video_chat_price}₽/час" if profile.video_chat_price else "Не указана"
        private_price = f"{profile.private_price}₽" if profile.private_price else "Не указана"
        
        # Информация о фотографиях
        photo_ids = profile.photo_ids or []
        photo_count = len(photo_ids)
        photo_info = f"{photo_count}/3" if photo_count > 0 else "Нет фотографий"
        
        return {
            "profile_name": profile.name,
            "profile_age": str(profile.age) if profile.age else "Не указан",
            "profile_description": profile.description if profile.description else "Не указано",
            "audio_price": audio_price,
            "video_price": video_price,
            "private_price": private_price,
            "channel_link": profile.channel_link if profile.channel_link else "Не указана",
            "games_list": games_list,
            "photo_info": photo_info,
        }


async def on_edit_field_select(c: CallbackQuery, button: Button, manager: DialogManager):
    """Выбор поля для редактирования"""
    field = button.widget_id.split("_")[-1]  # Получаем название поля из id кнопки
    
    field_map = {
        "name": states.AdminProfiles.EDIT_NAME,
        "age": states.AdminProfiles.EDIT_AGE,
        "description": states.AdminProfiles.EDIT_DESCRIPTION,
        "audio": states.AdminProfiles.EDIT_AUDIO_PRICE,
        "video": states.AdminProfiles.EDIT_VIDEO_PRICE,
        "private": states.AdminProfiles.EDIT_PRIVATE_PRICE,
        "channel": states.AdminProfiles.EDIT_CHANNEL,
        "games": states.AdminProfiles.EDIT_GAMES,
        "photos": states.AdminProfiles.EDIT_PHOTOS,
    }
    
    target_state = field_map.get(field)
    if target_state:
        await manager.switch_to(target_state)
    else:
        await c.answer("❌ Неизвестное поле", show_alert=True)


async def on_edit_profile(c: CallbackQuery, button: Button, manager: DialogManager):
    """Начало редактирования анкеты - переход к меню выбора поля"""
    profile_id = manager.dialog_data.get("selected_profile_id")
    if not profile_id:
        await c.answer("❌ Анкета не выбрана", show_alert=True)
        return
    
    # Загружаем данные анкеты для редактирования
    async with async_session_maker() as session:
        profile = await ProfileRepository.get_by_id(session, profile_id)
        if not profile:
            await c.answer("❌ Анкета не найдена", show_alert=True)
            return
        
        # Сохраняем текущие данные для редактирования
        manager.dialog_data["edit_profile"] = {
            "name": profile.name,
            "age": profile.age,
            "description": profile.description,
            "audio_chat_price": profile.audio_chat_price,
            "video_chat_price": profile.video_chat_price,
            "private_price": profile.private_price,
            "channel_link": profile.channel_link,
            "photo_ids": profile.photo_ids or [],
            "games": [pg.game_id for pg in profile.games],
        }
        # Сохраняем текущие игры для редактирования
        manager.dialog_data["selected_games"] = [pg.game_id for pg in profile.games]
    
    await manager.switch_to(states.AdminProfiles.EDIT_MENU)


# Обработчики ввода данных для новой анкеты
async def on_name_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода имени"""
    if not text or len(text.strip()) < 2:
        await message.answer("❌ Имя должно содержать минимум 2 символа")
        return
    
    manager.dialog_data["new_profile"]["name"] = text.strip()
    await manager.switch_to(states.AdminProfiles.ADD_AGE)


# Обработчики ввода данных для редактирования анкеты
async def on_edit_name_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода имени при редактировании"""
    if not text or len(text.strip()) < 2:
        await message.answer("❌ Имя должно содержать минимум 2 символа")
        return
    
    manager.dialog_data["edit_profile"]["name"] = text.strip()
    # Сохраняем изменения сразу
    profile_id = manager.dialog_data.get("selected_profile_id")
    if profile_id:
        async with async_session_maker() as session:
            await ProfileRepository.update(session, profile_id, {"name": text.strip()})
    await message.answer("✅ Имя обновлено")
    await manager.switch_to(states.AdminProfiles.EDIT_MENU)


async def on_age_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода возраста"""
    try:
        age = int(text.strip())
        if age < 18 or age > 100:
            await message.answer("❌ Возраст должен быть от 18 до 100 лет")
            return
        manager.dialog_data["new_profile"]["age"] = age
    except ValueError:
        await message.answer("❌ Введите корректный возраст (число)")
        return
    
    await manager.switch_to(states.AdminProfiles.ADD_DESCRIPTION)


async def on_edit_age_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода возраста при редактировании"""
    try:
        age = int(text.strip())
        if age < 18 or age > 100:
            await message.answer("❌ Возраст должен быть от 18 до 100 лет")
            return
        manager.dialog_data["edit_profile"]["age"] = age
        # Сохраняем изменения сразу
        profile_id = manager.dialog_data.get("selected_profile_id")
        if profile_id:
            async with async_session_maker() as session:
                await ProfileRepository.update(session, profile_id, {"age": age})
        await message.answer("✅ Возраст обновлен")
    except ValueError:
        await message.answer("❌ Введите корректный возраст (число)")
        return
    
    await manager.switch_to(states.AdminProfiles.EDIT_MENU)


async def on_description_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода описания"""
    if not text or len(text.strip()) < 10:
        await message.answer("❌ Описание должно содержать минимум 10 символов")
        return
    
    manager.dialog_data["new_profile"]["description"] = text.strip()
    await manager.switch_to(states.AdminProfiles.ADD_AUDIO_PRICE)


async def on_edit_description_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода описания при редактировании"""
    if not text or len(text.strip()) < 10:
        await message.answer("❌ Описание должно содержать минимум 10 символов")
        return
    
    manager.dialog_data["edit_profile"]["description"] = text.strip()
    # Сохраняем изменения сразу
    profile_id = manager.dialog_data.get("selected_profile_id")
    if profile_id:
        async with async_session_maker() as session:
            await ProfileRepository.update(session, profile_id, {"description": text.strip()})
    await message.answer("✅ Описание обновлено")
    await manager.switch_to(states.AdminProfiles.EDIT_MENU)


async def on_audio_price_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода цены аудио-чата"""
    try:
        price = float(text.strip())
        if price < 0:
            await message.answer("❌ Цена не может быть отрицательной")
            return
        manager.dialog_data["new_profile"]["audio_chat_price"] = price
    except ValueError:
        await message.answer("❌ Введите корректную цену (число)")
        return
    
    await manager.switch_to(states.AdminProfiles.ADD_VIDEO_PRICE)


async def on_edit_audio_price_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода цены аудио-чата при редактировании"""
    try:
        price = float(text.strip())
        if price < 0:
            await message.answer("❌ Цена не может быть отрицательной")
            return
        manager.dialog_data["edit_profile"]["audio_chat_price"] = price
        # Сохраняем изменения сразу
        profile_id = manager.dialog_data.get("selected_profile_id")
        if profile_id:
            async with async_session_maker() as session:
                await ProfileRepository.update(session, profile_id, {"audio_chat_price": price})
        await message.answer("✅ Цена аудио-чата обновлена")
    except ValueError:
        await message.answer("❌ Введите корректную цену (число)")
        return
    
    await manager.switch_to(states.AdminProfiles.EDIT_MENU)


async def on_video_price_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода цены видео-чата"""
    try:
        price = float(text.strip())
        if price < 0:
            await message.answer("❌ Цена не может быть отрицательной")
            return
        manager.dialog_data["new_profile"]["video_chat_price"] = price
    except ValueError:
        await message.answer("❌ Введите корректную цену (число)")
        return
    
    await manager.switch_to(states.AdminProfiles.ADD_PRIVATE_PRICE)


async def on_edit_video_price_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода цены видео-чата при редактировании"""
    try:
        price = float(text.strip())
        if price < 0:
            await message.answer("❌ Цена не может быть отрицательной")
            return
        manager.dialog_data["edit_profile"]["video_chat_price"] = price
        # Сохраняем изменения сразу
        profile_id = manager.dialog_data.get("selected_profile_id")
        if profile_id:
            async with async_session_maker() as session:
                await ProfileRepository.update(session, profile_id, {"video_chat_price": price})
        await message.answer("✅ Цена видео-чата обновлена")
    except ValueError:
        await message.answer("❌ Введите корректную цену (число)")
        return
    
    await manager.switch_to(states.AdminProfiles.EDIT_MENU)


async def on_private_price_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода цены приватки"""
    if text.strip().lower() in ["нет", "н", "skip", "пропустить"]:
        manager.dialog_data["new_profile"]["private_price"] = None
    else:
        try:
            price = float(text.strip())
            if price < 0:
                await message.answer("❌ Цена не может быть отрицательной")
                return
            manager.dialog_data["new_profile"]["private_price"] = price
        except ValueError:
            await message.answer("❌ Введите корректную цену (число) или 'нет' для пропуска")
            return
    
    await manager.switch_to(states.AdminProfiles.ADD_CHANNEL)


async def on_edit_private_price_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода цены приватки при редактировании"""
    if text.strip().lower() in ["нет", "н", "skip", "пропустить"]:
        manager.dialog_data["edit_profile"]["private_price"] = None
        # Сохраняем изменения сразу
        profile_id = manager.dialog_data.get("selected_profile_id")
        if profile_id:
            async with async_session_maker() as session:
                await ProfileRepository.update(session, profile_id, {"private_price": None})
        await message.answer("✅ Цена приватки удалена")
    else:
        try:
            price = float(text.strip())
            if price < 0:
                await message.answer("❌ Цена не может быть отрицательной")
                return
            manager.dialog_data["edit_profile"]["private_price"] = price
            # Сохраняем изменения сразу
            profile_id = manager.dialog_data.get("selected_profile_id")
            if profile_id:
                async with async_session_maker() as session:
                    await ProfileRepository.update(session, profile_id, {"private_price": price})
            await message.answer("✅ Цена приватки обновлена")
        except ValueError:
            await message.answer("❌ Введите корректную цену (число) или 'нет' для пропуска")
            return
    
    await manager.switch_to(states.AdminProfiles.EDIT_MENU)


async def on_channel_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода ссылки на канал"""
    text = text.strip()
    if text.lower() in ["нет", "н", "skip", "пропустить"]:
        manager.dialog_data["new_profile"]["channel_link"] = None
    else:
        # Проверяем, что ссылка начинается с @
        if not text.startswith("@"):
            await message.answer("❌ Ссылка на канал должна начинаться с @")
            return
        manager.dialog_data["new_profile"]["channel_link"] = text
    
    await manager.switch_to(states.AdminProfiles.ADD_GAMES)


async def on_edit_channel_input(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода ссылки на канал при редактировании"""
    text = text.strip()
    if text.lower() in ["нет", "н", "skip", "пропустить"]:
        manager.dialog_data["edit_profile"]["channel_link"] = None
        # Сохраняем изменения сразу
        profile_id = manager.dialog_data.get("selected_profile_id")
        if profile_id:
            async with async_session_maker() as session:
                await ProfileRepository.update(session, profile_id, {"channel_link": None})
        await message.answer("✅ Ссылка на канал удалена")
    else:
        # Проверяем, что ссылка начинается с @
        if not text.startswith("@"):
            await message.answer("❌ Ссылка на канал должна начинаться с @")
            return
        manager.dialog_data["edit_profile"]["channel_link"] = text
        # Сохраняем изменения сразу
        profile_id = manager.dialog_data.get("selected_profile_id")
        if profile_id:
            async with async_session_maker() as session:
                await ProfileRepository.update(session, profile_id, {"channel_link": text})
        await message.answer("✅ Ссылка на канал обновлена")
    
    await manager.switch_to(states.AdminProfiles.EDIT_MENU)


async def on_photo_received(message: Message, widget: MessageInput, manager: DialogManager):
    """Обработка получения фотографии"""
    if message.photo:
        # Берем самое большое фото
        photo = message.photo[-1]
        photo_id = photo.file_id
        
        photos = manager.dialog_data["new_profile"].get("photo_ids", [])
        if len(photos) >= 3:
            await message.answer("❌ Можно загрузить максимум 3 фотографии")
            return
        
        photos.append(photo_id)
        manager.dialog_data["new_profile"]["photo_ids"] = photos
        
        remaining = 3 - len(photos)
        if remaining > 0:
            await message.answer(f"✅ Фото добавлено. Осталось загрузить: {remaining}")
        else:
            await message.answer("✅ Все 3 фотографии загружены! Нажмите 'Продолжить'")
    else:
        await message.answer("❌ Отправьте фотографию")


async def on_edit_photo_received(message: Message, widget: MessageInput, manager: DialogManager):
    """Обработка получения фотографии при редактировании"""
    if message.photo:
        # Берем самое большое фото
        photo = message.photo[-1]
        photo_id = photo.file_id
        
        photos = manager.dialog_data["edit_profile"].get("photo_ids", [])
        if len(photos) >= 3:
            await message.answer("❌ Можно загрузить максимум 3 фотографии")
            return
        
        photos.append(photo_id)
        manager.dialog_data["edit_profile"]["photo_ids"] = photos
        
        # Сохраняем изменения сразу
        profile_id = manager.dialog_data.get("selected_profile_id")
        if profile_id:
            async with async_session_maker() as session:
                await ProfileRepository.update(session, profile_id, {"photo_ids": photos})
        
        remaining = 3 - len(photos)
        if remaining > 0:
            await message.answer(f"✅ Фото добавлено. Осталось загрузить: {remaining}")
        else:
            await message.answer("✅ Все 3 фотографии загружены!")
        await manager.switch_to(states.AdminProfiles.EDIT_MENU)
    else:
        await message.answer("❌ Отправьте фотографию")


async def on_game_toggle(c: CallbackQuery, button: Button, manager: DialogManager):
    """Переключение выбора игры"""
    logger.info(f"[on_game_toggle] Начало обработки. Callback data: {c.data}")
    logger.info(f"[on_game_toggle] Button widget_id: {button.widget_id if hasattr(button, 'widget_id') else 'N/A'}")
    
    # В aiogram_dialog для ListGroup item_id передается через manager.item_id
    # manager в ListGroup является SubManager, который содержит item_id текущего элемента
    logger.info(f"[on_game_toggle] Шаг 1: Получаем item_id из manager.item_id")
    logger.info(f"[on_game_toggle] manager.item_id = {getattr(manager, 'item_id', 'N/A')}")
    logger.info(f"[on_game_toggle] Тип manager = {type(manager)}")
    logger.info(f"[on_game_toggle] Атрибуты manager: {dir(manager)}")
    
    item_id = getattr(manager, 'item_id', None)
    
    # Fallback: если item_id не найден в manager, пробуем из callback_data
    if item_id is None:
        logger.info(f"[on_game_toggle] Шаг 2: item_id не найден в manager, пробуем callback_data")
        logger.info(f"[on_game_toggle] Проверка callback_data. c.data = {c.data}")
        
        if c.data:
            parts = c.data.split(":")
            logger.info(f"[on_game_toggle] Разделили на части. parts = {parts}, len(parts) = {len(parts)}")
            
            if len(parts) >= 3:
                item_id = parts[-1]
                logger.info(f"[on_game_toggle] len(parts) >= 3, взяли последнюю часть. item_id = {item_id}")
            else:
                item_id = parts[-1] if parts else None
                logger.info(f"[on_game_toggle] len(parts) < 3, взяли последнюю часть. item_id = {item_id}")
        else:
            logger.info(f"[on_game_toggle] c.data отсутствует")
    
    logger.info(f"[on_game_toggle] Шаг 3: Итоговый item_id перед проверкой = {item_id}")
    logger.info(f"[on_game_toggle] Тип item_id = {type(item_id)}")
    
    if not item_id:
        logger.error(f"[on_game_toggle] ОШИБКА: item_id не найден. manager.item_id = {getattr(manager, 'item_id', 'N/A')}, callback_data = {c.data}")
        await c.answer("❌ Ошибка: не удалось получить ID игры", show_alert=True)
        return
    
    logger.info(f"[on_game_toggle] Шаг 4: Пытаемся преобразовать item_id '{item_id}' в int")
    try:
        # item_id может быть строкой или уже числом
        if isinstance(item_id, str):
            game_id = int(item_id)
        else:
            game_id = int(item_id)
        logger.info(f"[on_game_toggle] Шаг 5: Успешно преобразовали в int. game_id = {game_id}")
    except (ValueError, TypeError) as e:
        logger.error(f"[on_game_toggle] ОШИБКА: Не удалось преобразовать '{item_id}' в int. Ошибка: {e}")
        logger.error(f"[on_game_toggle] Тип item_id: {type(item_id)}, значение: {repr(item_id)}")
        await c.answer(f"❌ Ошибка: неверный формат ID игры. Получено: '{item_id}'", show_alert=True)
        return
    
    logger.info(f"[on_game_toggle] Шаг 7: Получаем selected_games из dialog_data")
    selected_games = manager.dialog_data.get("selected_games", [])
    logger.info(f"[on_game_toggle] Шаг 8: Текущий список selected_games = {selected_games}")
    
    if game_id in selected_games:
        logger.info(f"[on_game_toggle] Шаг 9: game_id {game_id} уже в списке, удаляем")
        selected_games.remove(game_id)
        await c.answer(f"❌ Игра удалена из списка")
    else:
        logger.info(f"[on_game_toggle] Шаг 9: game_id {game_id} нет в списке, добавляем")
        selected_games.append(game_id)
        await c.answer(f"✅ Игра добавлена в список")
    
    logger.info(f"[on_game_toggle] Шаг 10: Обновленный список selected_games = {selected_games}")
    manager.dialog_data["selected_games"] = selected_games
    
    # Определяем, в каком режиме мы находимся (добавление или редактирование)
    current_state = manager.current_context().state
    logger.info(f"[on_game_toggle] Шаг 11: Текущее состояние = {current_state}")
    
    if current_state == states.AdminProfiles.EDIT_GAMES:
        logger.info(f"[on_game_toggle] Режим редактирования, переключаемся на EDIT_GAMES")
        await manager.switch_to(states.AdminProfiles.EDIT_GAMES)
    else:
        logger.info(f"[on_game_toggle] Режим добавления, переключаемся на ADD_GAMES")
        await manager.switch_to(states.AdminProfiles.ADD_GAMES)
    logger.info(f"[on_game_toggle] Шаг 12: Функция завершена успешно")


async def on_save_profile(c: CallbackQuery, button: Button, manager: DialogManager):
    """Сохранение новой анкеты"""
    profile_data = manager.dialog_data.get("new_profile")
    if not profile_data:
        await c.answer("❌ Ошибка: данные анкеты не найдены", show_alert=True)
        return
    
    # Проверка обязательных полей
    if not profile_data.get("name") or not profile_data.get("audio_chat_price") or not profile_data.get("video_chat_price"):
        await c.answer("❌ Заполните все обязательные поля", show_alert=True)
        return
    
    if len(profile_data.get("photo_ids", [])) < 3:
        await c.answer("❌ Загрузите 3 фотографии", show_alert=True)
        return
    
    selected_games = manager.dialog_data.get("selected_games", [])
    
    async with async_session_maker() as session:
        # Создаем анкету
        profile = await ProfileRepository.create(session, {
            "name": profile_data["name"],
            "age": profile_data.get("age"),
            "description": profile_data.get("description"),
            "audio_chat_price": profile_data["audio_chat_price"],
            "video_chat_price": profile_data["video_chat_price"],
            "private_price": profile_data.get("private_price"),
            "channel_link": profile_data.get("channel_link"),
            "photo_ids": profile_data["photo_ids"],
        })
        
        # Добавляем игры
        for game_id in selected_games:
            await ProfileRepository.add_game(session, profile.id, game_id)
        
        await c.answer("✅ Анкета создана")
        await manager.switch_to(states.AdminProfiles.LIST)


async def on_save_edited_profile(c: CallbackQuery, button: Button, manager: DialogManager):
    """Сохранение отредактированной анкеты (для игр и фотографий)"""
    profile_id = manager.dialog_data.get("selected_profile_id")
    if not profile_id:
        await c.answer("❌ Ошибка: анкета не выбрана", show_alert=True)
        return
    
    profile_data = manager.dialog_data.get("edit_profile")
    if not profile_data:
        await c.answer("❌ Ошибка: данные анкеты не найдены", show_alert=True)
        return
    
    selected_games = manager.dialog_data.get("selected_games", [])
    
    async with async_session_maker() as session:
        # Обновляем игры: удаляем все старые и добавляем новые
        current_profile = await ProfileRepository.get_by_id(session, profile_id)
        if current_profile:
            # Удаляем все старые игры
            for pg in current_profile.games:
                await ProfileRepository.remove_game(session, profile_id, pg.game_id)
        
        # Добавляем новые игры
        for game_id in selected_games:
            await ProfileRepository.add_game(session, profile_id, game_id)
        
        # Обновляем фотографии, если они были изменены
        if "photo_ids" in profile_data:
            await ProfileRepository.update(session, profile_id, {
                "photo_ids": profile_data.get("photo_ids", []),
            })
        
        await c.answer("✅ Изменения сохранены")
        await manager.switch_to(states.AdminProfiles.EDIT_MENU)


profiles_dialog = Dialog(
    Window(
        Const("👤 <b>Управление анкетами</b>\n\nВыберите действие:"),
        Column(
            SwitchTo(
                Const("📋 Список анкет"),
                id="list",
                state=states.AdminProfiles.LIST,
            ),
            Button(
                Const("➕ Добавить анкету"),
                id="add",
                on_click=on_add_profile,
            ),
            Cancel(Const("🔙 Назад")),
        ),
        getter=get_main_data,
        state=states.AdminProfiles.MAIN,
    ),
    
    Window(
        Format("📋 <b>Список анкет</b>\n\n"),
        ScrollingGroup(
            ListGroup(
                Button(
                    Format("{item.name}"),
                    id="profile_btn",
                    on_click=on_profile_select,
                ),
                id="profiles_list",
                item_id_getter=lambda item: str(item.id),
                items="profiles",
            ),
            id="profiles_scroll",
            width=1,
            height=10,
        ),
        Back(Const("🔙 Назад")),
        getter=get_profiles_data,
        state=states.AdminProfiles.LIST,
    ),
    
    # Добавление анкеты - шаг 1: Имя
    Window(
        Const("➕ <b>Добавить анкету</b>\n\nВведите имя:"),
        TextInput(
            id="name_input",
            on_success=on_name_input,
        ),
        Back(Const("🔙 Назад")),
        getter=get_add_name_data,
        state=states.AdminProfiles.ADD_NAME,
    ),
    
    # Шаг 2: Возраст
    Window(
        Const("Введите возраст:"),
        TextInput(
            id="age_input",
            on_success=on_age_input,
        ),
        Back(Const("🔙 Назад")),
        getter=get_add_age_data,
        state=states.AdminProfiles.ADD_AGE,
    ),
    
    # Шаг 3: Описание
    Window(
        Const("Введите описание:"),
        TextInput(
            id="description_input",
            on_success=on_description_input,
        ),
        Back(Const("🔙 Назад")),
        getter=get_add_description_data,
        state=states.AdminProfiles.ADD_DESCRIPTION,
    ),
    
    # Шаг 4: Цена аудио-чата
    Window(
        Const("Введите цену аудио-чата (₽/час):"),
        TextInput(
            id="audio_price_input",
            on_success=on_audio_price_input,
        ),
        Back(Const("🔙 Назад")),
        getter=get_add_audio_price_data,
        state=states.AdminProfiles.ADD_AUDIO_PRICE,
    ),
    
    # Шаг 5: Цена видео-чата
    Window(
        Const("Введите цену видео-чата (₽/час):"),
        TextInput(
            id="video_price_input",
            on_success=on_video_price_input,
        ),
        Back(Const("🔙 Назад")),
        getter=get_add_video_price_data,
        state=states.AdminProfiles.ADD_VIDEO_PRICE,
    ),
    
    # Шаг 6: Цена приватки
    Window(
        Const("Введите цену приватки (₽) или 'нет' для пропуска:"),
        TextInput(
            id="private_price_input",
            on_success=on_private_price_input,
        ),
        Back(Const("🔙 Назад")),
        getter=get_add_private_price_data,
        state=states.AdminProfiles.ADD_PRIVATE_PRICE,
    ),
    
    # Шаг 7: Ссылка на канал
    Window(
        Const("Введите ссылку на канал (начинается с @) или 'нет' для пропуска:"),
        TextInput(
            id="channel_input",
            on_success=on_channel_input,
        ),
        Back(Const("🔙 Назад")),
        getter=get_add_channel_data,
        state=states.AdminProfiles.ADD_CHANNEL,
    ),
    
    # Шаг 8: Выбор игр
    Window(
        Format("🎮 <b>Выберите игры</b>\n\nВыбрано: {selected_count}{selected_text}"),
        ScrollingGroup(
            ListGroup(
                Button(
                    Format("{item.display_name}"),
                    id="game_toggle_btn",
                    on_click=on_game_toggle,
                ),
                id="games_list",
                item_id_getter=lambda item: str(item.id),
                items="games",
            ),
            id="games_scroll",
            width=1,
            height=10,
        ),
        Button(
            Const("✅ Продолжить"),
            id="continue",
            on_click=lambda c, b, m: m.switch_to(states.AdminProfiles.ADD_PHOTOS),
        ),
        Back(Const("🔙 Назад")),
        getter=get_games_for_profile,
        state=states.AdminProfiles.ADD_GAMES,
    ),
    
    # Шаг 9: Загрузка фотографий
    Window(
        Format("📷 <b>Загрузите 3 фотографии</b>\n\nЗагружено: {photo_count}/3"),
        MessageInput(
            func=on_photo_received,
            content_types=["photo"],
        ),
        Button(
            Const("✅ Продолжить"),
            id="continue",
            on_click=on_save_profile,
        ),
        Back(Const("🔙 Назад")),
        getter=get_photo_count_data,
        state=states.AdminProfiles.ADD_PHOTOS,
    ),
    
    # Окно деталей анкеты
    Window(
        Format(
            "👤 <b>Анкета: {profile_name}</b>\n\n"
            "Возраст: {profile_age}\n"
            "Описание: {profile_description}\n\n"
            "💰 <b>Цены:</b>\n"
            "Аудио-чат: {audio_price}\n"
            "Видео-чат: {video_price}\n"
            "Приватка: {private_price}\n\n"
            "📱 Канал: {channel_link}\n"
            "🎮 Игры: {games_list}\n"
            "📷 Фотографии: {photo_info}"
        ),
        Column(
            Button(
                Const("📷 Просмотреть фотографии"),
                id="view_photos",
                on_click=on_view_photos,
                when="has_photos",
            ),
            Button(
                Const("✏️ Редактировать"),
                id="edit",
                on_click=on_edit_profile,
            ),
            Button(
                Const("🗑️ Удалить"),
                id="delete",
                on_click=lambda c, b, m: m.switch_to(states.AdminProfiles.DELETE_CONFIRM),
            ),
            Button(
                Const("🔙 Назад"),
                id="back",
                on_click=lambda c, b, m: m.switch_to(states.AdminProfiles.LIST),
            ),
        ),
        getter=get_profile_detail_data,
        state=states.AdminProfiles.DETAIL,
    ),
    
    # Подтверждение удаления
    Window(
        Format("❓ <b>Подтверждение удаления</b>\n\nВы уверены, что хотите удалить анкету:\n<b>{profile_name}</b>?"),
        Row(
            Button(
                Const("✅ Да, удалить"),
                id="confirm_delete",
                on_click=on_delete_confirm,
            ),
            Button(
                Const("❌ Отмена"),
                id="cancel_delete",
                on_click=lambda c, b, m: m.switch_to(states.AdminProfiles.DETAIL),
            ),
        ),
        getter=get_profile_detail_data,
        state=states.AdminProfiles.DELETE_CONFIRM,
    ),
    
    # Меню редактирования анкеты
    Window(
        Format(
            "✏️ <b>Редактирование анкеты: {profile_name}</b>\n\n"
            "👤 <b>Текущие данные:</b>\n"
            "Имя: {profile_name}\n"
            "Возраст: {profile_age}\n"
            "Описание: {profile_description}\n\n"
            "💰 <b>Цены:</b>\n"
            "Аудио-чат: {audio_price}\n"
            "Видео-чат: {video_price}\n"
            "Приватка: {private_price}\n\n"
            "📱 Канал: {channel_link}\n"
            "🎮 Игры: {games_list}\n"
            "📷 Фотографии: {photo_info}\n\n"
            "<b>Выберите, что хотите изменить:</b>"
        ),
        Column(
            Button(
                Const("👤 Имя"),
                id="edit_field_name",
                on_click=on_edit_field_select,
            ),
            Button(
                Const("🎂 Возраст"),
                id="edit_field_age",
                on_click=on_edit_field_select,
            ),
            Button(
                Const("📝 Описание"),
                id="edit_field_description",
                on_click=on_edit_field_select,
            ),
            Button(
                Const("💰 Цена аудио-чата"),
                id="edit_field_audio",
                on_click=on_edit_field_select,
            ),
            Button(
                Const("💰 Цена видео-чата"),
                id="edit_field_video",
                on_click=on_edit_field_select,
            ),
            Button(
                Const("💰 Цена приватки"),
                id="edit_field_private",
                on_click=on_edit_field_select,
            ),
            Button(
                Const("📱 Канал"),
                id="edit_field_channel",
                on_click=on_edit_field_select,
            ),
            Button(
                Const("🎮 Игры"),
                id="edit_field_games",
                on_click=on_edit_field_select,
            ),
            Button(
                Const("📷 Фотографии"),
                id="edit_field_photos",
                on_click=on_edit_field_select,
            ),
            Button(
                Const("🔙 К анкете"),
                id="back_to_detail",
                on_click=lambda c, b, m: m.switch_to(states.AdminProfiles.DETAIL),
            ),
        ),
        getter=get_edit_menu_data,
        state=states.AdminProfiles.EDIT_MENU,
    ),
    
    # Редактирование анкеты - Имя
    Window(
        Format("✏️ <b>Редактировать имя</b>\n\nТекущее имя: {current_name}\n\nВведите новое имя:"),
        TextInput(
            id="edit_name_input",
            on_success=on_edit_name_input,
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(states.AdminProfiles.EDIT_MENU),
        ),
        getter=get_edit_name_data,
        state=states.AdminProfiles.EDIT_NAME,
    ),
    
    # Редактирование возраста
    Window(
        Format("✏️ <b>Редактировать возраст</b>\n\nТекущий возраст: {current_age}\n\nВведите новый возраст:"),
        TextInput(
            id="edit_age_input",
            on_success=on_edit_age_input,
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(states.AdminProfiles.EDIT_MENU),
        ),
        getter=get_edit_age_data,
        state=states.AdminProfiles.EDIT_AGE,
    ),
    
    # Редактирование описания
    Window(
        Format("✏️ <b>Редактировать описание</b>\n\nТекущее описание: {current_description}\n\nВведите новое описание:"),
        TextInput(
            id="edit_description_input",
            on_success=on_edit_description_input,
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(states.AdminProfiles.EDIT_MENU),
        ),
        getter=get_edit_description_data,
        state=states.AdminProfiles.EDIT_DESCRIPTION,
    ),
    
    # Редактирование цены аудио-чата
    Window(
        Format("✏️ <b>Редактировать цену аудио-чата</b>\n\nТекущая цена: {current_price}₽/час\n\nВведите новую цену (₽/час):"),
        TextInput(
            id="edit_audio_price_input",
            on_success=on_edit_audio_price_input,
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(states.AdminProfiles.EDIT_MENU),
        ),
        getter=get_edit_audio_price_data,
        state=states.AdminProfiles.EDIT_AUDIO_PRICE,
    ),
    
    # Редактирование цены видео-чата
    Window(
        Format("✏️ <b>Редактировать цену видео-чата</b>\n\nТекущая цена: {current_price}₽/час\n\nВведите новую цену (₽/час):"),
        TextInput(
            id="edit_video_price_input",
            on_success=on_edit_video_price_input,
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(states.AdminProfiles.EDIT_MENU),
        ),
        getter=get_edit_video_price_data,
        state=states.AdminProfiles.EDIT_VIDEO_PRICE,
    ),
    
    # Редактирование цены приватки
    Window(
        Format("✏️ <b>Редактировать цену приватки</b>\n\nТекущая цена: {current_price}₽\n\nВведите новую цену (₽) или 'нет' для пропуска:"),
        TextInput(
            id="edit_private_price_input",
            on_success=on_edit_private_price_input,
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(states.AdminProfiles.EDIT_MENU),
        ),
        getter=get_edit_private_price_data,
        state=states.AdminProfiles.EDIT_PRIVATE_PRICE,
    ),
    
    # Редактирование ссылки на канал
    Window(
        Format("✏️ <b>Редактировать канал</b>\n\nТекущая ссылка: {current_channel}\n\nВведите новую ссылку (начинается с @) или 'нет' для пропуска:"),
        TextInput(
            id="edit_channel_input",
            on_success=on_edit_channel_input,
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(states.AdminProfiles.EDIT_MENU),
        ),
        getter=get_edit_channel_data,
        state=states.AdminProfiles.EDIT_CHANNEL,
    ),
    
    # Редактирование игр
    Window(
        Format("🎮 <b>Редактировать игры</b>\n\nВыбрано: {selected_count}{selected_text}"),
        ScrollingGroup(
            ListGroup(
                Button(
                    Format("{item.display_name}"),
                    id="game_toggle_btn",
                    on_click=on_game_toggle,
                ),
                id="games_list",
                item_id_getter=lambda item: str(item.id),
                items="games",
            ),
            id="games_scroll",
            width=1,
            height=10,
        ),
        Button(
            Const("✅ Сохранить"),
            id="save",
            on_click=on_save_edited_profile,
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(states.AdminProfiles.EDIT_MENU),
        ),
        getter=get_games_for_profile,
        state=states.AdminProfiles.EDIT_GAMES,
    ),
    
    # Редактирование фотографий
    Window(
        Format("📷 <b>Редактировать фотографии</b>\n\nЗагружено: {photo_count}/3\n\nОтправьте фотографии для замены:"),
        MessageInput(
            func=on_edit_photo_received,
            content_types=["photo"],
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(states.AdminProfiles.EDIT_MENU),
        ),
        getter=get_edit_photo_count_data,
        state=states.AdminProfiles.EDIT_PHOTOS,
    ),
    
    # Просмотр фотографий с пролистыванием
    Window(
        Format("📷 <b>Просмотр фотографий</b>\n\nФотография {photo_number} из {total_photos}"),
        Row(
            Button(
                Const("◀️ Предыдущая"),
                id="prev_photo",
                on_click=on_prev_photo,
                when="has_prev",
            ),
            Button(
                Const("Следующая ▶️"),
                id="next_photo",
                on_click=on_next_photo,
                when="has_next",
            ),
        ),
        Column(
            Button(
                Const("🔄 Заменить эту фотографию"),
                id="replace_photo",
                on_click=on_replace_photo,
            ),
            Button(
                Const("🔙 Назад"),
                id="back",
                on_click=lambda c, b, m: m.switch_to(states.AdminProfiles.DETAIL),
            ),
        ),
        getter=get_view_photos_data,
        state=states.AdminProfiles.VIEW_PHOTOS,
    ),
    
    # Замена фотографии
    Window(
        Format("📷 <b>Заменить фотографию</b>\n\nТекущая фотография: {photo_number} из {total_photos}\n\nОтправьте новую фотографию:"),
        MessageInput(
            func=on_replace_photo_received,
            content_types=["photo"],
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(states.AdminProfiles.VIEW_PHOTOS),
        ),
        getter=get_replace_photo_data,
        state=states.AdminProfiles.REPLACE_PHOTO,
    ),
)

