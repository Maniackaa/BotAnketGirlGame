#!/bin/bash

# Скрипт для проверки статуса Telegram бота
# Путь к корневой директории проекта
PROJECT_DIR="/root/BotAnketGirlGame"
# PID файл
PID_FILE="$PROJECT_DIR/bot.pid"
# Лог файл
LOG_FILE="$PROJECT_DIR/bot.log"

echo "=== Статус Telegram бота ==="
echo ""

# Проверяем наличие PID файла
if [ ! -f "$PID_FILE" ]; then
    echo "❌ Бот не запущен (PID файл не найден)"
    exit 1
fi

# Читаем PID
PID=$(cat "$PID_FILE")

# Проверяем, существует ли процесс
if ps -p "$PID" > /dev/null 2>&1; then
    echo "✅ Бот запущен"
    echo "   PID: $PID"
    echo "   Лог файл: $LOG_FILE"
    echo ""
    echo "Последние 10 строк лога:"
    echo "---"
    tail -n 10 "$LOG_FILE" 2>/dev/null || echo "Лог файл пуст или недоступен"
else
    echo "❌ Бот не запущен (процесс с PID $PID не найден)"
    echo "   Удаляем устаревший PID файл..."
    rm -f "$PID_FILE"
    exit 1
fi

