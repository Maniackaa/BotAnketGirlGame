"""Состояния для админских диалогов"""
from aiogram.fsm.state import State, StatesGroup


class AdminMenu(StatesGroup):
    MAIN = State()


class AdminGames(StatesGroup):
    MAIN = State()
    LIST = State()
    ADD = State()
    EDIT = State()
    DETAIL = State()
    DELETE = State()
    DELETE_CONFIRM = State()
    SEARCH = State()
    SEARCH_RESULTS = State()


class AdminProfiles(StatesGroup):
    MAIN = State()
    LIST = State()
    ADD = State()
    EDIT = State()
    EDIT_MENU = State()
    DETAIL = State()
    DELETE = State()
    DELETE_CONFIRM = State()
    ADD_NAME = State()
    ADD_AGE = State()
    ADD_DESCRIPTION = State()
    ADD_GAMES = State()
    ADD_AUDIO_PRICE = State()
    ADD_VIDEO_PRICE = State()
    ADD_PRIVATE_PRICE = State()
    ADD_CHANNEL = State()
    ADD_PHOTOS = State()
    CONFIRM_ADD = State()
    EDIT_NAME = State()
    EDIT_AGE = State()
    EDIT_DESCRIPTION = State()
    EDIT_GAMES = State()
    EDIT_AUDIO_PRICE = State()
    EDIT_VIDEO_PRICE = State()
    EDIT_PRIVATE_PRICE = State()
    EDIT_CHANNEL = State()
    EDIT_PHOTOS = State()
    VIEW_PHOTOS = State()
    REPLACE_PHOTO = State()


class AdminOrders(StatesGroup):
    MAIN = State()
    LIST = State()
    DETAIL = State()
    CHANGE_DATETIME = State()
    CHANGE_PAYMENT_STATUS = State()
    ADD_CONFERENCE_LINK = State()
    CANCEL = State()
    MESSAGE_USER = State()
    MESSAGE_GIRL = State()

