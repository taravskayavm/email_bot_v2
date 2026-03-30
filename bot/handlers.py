from aiogram import Router  # Маршрутизация входящих событий.
from aiogram.filters import CommandStart  # Фильтр для команды /start.
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup  # Типы Telegram API.


router = Router()  # Создание роутера обработчиков.


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Формирует главное меню бота."""
    keyboard = ReplyKeyboardMarkup(  # Создание клавиатуры ответа.
        keyboard=[
            [KeyboardButton(text="Массовая рассылка")],  # Кнопка массовой рассылки.
            [KeyboardButton(text="Ручная рассылка")],  # Кнопка ручной рассылки.
            [KeyboardButton(text="🩺 Диагностика")],  # Кнопка диагностики.
            [KeyboardButton(text="Стоп")],  # Кнопка остановки.
        ],
        resize_keyboard=True,  # Автоподгонка размеров клавиатуры.
    )
    return keyboard  # Возврат собранной клавиатуры.


@router.message(CommandStart())  # Регистрация обработчика команды /start.
async def cmd_start(message: Message) -> None:
    """Обрабатывает команду /start и показывает основное меню."""
    await message.answer(  # Отправка приветственного сообщения.
        "Бот запущен.\nВыберите действие:",  # Текст сообщения пользователю.
        reply_markup=get_main_keyboard(),  # Подключение клавиатуры к сообщению.
    )
