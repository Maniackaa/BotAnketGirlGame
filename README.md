# Telegram Bot - Xplay (AnketGirlGame)

Telegram бот для платформы Xplay на базе aiogram-dialog.

## Структура проекта

```
BotAnketGirlGame/
├── bot/
│   ├── __init__.py
│   ├── main.py                 # Точка входа
│   ├── config.py               # Конфигурация
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy модели
│   │   ├── database.py         # Подключение к БД
│   │   └── repositories.py     # Репозитории для работы с БД
│   ├── dialogs/
│   │   ├── __init__.py
│   │   ├── user/
│   │   │   ├── __init__.py
│   │   │   ├── start.py        # Старт, правила
│   │   │   ├── main_menu.py    # Главное меню
│   │   │   ├── profiles.py     # Просмотр анкет
│   │   │   ├── booking.py      # Бронирование
│   │   │   └── cabinet.py      # Личный кабинет
│   │   └── admin/
│   │       ├── __init__.py
│   │       ├── menu.py         # Админ меню
│   │       ├── profiles.py     # Управление анкетами
│   │       ├── games.py        # Управление играми
│   │       └── orders.py       # Управление заказами
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── errors.py           # Обработка ошибок
│   │   └── support.py          # Обработка чата с админом
│   ├── services/
│   │   ├── __init__.py
│   │   ├── notifications.py    # Уведомления
│   │   ├── reminders.py        # Напоминания
│   │   └── payment.py           # Расчет стоимости
│   ├── filters/
│   │   ├── __init__.py
│   │   └── admin.py            # Фильтр для админов
│   └── utils/
│       ├── __init__.py
│       ├── validators.py       # Валидация данных
│       └── formatters.py       # Форматирование сообщений
├── data/                       # Данные (БД, медиа)
│   └── .gitkeep
├── .env.example                # Пример переменных окружения
├── requirements.txt            # Зависимости
└── README.md
```

## Основные компоненты

### Пользовательские диалоги
- **start.py** - Правила, приветствие
- **main_menu.py** - Главное меню (анкеты, кабинет)
- **profiles.py** - Просмотр анкет (по фото/играм)
- **booking.py** - Бронирование встреч
- **cabinet.py** - Личный кабинет, заказы

### Админские диалоги
- **menu.py** - Админ меню
- **profiles.py** - CRUD анкет
- **games.py** - Управление играми
- **orders.py** - Управление заказами

### Сервисы
- **notifications.py** - Уведомления админу о заказах
- **reminders.py** - Напоминания за 15 минут до встречи
- **payment.py** - Расчет стоимости заказов

## База данных

Модели:
- User (пользователи)
- Profile (анкеты девушек)
- Game (игры)
- Order (заказы)
- ProfileGame (связь анкет и игр)

## Установка

1. Установить зависимости: `pip install -r requirements.txt`
2. Настроить `.env` файл
3. Запустить: `python -m bot.main`

