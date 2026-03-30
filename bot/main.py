import asyncio  # Асинхронный запуск приложения.
import logging  # Логирование событий бота.
import os  # Работа с переменными окружения.

from aiogram import Bot, Dispatcher  # Ядро бота.
from aiogram.types import BotCommand  # Описание команд в меню Telegram.
from dotenv import load_dotenv  # Загрузка переменных из файла .env.

from bot.handlers import router  # Подключение обработчиков.


load_dotenv()  # Загрузка переменных окружения из .env.

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Получение токена бота из окружения.

if not TOKEN:  # Проверка наличия токена.
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set")  # Ошибка при отсутствии токена.


async def set_commands(bot: Bot) -> None:
    """Устанавливает команды бота в Telegram-клиенте."""
    await bot.set_my_commands(  # Установка списка доступных команд.
        [
            BotCommand(command="start", description="Запуск бота"),  # Команда запуска.
        ]
    )


async def main() -> None:
    """Инициализирует и запускает Telegram-бота через polling."""
    logging.basicConfig(level=logging.INFO)  # Настройка базового логирования.

    bot = Bot(token=TOKEN)  # Создание экземпляра бота.
    dispatcher = Dispatcher()  # Создание диспетчера событий.

    dispatcher.include_router(router)  # Подключение роутера обработчиков.

    await set_commands(bot)  # Регистрация команд в Telegram.

    await dispatcher.start_polling(bot)  # Запуск polling.


if __name__ == "__main__":  # Запуск файла как скрипта.
    asyncio.run(main())  # Старт асинхронного цикла.
