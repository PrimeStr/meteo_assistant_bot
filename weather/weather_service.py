import os
import urllib
from typing import Dict

import aiohttp
from aiohttp.client_exceptions import ClientConnectorError
from aiogram.types import Location
from dotenv import load_dotenv

from logger import logger
from weather.exceptions import (GetWeatherFromJSONError, WeatherCustomError,
                                WeatherAPIError)

load_dotenv()

WEATHER_API_KEY: str = os.getenv('WEATHER_API_KEY')
WEATHER_FOR_LOC_FAILED_MESSAGE: str = (f'К сожалению такого города не найдено!'
                                       f' Выйдите в меню и попробуйте снова.')
ZERO_KELVIN: float = 273.15


class WeatherInformation:
    """Класс для хранения данных о погоде."""

    def __init__(self, name: str, temperature: float, status: str) -> None:
        self.name = name
        self.temperature = temperature
        self.status = status

    def __str__(self) -> str:
        return self.name


async def get_weather_for_city(city_name) -> WeatherInformation:
    """Функция для получения готового ответа от API погоды по городу."""
    try:
        response = await make_weather_service_query(get_city_url(city_name))
        return response

    except KeyError as json_error:
        msg_error = (f'Ошибка ключей при распаковке JSON в функции '
                     f'get_weather_from_response() для города: {json_error}')
        logger.error(msg_error)
        raise GetWeatherFromJSONError(msg_error)

    except ClientConnectorError as connection_error:
        msg_error = (f'Ошибка подключения к API погоды при запросе по городу: '
                     f'{connection_error}')
        logger.error(msg_error)
        raise WeatherAPIError(msg_error)

    except Exception as error:
        msg_error = (f'Непредвиденная ошибка при запросе '
                     f'погоды по городу: {error}')
        logger.error(msg_error)
        raise WeatherCustomError(msg_error)


async def get_weather_for_location(location) -> WeatherInformation:
    """Функция для получения готового ответа от API погоды по геолокации."""
    try:
        response = await make_weather_service_query(get_location_url(location))
        return response

    except KeyError as json_error:
        msg_error = (f'Ошибка ключей при распаковке JSON в функции '
                     f'get_weather_from_response() для локации: {json_error}')
        logger.error(msg_error)
        raise GetWeatherFromJSONError(msg_error)

    except ClientConnectorError as connection_error:
        msg_error = (f'Ошибка подключения к API погоды при запросе '
                     f'по геолокации: {connection_error}')
        logger.error(msg_error)
        raise WeatherAPIError(msg_error)

    except Exception as error:
        msg_error = (f'Непредвиденная ошибка при запросе '
                     f'погоды по геолокации: {error}')
        logger.error(msg_error)
        raise WeatherCustomError(msg_error)


def get_city_url(city_name: str) -> str:
    """Функция для возврата готового URL с городом для запроса к API."""
    # Кодируем название города для корректного построения url запроса.
    city_name_for_url = urllib.parse.quote(city_name)
    return (
        f'https://api.openweathermap.org/data'
        f'/2.5/weather?q={city_name_for_url}'
        f'&appid={WEATHER_API_KEY}&lang=ru'
    )


def get_location_url(location: Location) -> str:
    """Функция для возврата готового URL с геолокацией для запроса к API."""
    return (
        f'https://api.openweathermap.org/data'
        f'/2.5/weather?lat={location.latitude}'
        f'&lon={location.longitude}&appid={WEATHER_API_KEY}&lang=ru'
    )


async def get_weather_from_response(json: Dict) -> WeatherInformation:
    """Функция распаковки ответа JSON в объект класса WeatherInformation"""
    response = WeatherInformation(json['name'], json['main']['temp'],
                                  json['weather'][0]['description'])

    await convert_temperature(response)
    return response


async def make_weather_service_query(url: str) -> WeatherInformation:
    """Функция асинхронного запроса к API погоды."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                json_data = await response.json()
                return await get_weather_from_response(json_data)


async def convert_temperature(weather_obj: WeatherInformation) -> None:
    """Функция асинхронного вызова конвертирования
    температуры в градусы Цельсия.
    """
    weather_obj.temperature = await convert_kelvin_to_celsius(
        weather_obj.temperature
    )


async def convert_kelvin_to_celsius(kelvin: float) -> float:
    """Функция, конвертирующая температуру из ответа API в градусы Цельсия."""
    celsius_long_float = kelvin - ZERO_KELVIN
    celsius = round(celsius_long_float, 1)
    return celsius
