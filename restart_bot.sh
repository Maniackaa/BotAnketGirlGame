#!/bin/bash

# Скрипт для перезапуска Telegram бота
# Путь к корневой директории проекта
PROJECT_DIR="/root/BotAnketGirlGame"

echo "Перезапуск бота..."

# Останавливаем бота
"$PROJECT_DIR/stop_bot.sh"

# Ждем немного перед запуском
sleep 2

# Запускаем бота
"$PROJECT_DIR/start_bot.sh"

