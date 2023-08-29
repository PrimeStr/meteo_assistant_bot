from typing import Dict

MESSAGES: Dict = {
    'weather_for_location_retrieval_failed':
        'Не удалось узнать погоду в этой локации 😞,',
    'weather_in_city_message':
        'Погода в городе {}:\n{}\nТемпература: {}°C.',
}


async def get_message(message_key: str) -> str:
    """Функция, формирующая ответное сообщение пользователю
    с данными о погоде.
    """
    return MESSAGES[message_key]
