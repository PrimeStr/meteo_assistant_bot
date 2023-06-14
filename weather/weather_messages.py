MESSAGES = {
    'weather_for_location_retrieval_failed': 'Не удалось узнать погоду в этой локации 😞,',
    'weather_in_city_message': 'Погода в городе {}:\n{}\nТемпература: {:.1f}°C.',
    'weather_in_location_message': 'Погода в городе {}:\n{}\nТемпература: {:.1f}°C.',
}


def get_message(message_key: str):
    return MESSAGES[message_key]
