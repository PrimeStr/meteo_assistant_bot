import os
import urllib
import json
import requests
from dotenv import load_dotenv
from logger import logger

load_dotenv()

WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')


class WeatherCustomException(BaseException):
    pass


class WeatherInformation:

    def __init__(self, name, temperature, status, is_kelvin=True):
        self.name = name
        self.temperature = convert_kelvin_to_celsius(
            temperature) if is_kelvin else temperature
        self.status = status


def get_weather_for_city(city_name):
    return make_weather_service_query(get_city_url(city_name))


def get_weather_for_location(location):
    return make_weather_service_query(get_location_url(location))


def get_city_url(city_name: str):
    return f'http://api.openweathermap.org/data/2.5/weather?q={urllib.parse.quote(city_name)}&appid={WEATHER_API_KEY}&lang=ru'


def get_location_url(location):
    return f'http://api.openweathermap.org/data/2.5/weather?lat={location.latitude}&lon={location.longitude}&appid={WEATHER_API_KEY}&lang=ru'

def get_weather_from_response(json):
    return WeatherInformation(json['name'], json['main']['temp'], json['weather'][0]['description'])

def make_weather_service_query(url):
    responce = requests.get(url)
    if responce.status_code == 200:
        return get_weather_from_response(responce.json())
    raise WeatherCustomException('API request error!')


def convert_kelvin_to_celsius(degrees) -> float:
    ZERO_KELVIN = 273.15
    return degrees - ZERO_KELVIN
