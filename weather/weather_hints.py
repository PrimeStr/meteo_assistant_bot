temperatures_list = [
    (-30, '❄️❄️❄️ Крайне холодно. Оставайтесь в тёплой постели. '
          'Если Вы по каким-то причинам должны выйти на улицу - соболезную.'),
    (-20, '❄️❄️ Очень холодно. Надевайте перчатки и все самое теплое.'),
    (-10, '❄️ Холодно. Надевайте все теплое.'),
    (0, '☁️ Холодновато, стоит взять куртку и шарф.'),
    (10, '🌤 Прохладно, стоит одеться чуть потеплее.'),
    (15, '🌤 Приятная погода, куртку можно оставить дома.'),
    (20, '☀️ Тепло. Штаны уже будут лишними.'),
    (27, '☀️☀️ Очень тепло. Футболка и шорты - можно балдеть.'),
    (50, '☀️☀️☀️ Адски жарко, держитесь в тени и не отходите далеко от кондиционера.'),
    (2000, '🌝 Друже, что вы забыли на Солнце?.')
]


def get_temperature_hint(temperature) -> str:
    for example_temperature, hint in temperatures_list:
        if temperature < example_temperature:
            return hint
    return 'Друже, тут я могу только посочувствовать.'


def get_rain_hint(weather_status: str) -> str:
    if 'дожд' in weather_status:
        return '☔️ Возьмите с собой зонт.'
    return ''


def get_hint(weather) -> str:
    advice = f'{get_temperature_hint(weather.temperature)}\n{get_rain_hint(weather.status)}'
    return advice
