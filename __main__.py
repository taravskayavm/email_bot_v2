import asyncio  # Асинхронный запуск.

from bot.main import main  # Импорт основной функции.


if __name__ == "__main__":  # Точка входа при запуске модуля.
    asyncio.run(main())  # Запуск основной асинхронной функции.
