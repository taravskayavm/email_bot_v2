import imaplib  # Подключение клиента IMAP для проверки входящей почты.
import os  # Доступ к переменным окружения.
import socket  # Низкоуровневая проверка TCP-подключения и резолвинг адресов.
import smtplib  # Подключение клиента SMTP для проверки исходящей почты.
import ssl  # SSL-контекст для защищённых подключений.

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


def _short_error(exc: Exception) -> str:
    """Возвращает короткое и безопасное описание ошибки."""
    return str(exc).replace("\n", " ").strip()[:100]  # Удаление переводов строки и обрезка сообщения.


def _resolve_host(host: str, port: int, ipv4_only: bool) -> tuple[str, int]:
    """Разрешает хост в IP-адрес с возможностью принудительного IPv4."""
    family = socket.AF_INET if ipv4_only else socket.AF_UNSPEC  # Выбор семейства адресов по настройке.
    addrinfo = socket.getaddrinfo(  # Получение вариантов адресов для подключения по TCP.
        host, port, family, socket.SOCK_STREAM
    )
    if not addrinfo:  # Проверка, что найден хотя бы один адрес.
        raise OSError(f"Не удалось разрешить адрес {host}:{port}")  # Явная ошибка резолвинга.
    sockaddr = addrinfo[0][4]  # Извлечение адреса и порта из первого найденного результата.
    return sockaddr[0], sockaddr[1]  # Возврат IP-адреса и порта.


def _check_tcp(host: str, port: int, timeout: int, ipv4_only: bool) -> tuple[bool, str]:
    """Проверяет TCP-доступность хоста и возвращает краткий статус."""
    try:  # Попытка выполнить TCP-подключение к целевому хосту.
        target_host, target_port = _resolve_host(  # Разрешение доменного имени в IP-адрес.
            host, port, ipv4_only
        )
        with socket.create_connection(  # Установка TCP-соединения с заданным таймаутом.
            (target_host, target_port), timeout=timeout
        ):
            return True, f"ok ({target_host}:{target_port})"  # Успешный статус TCP-подключения.
    except Exception as exc:  # Перехват ошибок DNS, сети или таймаута.
        return False, f"error ({_short_error(exc)})"  # Краткий и безопасный статус ошибки.


def _check_smtp_auth(
    host: str,
    port: int,
    email: str,
    password: str,
    timeout: int,
    ipv4_only: bool,
) -> tuple[bool, str]:
    """Проверяет SMTP-подключение и авторизацию."""
    try:  # Попытка открыть SMTP SSL-сессию и выполнить логин.
        _ = ipv4_only  # Сохранение параметра для совместимости сигнатуры и единого интерфейса.
        context = ssl.create_default_context()  # Создание безопасного SSL-контекста по умолчанию.
        with smtplib.SMTP_SSL(  # Установка защищённого SMTP-соединения.
            host=host, port=port, timeout=timeout, context=context
        ) as server:
            server.login(email, password)  # Проверка SMTP-авторизации указанными учетными данными.
        return True, "ok"  # Успешный статус SMTP-авторизации.
    except Exception as exc:  # Перехват ошибок сети, TLS и авторизации.
        return False, f"error ({_short_error(exc)})"  # Возврат краткой причины сбоя.


def _check_imap_auth(
    host: str,
    port: int,
    email: str,
    password: str,
    timeout: int,
    ipv4_only: bool,
) -> tuple[bool, str]:
    """Проверяет IMAP-подключение и авторизацию."""
    try:  # Попытка открыть IMAP SSL-сессию и выполнить логин.
        target_host, target_port = _resolve_host(  # Разрешение адреса для IMAP-подключения.
            host, port, ipv4_only
        )
        client = imaplib.IMAP4_SSL(  # Создание IMAP SSL-клиента с заданным таймаутом.
            host=target_host, port=target_port, timeout=timeout
        )
        try:  # Вложенный блок для гарантированного закрытия IMAP-сессии.
            client.login(email, password)  # Проверка IMAP-авторизации.
        finally:  # Блок, который выполняется независимо от результата логина.
            client.logout()  # Корректное завершение IMAP-сессии.
        return True, "ok"  # Успешный статус IMAP-авторизации.
    except Exception as exc:  # Перехват ошибок сети, TLS, IMAP-протокола и авторизации.
        return False, f"error ({_short_error(exc)})"  # Возврат краткой причины сбоя.


@router.message(
    lambda message: message.text == "🩺 Диагностика"
)  # Регистрация обработчика кнопки диагностики.
async def diagnostics(message: Message) -> None:
    """Проверяет ENV, SMTP и IMAP, затем отправляет статус каждой проверки."""
    result: list[str] = []  # Список строк с итогами по каждому диагностическому шагу.

    email = os.getenv("EMAIL_ADDRESS")  # Чтение адреса отправителя из ENV.
    password = os.getenv("EMAIL_PASSWORD")  # Чтение пароля отправителя из ENV.
    smtp_host = os.getenv("SMTP_HOST", "")  # Чтение SMTP-хоста из ENV.
    smtp_port = int(os.getenv("SMTP_PORT", "465"))  # Чтение SMTP-порта из ENV с дефолтом.
    smtp_timeout = int(os.getenv("SMTP_TIMEOUT", "10"))  # Чтение таймаута SMTP в секундах.
    imap_host = os.getenv("IMAP_HOST", "")  # Чтение IMAP-хоста из ENV.
    imap_port = int(os.getenv("IMAP_PORT", "993"))  # Чтение IMAP-порта из ENV с дефолтом.
    imap_timeout = int(os.getenv("IMAP_TIMEOUT", "10"))  # Чтение таймаута IMAP в секундах.
    ipv4_only = os.getenv("IMAP_IPV4_ONLY", "0") == "1"  # Флаг принудительного IPv4-режима.

    if email and password and smtp_host and imap_host:  # Проверка, что обязательные параметры заданы.
        result.append("ENV — ok")  # Фиксация успешной проверки ENV.
    else:  # Ветка при отсутствии хотя бы одного обязательного значения.
        result.append("ENV — error")  # Фиксация ошибки конфигурации ENV.
        text = "🩺 Диагностика:\n\n" + "\n".join(result)  # Формирование отчёта только по ENV-проверке.
        await message.answer(text)  # Отправка отчёта и ранний выход при некорректной конфигурации.
        return  # Прекращение дальнейших сетевых проверок.

    smtp_tcp_ok, smtp_tcp_status = _check_tcp(  # Проверка TCP-доступности SMTP-сервера.
        host=smtp_host,
        port=smtp_port,
        timeout=smtp_timeout,
        ipv4_only=ipv4_only,
    )
    result.append(f"TCP:SMTP — {smtp_tcp_status}")  # Добавление статуса TCP-проверки SMTP в отчёт.

    imap_tcp_ok, imap_tcp_status = _check_tcp(  # Проверка TCP-доступности IMAP-сервера.
        host=imap_host,
        port=imap_port,
        timeout=imap_timeout,
        ipv4_only=ipv4_only,
    )
    result.append(f"TCP:IMAP — {imap_tcp_status}")  # Добавление статуса TCP-проверки IMAP в отчёт.

    if smtp_tcp_ok:  # Проверка: есть ли TCP-доступ до SMTP до попытки авторизации.
        _, smtp_auth_status = _check_smtp_auth(  # Проверка SMTP-авторизации.
            host=smtp_host,
            port=smtp_port,
            email=email,
            password=password,
            timeout=smtp_timeout,
            ipv4_only=ipv4_only,
        )
        result.append(f"SMTP AUTH — {smtp_auth_status}")  # Добавление статуса SMTP AUTH в отчёт.
    else:  # Ветка при недоступном SMTP по TCP.
        result.append("SMTP AUTH — skipped")  # Явная отметка пропуска авторизации SMTP.

    if imap_tcp_ok:  # Проверка: есть ли TCP-доступ до IMAP до попытки авторизации.
        _, imap_auth_status = _check_imap_auth(  # Проверка IMAP-авторизации.
            host=imap_host,
            port=imap_port,
            email=email,
            password=password,
            timeout=imap_timeout,
            ipv4_only=ipv4_only,
        )
        result.append(f"IMAP AUTH — {imap_auth_status}")  # Добавление статуса IMAP AUTH в отчёт.
    else:  # Ветка при недоступном IMAP по TCP.
        result.append("IMAP AUTH — skipped")  # Явная отметка пропуска авторизации IMAP.

    text = "🩺 Диагностика:\n\n" + "\n".join(  # Формирование итогового текста отчета.
        result
    )
    await message.answer(text)  # Отправка диагностического отчета пользователю.
