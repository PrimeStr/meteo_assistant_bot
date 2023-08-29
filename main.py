import asyncio
import os
import ssl

from aiogram import types
from aiogram.utils.exceptions import ChatNotFound, ChatIdIsEmpty, BotBlocked
from aiohttp import web
from dotenv import load_dotenv

import handlers
from bot import bot, dp
from logger import logger

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST')
WEBHOOK_PORT = os.getenv('WEBHOOK_PORT')

# Путь к SSL сертификату.
WEBHOOK_SSL_CERT = './webhook_certificates/webhook_cert.pem'
# Путь к приватному ключу SSL.
WEBHOOK_SSL_PRIV = './webhook_certificates/webhook_pkey.pem'

# Инициализация SSL контекста
# ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
# ssl_context.load_cert_chain(certfile=WEBHOOK_SSL_CERT, keyfile=WEBHOOK_SSL_PRIV)

app = web.Application()


async def on_startup(*args) -> None:
    """Функция, запускащаяся при старте бота.

    Отправляет администратору сообщение об успешном запуске.
    """
    logger.debug('Отправляем сообщение о старте бота администратору')
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text="Бот запущен!")


async def on_shutdown(*args):
    """Функция, запускащаяся при завершении работы бота.

    Отправляет администратору сообщение об остановке, снимает вебхук и
    завершает сессию.
    """
    logger.warning('Завершаем работу бота..')

    logger.debug('Отправляем сообщение об остановке бота администратору')
    await bot.send_message(chat_id=ADMIN_CHAT_ID, text="Bot is shutting down")

    logger.debug('Снимаем вебхук')
    await bot.delete_webhook()

    logger.debug('Завершаем сессию')
    await bot.session.close()


async def webhook_handler(request):
    """Функция установки вебхука и """
    if request.match_info.get('token') == API_TOKEN:
        request_body_dict = await request.json()
        update = types.Update(**request_body_dict)
        await dp.process_update(update)
        return web.Response()
    else:
        return web.Response(status=403)


async def main() -> None:
    """Основная логика для запуска webhook."""
    try:
        # Раскомментировать строки с пометкой #WEBHOOK, если запуск бота ;
        # Производится через webhook. Аналогично, если запуск производится ;
        # Через polling - раскомментировать строку с пометкой #POLLING.

        #WEBHOOK app.router.add_post('/{token}', webhook_handler)
        await on_startup()
        #WEBHOOK app.on_startup.append(on_startup)
        #WEBHOOK app.on_shutdown.append(on_shutdown)
        #WEBHOOK web.run_app(app, host=WEBHOOK_HOST,
        #WEBHOOK             port=WEBHOOK_PORT, ssl_context=ssl_context)

    except ChatNotFound as chat_nf_error:
        msg_error = f'Пользователь с таким Chat_ID не найден! {chat_nf_error}'
        logger.error(msg_error)

    except ChatIdIsEmpty as chat_id_error:
        msg_error = (f'Для ADMIN_CHAT_ID в '
                     f'.env файле не задано значение! {chat_id_error}')
        logger.error(msg_error)

    except BotBlocked as bot_blocked_error:
        msg_error = f'Бот заблокирован администратором! {bot_blocked_error}'
        logger.error(msg_error)

    except Exception as error:
        msg_error = (f'Ошибка отправки сообщения '
                     f'о состоянии бота администратору! {error}')
        logger.error(msg_error)


if __name__ == "__main__":

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    # Раскомментировать строку если бот запускается через polling.
    # loop.run_until_complete(dp.start_polling())
