"""Тестовый запуск бота для проверки ошибок"""
import sys
import traceback

try:
    print("Импорт модулей...")
    from bot.main import main
    import asyncio
    print("Модули импортированы успешно")
    print("Запуск бота...")
    asyncio.run(main())
except Exception as e:
    print(f"ОШИБКА: {type(e).__name__}: {e}")
    traceback.print_exc()
    sys.exit(1)

