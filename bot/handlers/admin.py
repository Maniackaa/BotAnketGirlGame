"""Хендлеры для админ-панели"""
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode
from aiogram.fsm.context import FSMContext

from bot.filters.admin import AdminFilter
from bot.dialogs.admin.states import AdminMenu

logger = logging.getLogger(__name__)
router = Router(name="admin")


@router.message(Command("admin"), AdminFilter())
async def cmd_admin(message: Message, dialog_manager: DialogManager, state: FSMContext):
    """Команда для запуска админ-панели"""
    logger.info(f"[cmd_admin] Команда /admin получена. Текущее состояние: {await state.get_state()}")
    
    # Закрываем все текущие диалоги перед открытием нового
    try:
        await dialog_manager.done()
        logger.info("[cmd_admin] Активные диалоги закрыты")
    except Exception as e:
        # Если диалог не активен, игнорируем ошибку
        logger.debug(f"[cmd_admin] Ошибка при закрытии диалога (возможно, диалог не активен): {e}")
        pass
    
    # Очищаем состояние FSM
    try:
        await state.clear()
        logger.info("[cmd_admin] Состояние FSM очищено")
    except Exception as e:
        logger.warning(f"[cmd_admin] Ошибка при очистке состояния FSM: {e}")
    
    # Открываем админ-панель с очисткой стека
    await dialog_manager.start(
        state=AdminMenu.MAIN,
        mode=StartMode.RESET_STACK,
    )
    logger.info("[cmd_admin] Админ-панель запущена")

