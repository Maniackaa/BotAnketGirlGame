"""Админское меню"""
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Row, Column
from aiogram_dialog import StartMode
from aiogram.types import CallbackQuery

from bot.dialogs.admin import states


async def on_profiles_click(c: CallbackQuery, button: Button, manager):
    """Переход к управлению анкетами"""
    from bot.dialogs.admin.states import AdminProfiles
    await manager.start(AdminProfiles.MAIN, mode=StartMode.NORMAL)


async def on_games_click(c: CallbackQuery, button: Button, manager):
    """Переход к управлению играми"""
    from bot.dialogs.admin.states import AdminGames
    await manager.start(AdminGames.MAIN, mode=StartMode.NORMAL)


async def on_orders_click(c: CallbackQuery, button: Button, manager):
    """Переход к управлению заказами"""
    from bot.dialogs.admin.states import AdminOrders
    await manager.start(AdminOrders.MAIN, mode=StartMode.NORMAL)


admin_menu_dialog = Dialog(
    Window(
        Const("🔧 <b>Админ-панель</b>\n\nВыберите раздел:"),
        Column(
            Button(
                Const("👤 Список анкет"),
                id="profiles",
                on_click=on_profiles_click,
            ),
            Button(
                Const("🎮 Игры"),
                id="games",
                on_click=on_games_click,
            ),
            Button(
                Const("📋 Заказы"),
                id="orders",
                on_click=on_orders_click,
            ),
        ),
        state=states.AdminMenu.MAIN,
    ),
)

