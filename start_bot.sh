#!/bin/bash

# Скрипт для запуска Telegram бота как демона
# Путь к корневой директории проекта
PROJECT_DIR="/root/BotAnketGirlGame"
# Путь к виртуальному окружению
VENV_DIR="$PROJECT_DIR/venv"
# Путь к лог-файлу
LOG_FILE="$PROJECT_DIR/bot.log"
# PID файл
PID_FILE="$PROJECT_DIR/bot.pid"

# Переходим в директорию проекта
cd "$PROJECT_DIR" || exit 1

# Проверяем, не запущен ли уже бот
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "Бот уже запущен (PID: $OLD_PID)"
        exit 1
    else
        echo "Удаляем устаревший PID файл"
        rm -f "$PID_FILE"
    fi
fi

# Активируем виртуальное окружение и запускаем бота
source "$VENV_DIR/bin/activate"

# Запускаем бота в фоновом режиме
nohup python bot/main.py > "$LOG_FILE" 2>&1 &

# Сохраняем PID процесса
echo $! > "$PID_FILE"

echo "Бот запущен (PID: $(cat $PID_FILE))"
echo "Логи сохраняются в: $LOG_FILE"
echo "Для остановки используйте: ./stop_bot.sh"

