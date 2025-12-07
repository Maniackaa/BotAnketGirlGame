"""Состояния для пользовательских диалогов"""
from aiogram.fsm.state import State, StatesGroup


class UserStart(StatesGroup):
    """Состояния для диалога приветствия"""
    RULES = State()  # Показ правил
    CONFIRMED = State()  # Сообщение о подтверждении правил
    WELCOME = State()  # Приветственное письмо с главным меню


class UserProfiles(StatesGroup):
    """Состояния для просмотра анкет"""
    LIST = State()  # Список анкет (начало просмотра)
    VIEW = State()  # Просмотр конкретной анкеты с фотографиями


class UserBooking(StatesGroup):
    """Состояния для бронирования встречи"""
    CONFIRM_FORMAT = State()  # Подтверждение формата (аудио/видео/приватка)
    SELECT_GAME = State()  # Выбор игры
    INPUT_DATE = State()  # Ввод даты
    INPUT_TIME = State()  # Ввод времени
    INPUT_DURATION = State()  # Ввод продолжительности
    INPUT_PARTICIPANTS = State()  # Ввод количества участников
    CONFIRM_ORDER = State()  # Подтверждение заказа

