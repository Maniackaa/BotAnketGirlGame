"""Точка входа для запуска бота"""
import asyncio
import logging
from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN
from bot.handlers import admin as admin_handlers
from bot.dialogs.admin import get_admin_dialogs
from bot.dialogs.user import get_user_dialogs
from aiogram_dialog import setup_dialogs, DialogManager, StartMode
from aiogram_dialog.api.exceptions import UnknownIntent
from aiogram.types import ErrorEvent
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import BaseFilter
from bot.database.database import init_db, close_db, async_session_maker
from bot.dialogs.admin.states import AdminMenu
from bot.dialogs.user.states import UserStart

# Закомментированные импорты для будущего использования
# from bot.services.reminders import ReminderService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создаем роутер для хендлеров
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, dialog_manager: DialogManager):
    """Обработчик команды /start - запуск диалога приветствия"""
    logger.info(f"[cmd_start] Команда /start от пользователя {message.from_user.id}")
    
    # Закрываем все текущие диалоги перед открытием нового
    try:
        await dialog_manager.done()
        logger.info("[cmd_start] Активные диалоги закрыты")
    except Exception as e:
        logger.debug(f"[cmd_start] Ошибка при закрытии диалога (возможно, диалог не активен): {e}")
        pass
    
    # Открываем диалог приветствия с передачей данных через data
    user_name = message.from_user.first_name or "Пользователь"
    await dialog_manager.start(
        state=UserStart.RULES,
        mode=StartMode.RESET_STACK,
        data={"user_name": user_name},
    )
    # После запуска диалога данные из data автоматически попадают в dialog_data
    # Но на всякий случай сохраняем их явно
    try:
        if "user_name" not in dialog_manager.dialog_data:
            dialog_manager.dialog_data["user_name"] = user_name
            logger.info(f"[cmd_start] Сохранено user_name = {user_name} в dialog_data")
    except Exception as e:
        logger.warning(f"[cmd_start] Не удалось сохранить user_name в dialog_data: {e}")
    logger.info("[cmd_start] Диалог приветствия запущен")


class ExceptionTypeFilter(BaseFilter):
    """Фильтр для проверки типа исключения"""
    def __init__(self, exception_type):
        self.exception_type = exception_type
    
    async def __call__(self, event: ErrorEvent) -> bool:
        return isinstance(event.exception, self.exception_type)


async def on_unknown_intent(event: ErrorEvent, dialog_manager: DialogManager):
    """Обработчик для старых интентов (кнопок из закрытых диалогов)"""
    logger.warning("Перезапуск диалога из-за UnknownIntent: %s", event.exception)
    
    # Получаем информацию о пользователе
    user = None
    if event.update.callback_query:
        user = event.update.callback_query.from_user
        await event.update.callback_query.answer(
            "⚠️ Это меню устарело. Открываю новое меню...",
        )
        if event.update.callback_query.message:
            try:
                await event.update.callback_query.message.delete()
            except TelegramBadRequest:
                pass  # Сообщение уже удалено или недоступно
    elif event.update.message:
        user = event.update.message.from_user
        await event.update.message.answer(
            "⚠️ Это меню устарело. Открываю новое меню...",
        )
    
    # Закрываем все текущие диалоги
    try:
        await dialog_manager.done()
        logger.info("[on_unknown_intent] Активные диалоги закрыты")
    except Exception as e:
        logger.debug(f"[on_unknown_intent] Ошибка при закрытии диалога: {e}")
    
    # Открываем стартовый диалог пользователя
    if user:
        user_name = user.first_name or "Пользователь"
        await dialog_manager.start(
            state=UserStart.RULES,
            mode=StartMode.RESET_STACK,
            data={"user_name": user_name},
        )
        logger.info(f"[on_unknown_intent] Стартовый диалог запущен для пользователя {user.id}")
    else:
        logger.warning("[on_unknown_intent] Не удалось получить информацию о пользователе")


async def main():
    """Основная функция запуска бота"""
    # Инициализация бота и диспетчера
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Инициализация базы данных
    await init_db()
    logger.info("База данных инициализирована")
    
    # Регистрация роутера с командой /start
    dp.include_router(router)
    logger.info("Базовые хендлеры зарегистрированы")
    
    # Регистрация админских хендлеров ПЕРЕД диалогами
    # Это важно, чтобы команда /admin обрабатывалась первой
    dp.include_router(admin_handlers.router)
    logger.info("Админские хендлеры зарегистрированы")
    
    # Регистрация админских диалогов
    for dialog in get_admin_dialogs():
        dp.include_router(dialog)
    logger.info("Админские диалоги зарегистрированы")
    
    # Регистрация пользовательских диалогов
    for dialog in get_user_dialogs():
        dp.include_router(dialog)
    logger.info("Пользовательские диалоги зарегистрированы")
    
    # Настройка диалогов (вызывается один раз после регистрации всех диалогов)
    setup_dialogs(dp)
    logger.info("Диалоги настроены")
    
    # Регистрация обработчика ошибок для UnknownIntent
    dp.errors.register(
        on_unknown_intent,
        ExceptionTypeFilter(UnknownIntent),
    )
    logger.info("Обработчик UnknownIntent зарегистрирован")
    
    # Закомментированная инициализация для будущего использования
    # reminder_service = ReminderService(bot)
    # async with async_session_maker() as session:
    #     await reminder_service.initialize(session)
    # logger.info("ReminderService инициализирован")
    
    try:
        logger.info("Бот запущен")
        await dp.start_polling(bot)
    finally:
        # Закомментированная очистка для будущего использования
        # if reminder_service:
        #     reminder_service.shutdown()
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

