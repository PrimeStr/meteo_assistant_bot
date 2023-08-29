class WeatherCustomError(BaseException):
    """Непредвиденная ошибка сервиса погоды."""
    pass


class WeatherAPIError(BaseException):
    """Ошибка при запросе к API погоды."""
    pass


class WeatherGetMessageError(BaseException):
    """Ошибка формирования ответа API пользователю."""
    pass


class GetWeatherFromJSONError(BaseException):
    """Ошибка разбивки JSON из ответа API."""
    pass
