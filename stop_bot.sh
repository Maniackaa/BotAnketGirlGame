#!/bin/bash

# Скрипт для остановки Telegram бота
# Путь к корневой директории проекта
PROJECT_DIR="/root/BotAnketGirlGame"
# PID файл
PID_FILE="$PROJECT_DIR/bot.pid"

# Проверяем наличие PID файла
if [ ! -f "$PID_FILE" ]; then
    echo "PID файл не найден. Бот, возможно, не запущен."
    exit 1
fi

# Читаем PID
PID=$(cat "$PID_FILE")

# Проверяем, существует ли процесс
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "Процесс с PID $PID не найден. Удаляем PID файл."
    rm -f "$PID_FILE"
    exit 1
fi

# Останавливаем процесс
echo "Останавливаем бота (PID: $PID)..."
kill "$PID"

# Ждем завершения процесса (максимум 10 секунд)
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo "Бот успешно остановлен"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# Если процесс не остановился, принудительно завершаем
echo "Процесс не остановился, принудительное завершение..."
kill -9 "$PID" 2>/dev/null
rm -f "$PID_FILE"
echo "Бот принудительно остановлен"

