"""Пользовательские диалоги"""
from bot.dialogs.user.start import start_dialog
from bot.dialogs.user.profiles import profiles_dialog
from bot.dialogs.user.booking import booking_dialog


def get_user_dialogs():
    """Получить все пользовательские диалоги"""
    return [
        start_dialog,
        profiles_dialog,
        booking_dialog,
    ]

