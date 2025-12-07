# Управление ботом как демоном

Созданы скрипты для запуска бота в фоновом режиме на Linux сервере.

## Файлы

- `start_bot.sh` - Запуск бота в фоновом режиме
- `stop_bot.sh` - Остановка бота
- `restart_bot.sh` - Перезапуск бота
- `status_bot.sh` - Проверка статуса бота

## Настройка

1. Убедитесь, что пути в скриптах соответствуют вашей системе:
   - Корневая директория: `/root/BotAnketGirlGame`
   - Виртуальное окружение: `/root/BotAnketGirlGame/venv`

2. Сделайте скрипты исполняемыми:
   ```bash
   chmod +x start_bot.sh
   chmod +x stop_bot.sh
   chmod +x restart_bot.sh
   chmod +x status_bot.sh
   ```

## Использование

### Запуск бота
```bash
./start_bot.sh
```

### Остановка бота
```bash
./stop_bot.sh
```

### Перезапуск бота
```bash
./restart_bot.sh
```

### Проверка статуса
```bash
./status_bot.sh
```

## Логи

Логи бота сохраняются в файл: `/root/BotAnketGirlGame/bot.log`

Для просмотра логов в реальном времени:
```bash
tail -f /root/BotAnketGirlGame/bot.log
```

## PID файл

PID процесса сохраняется в: `/root/BotAnketGirlGame/bot.pid`

Это позволяет скриптам проверять, запущен ли бот, и корректно его останавливать.

## Автозапуск при перезагрузке сервера

Для автоматического запуска бота при перезагрузке сервера добавьте в `/etc/rc.local`:

```bash
#!/bin/bash
/root/BotAnketGirlGame/start_bot.sh
exit 0
```

Или создайте systemd service (рекомендуется):

```bash
sudo nano /etc/systemd/system/bot.service
```

Содержимое файла:
```ini
[Unit]
Description=Telegram Bot AnketGirlGame
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/BotAnketGirlGame
Environment="PATH=/root/BotAnketGirlGame/venv/bin"
ExecStart=/root/BotAnketGirlGame/venv/bin/python /root/BotAnketGirlGame/bot/main.py
Restart=always
RestartSec=10
StandardOutput=append:/root/BotAnketGirlGame/bot.log
StandardError=append:/root/BotAnketGirlGame/bot.log

[Install]
WantedBy=multi-user.target
```

Затем:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bot.service
sudo systemctl start bot.service
```

Проверка статуса:
```bash
sudo systemctl status bot.service
```

