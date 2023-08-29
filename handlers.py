from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import (InlineKeyboardMarkup, CallbackQuery,
                           InlineKeyboardButton, Message, ContentType)
from aiogram.utils.exceptions import BotBlocked

from bot import bot, dp
from logger import logger
from weather.weather_hints import get_hint
from weather.weather_messages import get_message
from weather.weather_service import (get_weather_for_city,
                                     get_weather_for_location,
                                     WEATHER_FOR_LOC_FAILED_MESSAGE)

GREETINGS_TEXT = ('Привет! Я ваш личный метеорологический помощник.\nМогу '
                  'предоставить вам текущий прогноз погоды как по городу, '
                  'так и по геолокации.\n\nПросто нажмите на нужную кнопку '
                  'в меню, после чего отправьте мне название города или свою '
                  'геопозицию, и я поделюсь с вами актуальной информацией '
                  'о погоде.\n\nПопробуйте и узнайте, какая погода вас '
                  'ожидает! 🌦️🌤️')
MENU_TEXT = (f'🌦️ Приветствую в метео-меню 🌧️\n\n'
             f'Как вы хотите получить прогноз погоды?\n'
             f'🏙️ Выберите "Погода по городу" для ввода названия города.\n'
             f'🌐 Или выберите "Погода по геолокации" для '
             f'использования вашей текущей геопозиции.\n\n'
             f'Просто нажмите на одну из кнопок ниже и начнем! ⬇️')
START_GET_WEATHER_TEXT = (f'Введите название города '
                          f'для получения текущей погоды:')
START_GET_WEATHER_IN_LOC_TEXT = (f'Отправьте вашу геолокацию для '
                                 f'получения текущей погоды:')
CANCEL_TEXT = 'Вы вернулись в меню!\n\n' + MENU_TEXT
UNKNOWN_COMMAND_TEXT = (f'Я не знаю такой команды.\nНажав на кнопку ниже вы '
                        f'сможете воспользоваться всем моим функционалом. ⬇️')


class WaitingForCityInput(StatesGroup):
    city = State()


class WaitingForLocationInput(StatesGroup):
    location = State()


@dp.message_handler(commands=['start'])
async def start(message: Message) -> None:
    """
    Обработчик команды /start. Отправляет приветствие пользователю.

    Параметры:
        message (Message): Объект сообщения.
    """
    keyboard = InlineKeyboardMarkup()
    button_menu = InlineKeyboardButton('Меню', callback_data='menu')
    keyboard.row(button_menu)

    await bot.send_message(chat_id=message.chat.id, text=GREETINGS_TEXT,
                           reply_markup=keyboard)


# Обработчик для кнопки "Меню"
@dp.callback_query_handler(lambda c: c.data == 'menu')
@dp.message_handler(commands=['menu'])
async def start_menu(message: Message or CallbackQuery) -> None:
    """
    Обработчик кнопки "Меню". Отправляет меню с выбором типа прогноза погоды.

    Параметры:
        message (Message or CallbackQuery): Объект сообщения или коллбэка.
    """
    keyboard = InlineKeyboardMarkup()
    btn_city_weather = InlineKeyboardButton('Погода по городу',
                                            callback_data='weather_in_city')
    btn_loc_weather = InlineKeyboardButton(
        'Погода по геолокации',
        callback_data='weather_from_location'
    )
    keyboard.row(btn_city_weather)
    keyboard.row(btn_loc_weather)

    if type(message) == CallbackQuery:
        await bot.edit_message_reply_markup(message.message.chat.id,
                                            message.message.message_id,
                                            reply_markup=None)

    await bot.send_message(message.from_user.id,
                           text=MENU_TEXT,
                           reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == 'weather_in_city')
async def start_get_weather_in_city_callback(
        callback_query: CallbackQuery) -> None:
    """
    Обработчик кнопки "Погода по городу". Запускает процесс
    получения погоды по городу.

    Параметры:
        callback_query (CallbackQuery): Объект коллбэка.
    """
    keyboard = InlineKeyboardMarkup()
    button_cancel = InlineKeyboardButton('Отмена', callback_data='cancel')
    keyboard.row(button_cancel)

    await callback_query.answer()
    sent_message = await callback_query.message.edit_text(
        START_GET_WEATHER_TEXT,
        reply_markup=keyboard)

    # Сохраняем message_id чтобы потом удалить предыдущее сообщение бота.
    state = dp.current_state(chat=callback_query.from_user.id)
    await state.update_data(last_message_id=sent_message.message_id)

    await WaitingForCityInput.city.set()


@dp.callback_query_handler(lambda c: c.data == 'weather_from_location')
async def start_get_weather_from_location_callback(
        callback_query: CallbackQuery) -> None:
    """
    Обработчик кнопки "Погода по геолокации". Запускает процесс
    получения погоды по геолокации.

    Параметры:
        callback_query (CallbackQuery): Объект коллбэка.
    """
    keyboard = InlineKeyboardMarkup()
    button_cancel = InlineKeyboardButton('Отмена', callback_data='cancel')
    keyboard.row(button_cancel)

    await callback_query.answer()
    sent_message = await callback_query.message.edit_text(
        START_GET_WEATHER_IN_LOC_TEXT,
        reply_markup=keyboard)

    # Сохраняем message_id чтобы потом удалить предыдущее сообщение бота.
    state = dp.current_state(chat=callback_query.from_user.id)
    await state.update_data(last_message_id=sent_message.message_id)

    await WaitingForLocationInput.location.set()


@dp.callback_query_handler(lambda c: c.data == 'cancel', state='*')
async def cancel_handler(callback_query: CallbackQuery,
                         state: FSMContext) -> None:
    """
    Обработчик кнопки "Отмена". Отменяет текущий запрос и возвращает в меню.

    Параметры:
        callback_query (CallbackQuery): Объект коллбэка.

        state (FSMContext): Объект для управления состоянием бота.
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    keyboard = InlineKeyboardMarkup()
    button_city_weather = InlineKeyboardButton(
        'Погода по городу',
        callback_data='weather_in_city'
    )
    button_loc_weather = InlineKeyboardButton(
        'Погода по геолокации',
        callback_data='weather_from_location'
    )
    keyboard.row(button_city_weather)
    keyboard.row(button_loc_weather)

    await state.finish()

    await callback_query.answer('Действие отменено')
    await callback_query.message.edit_text(CANCEL_TEXT, reply_markup=keyboard)


@dp.message_handler(state=WaitingForCityInput.city)
async def get_weather_in_city(message: Message,
                              state: FSMContext) -> None:
    """
    Обработчик ввода города для получения погоды. Выводит погоду
    и возвращает в меню.

    Параметры:
        message (Message): Объект сообщения.

        state (FSMContext): Объект для управления состоянием бота.
    """
    keyboard = InlineKeyboardMarkup()
    btn_menu = InlineKeyboardButton('Назад в меню', callback_data='menu')
    keyboard.row(btn_menu)

    user_input = message.text
    async with state.proxy() as data:
        # Записываем ответ пользователя в переменную city.
        data['city'] = user_input.capitalize()

    state_data = await state.get_data()
    last_message_id = state_data.get('last_message_id')

    try:
        weather = await get_weather_for_city(data['city'])

        response = (
            await get_message('weather_in_city_message')
        ).format(
            data['city'], weather.status, weather.temperature
        ) + '\n\n' + (
            await get_hint(weather)
        )

        await bot.send_message(message.chat.id, response,
                               reply_markup=keyboard)

    except AttributeError:
        await bot.send_message(message.chat.id,
                               WEATHER_FOR_LOC_FAILED_MESSAGE,
                               reply_markup=keyboard)

    # Удаляем предыдущее сообщение бота, созданное через Callback_Query.
    await bot.delete_message(message.chat.id, last_message_id)

    await state.finish()  # Сброс состояния после обработки ввода.


@dp.message_handler(content_types=ContentType.LOCATION,
                    state=WaitingForLocationInput.location)
async def get_weather_in_location(message: Message, state: FSMContext) -> None:
    """
    Обработчик получения геолокации для получения погоды. Выводит погоду
    и возвращает в меню.

    Параметры:
        message (Message): Объект сообщения.

        state (FSMContext): Объект для управления состоянием бота.
    """
    keyboard = InlineKeyboardMarkup()
    button_menu = InlineKeyboardButton('Назад в меню',
                                       callback_data='menu')
    keyboard.row(button_menu)

    user_input = message.location
    async with state.proxy() as data:
        # Записываем ответ пользователя в переменную city.
        data['location'] = user_input

    state_data = await state.get_data()
    last_message_id = state_data.get('last_message_id')
    try:
        logger.debug(f'Получена геолокация от пользователя '
                     f'{message.chat.id}. Запрашиваем погоду.')
        weather = await get_weather_for_location(data['location'])
        logger.debug(f'Погода пользователя {message.chat.id} '
                     f'успешно получена. Формируем ответ.')

        response = (
            await get_message('weather_in_city_message')
        ).format(
            weather.name, weather.status, weather.temperature
        ) + '\n\n' + (
            await get_hint(weather)
        )

        await bot.send_message(message.chat.id, response,
                               reply_markup=keyboard)

    except AttributeError:
        await bot.send_message(message.chat.id,
                               WEATHER_FOR_LOC_FAILED_MESSAGE,
                               reply_markup=keyboard)

    # Удаляем предыдущее сообщение бота, созданное через Callback_Query.
    await bot.delete_message(message.chat.id, last_message_id)

    await state.finish()  # Сброс состояния после обработки ввода.


@dp.message_handler()
async def unknown_command_message(message: Message) -> None:
    """
    Обработчик неизвестной команды или сообщения. Отправляет пользователю
    текст ошибки.

    Параметры:
        message (Message): Объект сообщения.
    """
    keyboard = InlineKeyboardMarkup()
    btn_menu = InlineKeyboardButton('Меню', callback_data='menu')
    keyboard.row(btn_menu)

    try:
        await bot.send_message(message.chat.id, UNKNOWN_COMMAND_TEXT,
                               reply_markup=keyboard)

    except BotBlocked as bot_blocked_error:
        msg_error = (f'Функция unknown_command_message не смогла отправить '
                     f'сообщение пользователю. Бот заблокирован '
                     f'пользователем! {bot_blocked_error}')
        logger.error(msg_error)

    except Exception as error:
        msg_error = (f'Ошибка отправки сообщения пользователю '
                     f'в функции unknown_command_message! {error}')
        logger.error(msg_error)
