"""Диалог управления играми"""
import logging
from typing import List
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
from bot.database.repositories import GameRepository

logger = logging.getLogger(__name__)


async def get_games_data(dialog_manager: DialogManager, **kwargs):
    """Получение списка игр для отображения"""
    async with async_session_maker() as session:
        offset = dialog_manager.dialog_data.get("games_offset", 0)
        games = await GameRepository.get_all(session, limit=10, offset=offset)
        
        return {
            "games": games,
            "has_prev": offset > 0,
            "has_next": len(games) == 10,
            "offset": offset,
        }


async def get_game_detail_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна деталей игры"""
    logger.info(f"[get_game_detail_data] Начало. Текущее состояние: {dialog_manager.current_context().state}")
    game_id = dialog_manager.dialog_data.get("selected_game_id")
    logger.info(f"[get_game_detail_data] game_id = {game_id}")
    
    if not game_id:
        logger.error(f"[get_game_detail_data] ОШИБКА: game_id не найден в dialog_data")
        logger.info(f"[get_game_detail_data] dialog_data keys: {list(dialog_manager.dialog_data.keys())}")
        return {
            "game_name": "Не выбрана",
        }
    
    async with async_session_maker() as session:
        game = await GameRepository.get_by_id(session, game_id)
        if not game:
            logger.error(f"[get_game_detail_data] ОШИБКА: игра с id {game_id} не найдена")
            return {
                "game_name": "Игра не найдена",
            }
        
        # Сохраняем название для окна подтверждения удаления
        dialog_manager.dialog_data["selected_game_name"] = game.name
        logger.info(f"[get_game_detail_data] Игра найдена: {game.name}")
        
        return {
            "game_name": game.name,
        }


async def on_game_select(c: CallbackQuery, button: Button, manager: DialogManager):
    """Выбор игры"""
    logger.info(f"[on_game_select] Начало. Callback data: {c.data}")
    
    # В aiogram_dialog для ListGroup item_id передается через manager.item_id
    item_id = getattr(manager, 'item_id', None)
    logger.info(f"[on_game_select] manager.item_id = {item_id}")
    
    # Fallback: если item_id не найден в manager, пробуем из callback_data
    if item_id is None:
        logger.info(f"[on_game_select] item_id не найден в manager, пробуем callback_data")
        if c.data:
            parts = c.data.split(":")
            logger.info(f"[on_game_select] parts = {parts}")
            if len(parts) >= 3:
                item_id = parts[-1]
            else:
                item_id = parts[-1] if parts else None
        else:
            item_id = button.widget_id.split(":")[-1] if ":" in button.widget_id else None
    
    logger.info(f"[on_game_select] Итоговый item_id = {item_id}")
    
    if not item_id:
        logger.error(f"[on_game_select] ОШИБКА: item_id не найден")
        await c.answer("❌ Ошибка: не удалось получить ID игры", show_alert=True)
        return
    
    try:
        game_id = int(item_id)
        logger.info(f"[on_game_select] game_id = {game_id}")
    except ValueError as e:
        logger.error(f"[on_game_select] ОШИБКА: неверный формат ID. {e}")
        await c.answer("❌ Ошибка: неверный формат ID игры", show_alert=True)
        return
    
    manager.dialog_data["selected_game_id"] = game_id
    logger.info(f"[on_game_select] Переключаемся на DETAIL. Текущее состояние: {manager.current_context().state}")
    await manager.switch_to(states.AdminGames.DETAIL)
    logger.info(f"[on_game_select] Переключились на DETAIL")


async def on_edit_game(c: CallbackQuery, button: Button, manager: DialogManager):
    """Начало редактирования игры"""
    logger.info(f"[on_edit_game] Начало. Текущее состояние: {manager.current_context().state}")
    logger.info(f"[on_edit_game] dialog_data keys: {list(manager.dialog_data.keys())}")
    game_id = manager.dialog_data.get("selected_game_id")
    logger.info(f"[on_edit_game] game_id = {game_id}")
    
    if not game_id:
        logger.error(f"[on_edit_game] ОШИБКА: игра не выбрана. dialog_data: {manager.dialog_data}")
        await c.answer("❌ Игра не выбрана. Выберите игру из списка.", show_alert=True)
        # Переходим к списку игр вместо редактирования
        await manager.switch_to(states.AdminGames.LIST)
        return
    
    # Загружаем данные игры для редактирования
    async with async_session_maker() as session:
        game = await GameRepository.get_by_id(session, game_id)
        if not game:
            logger.error(f"[on_edit_game] ОШИБКА: игра с id {game_id} не найдена")
            await c.answer("❌ Игра не найдена", show_alert=True)
            await manager.switch_to(states.AdminGames.LIST)
            return
        
        manager.dialog_data["edit_game_name"] = game.name
        logger.info(f"[on_edit_game] Загружено название: {game.name}")
    
    logger.info(f"[on_edit_game] Переключаемся на EDIT. Текущее состояние: {manager.current_context().state}")
    await manager.switch_to(states.AdminGames.EDIT)
    logger.info(f"[on_edit_game] Переключились на EDIT")


async def on_edit_game_name(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода нового названия игры"""
    logger.info(f"[on_edit_game_name] Начало. Текущее состояние: {manager.current_context().state}")
    logger.info(f"[on_edit_game_name] Введенный текст: {text}")
    
    if not text or len(text.strip()) < 2:
        logger.warning(f"[on_edit_game_name] Название слишком короткое")
        await message.answer("❌ Название игры должно содержать минимум 2 символа")
        return
    
    game_id = manager.dialog_data.get("selected_game_id")
    logger.info(f"[on_edit_game_name] game_id = {game_id}")
    
    if not game_id:
        logger.error(f"[on_edit_game_name] ОШИБКА: игра не выбрана")
        await message.answer("❌ Ошибка: игра не выбрана")
        return
    
    async with async_session_maker() as session:
        try:
            logger.info(f"[on_edit_game_name] Обновляем игру {game_id} на '{text.strip()}'")
            game = await GameRepository.update(session, game_id, text.strip())
            if game:
                logger.info(f"[on_edit_game_name] Игра успешно обновлена: '{game.name}'")
                await message.answer(f"✅ Игра обновлена: '{game.name}'")
                logger.info(f"[on_edit_game_name] Переключаемся на DETAIL")
                await manager.switch_to(states.AdminGames.DETAIL)
            else:
                logger.error(f"[on_edit_game_name] ОШИБКА: игра не найдена")
                await message.answer("❌ Ошибка: игра не найдена")
        except Exception as e:
            logger.error(f"[on_edit_game_name] ОШИБКА при обновлении: {e}")
            await message.answer(f"❌ Ошибка: {str(e)}")


async def on_delete_confirm(c: CallbackQuery, button: Button, manager: DialogManager):
    """Подтверждение удаления игры"""
    logger.info(f"[on_delete_confirm] Начало. Текущее состояние: {manager.current_context().state}")
    game_id = manager.dialog_data.get("selected_game_id")
    logger.info(f"[on_delete_confirm] game_id = {game_id}")
    
    if not game_id:
        logger.error(f"[on_delete_confirm] ОШИБКА: игра не выбрана")
        await c.answer("❌ Ошибка: игра не выбрана", show_alert=True)
        return
    
    async with async_session_maker() as session:
        logger.info(f"[on_delete_confirm] Удаляем игру {game_id}")
        deleted = await GameRepository.delete(session, game_id)
        if deleted:
            logger.info(f"[on_delete_confirm] Игра успешно удалена")
            await c.answer("✅ Игра удалена")
            logger.info(f"[on_delete_confirm] Переключаемся на LIST")
            await manager.switch_to(states.AdminGames.LIST)
        else:
            logger.error(f"[on_delete_confirm] ОШИБКА при удалении")
            await c.answer("❌ Ошибка при удалении", show_alert=True)


async def on_delete_cancel(c: CallbackQuery, button: Button, manager: DialogManager):
    """Отмена удаления"""
    await manager.switch_to(states.AdminGames.LIST)


async def get_delete_confirm_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для подтверждения удаления"""
    return {
        "game_name": dialog_manager.dialog_data.get("selected_game_name", "")
    }




async def get_edit_game_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна редактирования игры"""
    logger.info(f"[get_edit_game_data] Начало. Текущее состояние: {dialog_manager.current_context().state}")
    game_id = dialog_manager.dialog_data.get("selected_game_id")
    edit_game_name = dialog_manager.dialog_data.get("edit_game_name", "")
    logger.info(f"[get_edit_game_data] game_id = {game_id}, edit_game_name = {edit_game_name}")
    
    if not game_id:
        logger.error(f"[get_edit_game_data] ОШИБКА: game_id не найден в dialog_data")
        logger.info(f"[get_edit_game_data] dialog_data keys: {list(dialog_manager.dialog_data.keys())}")
        logger.info(f"[get_edit_game_data] Перенаправляем на LIST, так как game_id отсутствует")
        # Перенаправляем на LIST, если game_id отсутствует
        # Это делается через обработчик, но getter не может делать switch_to
        # Поэтому просто возвращаем сообщение об ошибке
        return {
            "current_name": "Ошибка: игра не выбрана. Выберите игру из списка.",
        }
    
    return {
        "current_name": edit_game_name,
    }


async def get_add_game_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна добавления игры"""
    return {}


async def get_main_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для главного окна (пустой dict)"""
    # Очищаем старые данные при открытии главного окна
    if "games_offset" in dialog_manager.dialog_data:
        del dialog_manager.dialog_data["games_offset"]
    if "selected_game_id" in dialog_manager.dialog_data:
        del dialog_manager.dialog_data["selected_game_id"]
    if "selected_game_name" in dialog_manager.dialog_data:
        del dialog_manager.dialog_data["selected_game_name"]
    if "edit_game_name" in dialog_manager.dialog_data:
        del dialog_manager.dialog_data["edit_game_name"]
    if "search_query" in dialog_manager.dialog_data:
        del dialog_manager.dialog_data["search_query"]
    return {}


async def get_search_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна поиска (пустой dict)"""
    # Очищаем данные поиска при открытии окна
    if "search_query" in dialog_manager.dialog_data:
        del dialog_manager.dialog_data["search_query"]
    if "search_results" in dialog_manager.dialog_data:
        del dialog_manager.dialog_data["search_results"]
    return {}


async def get_search_results_data(dialog_manager: DialogManager, **kwargs):
    """Получение данных для окна результатов поиска"""
    search_results = dialog_manager.dialog_data.get("search_results", [])
    search_query = dialog_manager.dialog_data.get("search_query", "")
    
    return {
        "games": search_results,
        "search_query": search_query,
        "results_count": len(search_results),
    }


async def on_add_game_name(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка ввода названия игры"""
    if not text or len(text.strip()) < 2:
        await message.answer("❌ Название игры должно содержать минимум 2 символа")
        return
    
    async with async_session_maker() as session:
        try:
            game = await GameRepository.create(session, text.strip())
            await message.answer(f"✅ Игра '{game.name}' добавлена")
            await manager.switch_to(states.AdminGames.LIST)
        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")


async def on_search_query(message: Message, widget: TextInput, manager: DialogManager, text: str):
    """Обработка поиска игр"""
    logger.info(f"[on_search_query] Начало. Поисковый запрос: {text}")
    
    if not text or len(text.strip()) < 1:
        logger.warning(f"[on_search_query] Пустой запрос")
        await message.answer("❌ Введите хотя бы 1 символ для поиска")
        return
    
    search_query = text.strip()
    manager.dialog_data["search_query"] = search_query
    
    async with async_session_maker() as session:
        games = await GameRepository.search(session, search_query)
        logger.info(f"[on_search_query] Найдено игр: {len(games)}")
        
        if not games:
            logger.info(f"[on_search_query] Игры не найдены")
            await message.answer("❌ Игры не найдены")
            return
        
        # Сохраняем результаты поиска для отображения в окне
        manager.dialog_data["search_results"] = games
        logger.info(f"[on_search_query] Сохранили результаты поиска. Переключаемся на SEARCH_RESULTS")
        await manager.switch_to(states.AdminGames.SEARCH_RESULTS)


async def on_prev_page(c: CallbackQuery, button: Button, manager: DialogManager):
    """Переход на предыдущую страницу"""
    offset = manager.dialog_data.get("games_offset", 0)
    if offset >= 10:
        manager.dialog_data["games_offset"] = offset - 10
    await manager.switch_to(states.AdminGames.LIST)


async def on_next_page(c: CallbackQuery, button: Button, manager: DialogManager):
    """Переход на следующую страницу"""
    offset = manager.dialog_data.get("games_offset", 0)
    manager.dialog_data["games_offset"] = offset + 10
    await manager.switch_to(states.AdminGames.LIST)


games_dialog = Dialog(
    Window(
        Const("🎮 <b>Управление играми</b>\n\nВыберите действие:"),
        Column(
            SwitchTo(
                Const("📋 Список игр"),
                id="list",
                state=states.AdminGames.LIST,
            ),
            SwitchTo(
                Const("➕ Добавить игру"),
                id="add",
                state=states.AdminGames.ADD,
            ),
            SwitchTo(
                Const("🔍 Поиск игр"),
                id="search",
                state=states.AdminGames.SEARCH,
            ),
            Cancel(Const("🔙 Назад")),
        ),
        getter=get_main_data,
        state=states.AdminGames.MAIN,
    ),
    
    Window(
        Format("📋 <b>Список игр</b>\n\n"),
        ScrollingGroup(
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
            id="games_scroll",
            width=1,
            height=10,
        ),
        Row(
            Button(
                Const("◀️ Предыдущая"),
                id="prev",
                on_click=on_prev_page,
                when="has_prev",
            ),
            Button(
                Const("Следующая ▶️"),
                id="next",
                on_click=on_next_page,
                when="has_next",
            ),
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(states.AdminGames.MAIN),
        ),
        getter=get_games_data,
        state=states.AdminGames.LIST,
    ),
    
    # Окно деталей игры
    Window(
        Format("🎮 <b>Игра: {game_name}</b>"),
        Column(
            Button(
                Const("✏️ Редактировать"),
                id="edit",
                on_click=on_edit_game,
            ),
            Button(
                Const("🗑️ Удалить"),
                id="delete",
                on_click=lambda c, b, m: m.switch_to(states.AdminGames.DELETE_CONFIRM),
            ),
            Button(
                Const("🔙 Назад"),
                id="back",
                on_click=lambda c, b, m: m.switch_to(states.AdminGames.LIST),
            ),
        ),
        getter=get_game_detail_data,
        state=states.AdminGames.DETAIL,
    ),
    
    Window(
        Const("➕ <b>Добавить игру</b>\n\nВведите название игры:"),
        TextInput(
            id="game_name",
            on_success=on_add_game_name,
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(states.AdminGames.MAIN),
        ),
        getter=get_add_game_data,
        state=states.AdminGames.ADD,
    ),
    
    
    Window(
        Format("❓ <b>Подтверждение удаления</b>\n\nВы уверены, что хотите удалить игру:\n<b>{game_name}</b>?"),
        Row(
            Button(
                Const("✅ Да, удалить"),
                id="confirm_delete",
                on_click=on_delete_confirm,
            ),
            Button(
                Const("❌ Отмена"),
                id="cancel_delete",
                on_click=lambda c, b, m: m.switch_to(states.AdminGames.DETAIL),
            ),
        ),
        getter=get_game_detail_data,
        state=states.AdminGames.DELETE_CONFIRM,
    ),
    
    # Окно редактирования игры
    Window(
        Format("✏️ <b>Редактировать игру</b>\n\nТекущее название: {current_name}\n\nВведите новое название:"),
        TextInput(
            id="edit_game_name",
            on_success=on_edit_game_name,
        ),
        Group(
            Button(
                Const("🔙 Назад"),
                id="back",
                on_click=lambda c, b, m: m.switch_to(states.AdminGames.DETAIL),
            ),
            when=lambda data, widget, manager: manager.dialog_data.get("selected_game_id") is not None,
        ),
        Group(
            Button(
                Const("🔙 К списку игр"),
                id="back_to_list",
                on_click=lambda c, b, m: m.switch_to(states.AdminGames.LIST),
            ),
            when=lambda data, widget, manager: manager.dialog_data.get("selected_game_id") is None,
        ),
        getter=get_edit_game_data,
        state=states.AdminGames.EDIT,
    ),
    
    Window(
        Const("🔍 <b>Поиск игр</b>\n\nВведите название игры для поиска:"),
        TextInput(
            id="search_query",
            on_success=on_search_query,
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(states.AdminGames.MAIN),
        ),
        getter=get_search_data,
        state=states.AdminGames.SEARCH,
    ),
    
    # Окно результатов поиска
    Window(
        Format("🔍 <b>Результаты поиска</b>\n\nЗапрос: <i>{search_query}</i>\nНайдено: {results_count}\n\nВыберите игру:"),
        ScrollingGroup(
            ListGroup(
                Button(
                    Format("{item.name}"),
                    id="game_search_btn",
                    on_click=on_game_select,
                ),
                id="games_search_list",
                item_id_getter=lambda item: str(item.id),
                items="games",
            ),
            id="games_search_scroll",
            width=1,
            height=10,
        ),
        Button(
            Const("🔙 Назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(states.AdminGames.SEARCH),
        ),
        getter=get_search_results_data,
        state=states.AdminGames.SEARCH_RESULTS,
    ),
)

