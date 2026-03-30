import imaplib  # Подключение клиента IMAP для проверки входящей почты.
import os  # Доступ к переменным окружения.
import smtplib  # Подключение клиента SMTP для проверки исходящей почты.

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


@router.message(
    lambda message: message.text == "🩺 Диагностика"
)  # Регистрация обработчика кнопки диагностики.
async def diagnostics(message: Message) -> None:
    """Проверяет ENV, SMTP и IMAP, затем отправляет статус каждой проверки."""
    result: list[str] = []  # Список строк с итогами по каждому диагностическому шагу.

    email = os.getenv("EMAIL_ADDRESS")  # Чтение адреса отправителя из ENV.
    password = os.getenv("EMAIL_PASSWORD")  # Чтение пароля отправителя из ENV.

    if email and password:  # Проверка, что обязательные учетные данные заданы.
        result.append("ENV — ok")  # Фиксация успешной проверки ENV.
    else:  # Ветка при отсутствии хотя бы одного обязательного значения.
        result.append("ENV — error")  # Фиксация ошибки конфигурации ENV.

    try:  # Блок безопасной проверки SMTP-подключения и логина.
        smtp_host = os.getenv("SMTP_HOST")  # Чтение SMTP-хоста из ENV.
        smtp_port = int(os.getenv("SMTP_PORT", 465))  # Приведение SMTP-порта к числу.

        server = smtplib.SMTP_SSL(  # Создание SSL-подключения к SMTP-серверу.
            smtp_host, smtp_port, timeout=10
        )
        server.login(email, password)  # Проверка авторизации SMTP-учетных данных.
        server.quit()  # Явное закрытие SMTP-сессии после проверки.

        result.append("SMTP — ok")  # Фиксация успешной проверки SMTP.
    except Exception as exc:  # Перехват любых ошибок сети, авторизации или конфигурации.
        result.append(
            f"SMTP — error ({str(exc)[:80]})"
        )  # Фиксация ошибки SMTP с краткой причиной.

    try:  # Блок безопасной проверки IMAP-подключения и логина.
        imap_host = os.getenv("IMAP_HOST")  # Чтение IMAP-хоста из ENV.
        imap_port = int(os.getenv("IMAP_PORT", 993))  # Приведение IMAP-порта к числу.

        mail = imaplib.IMAP4_SSL(  # Создание SSL-подключения к IMAP-серверу.
            imap_host, imap_port
        )
        mail.login(email, password)  # Проверка авторизации IMAP-учетных данных.
        mail.logout()  # Явное завершение IMAP-сессии после проверки.

        result.append("IMAP — ok")  # Фиксация успешной проверки IMAP.
    except Exception as exc:  # Перехват любых ошибок сети, авторизации или конфигурации.
        result.append(
            f"IMAP — error ({str(exc)[:80]})"
        )  # Фиксация ошибки IMAP с краткой причиной.

    text = "🩺 Диагностика:\n\n" + "\n".join(  # Формирование итогового текста отчета.
        result
    )
    await message.answer(text)  # Отправка диагностического отчета пользователю.
