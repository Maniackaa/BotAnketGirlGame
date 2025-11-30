"""Админские диалоги"""
from bot.dialogs.admin.menu import admin_menu_dialog
from bot.dialogs.admin.games import games_dialog
from bot.dialogs.admin.profiles import profiles_dialog
from bot.dialogs.admin.orders import orders_dialog

__all__ = [
    "admin_menu_dialog",
    "games_dialog",
    "profiles_dialog",
    "orders_dialog",
]


def get_admin_dialogs():
    """Получить все админские диалоги"""
    return [
        admin_menu_dialog,
        games_dialog,
        profiles_dialog,
        orders_dialog,
    ]

