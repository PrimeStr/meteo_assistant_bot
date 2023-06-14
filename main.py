import logging
import os
import time
import requests
import flask
import telebot
from dotenv import load_dotenv
from logger import logger
from weather.weather_service import WeatherCustomException, WeatherInformation, get_weather_for_city, get_weather_for_location
from weather.weather_messages import get_message
from weather.weather_hints import get_hint
load_dotenv()

API_TG_TOKEN = os.getenv('API_TG_TOKEN')

WEATHER_FOR_LOC_FAILED_MESSAGE = 'Weather for location failed!'

WEBHOOK_HOST = os.getenv('WEBHOOK_HOST')
WEBHOOK_PORT = os.getenv('WEBHOOK_PORT')
WEBHOOK_LISTEN = os.getenv('WEBHOOK_LISTEN')

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Path to the ssl private key

# Quick'n'dirty SSL certificate generation:
#
# openssl genrsa -out webhook_pkey.pem 2048
# openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem
#
# When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply
# with the same value in you put in WEBHOOK_HOST

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (API_TG_TOKEN)

THEDOGAPI_URL = 'https://api.thedogapi.com/v1/images/search'



bot = telebot.TeleBot(API_TG_TOKEN)

app = flask.Flask(__name__)


# Empty webserver index, return nothing, just http 200
@app.route('/', methods=['GET', 'HEAD'])
def index():
    return ''


# Process webhook calls
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message,
                 ("Hello there, I am Multipurpose Telebot!.\n"
                  "I am here to make your life better."))


@bot.message_handler(commands=['doggy'])
def send_doggy(message):
    try:
        response = requests.get(THEDOGAPI_URL)
    except Exception as error:
        logging.error(f'Error when requesting main API: {error}')
        msg = ('Sorry, the dog server is not available at the moment.'
               'Here\'s a cat for you.')
        bot.send_message(message.chat.id, msg)
        new_url = 'https://api.thecatapi.com/v1/images/search'
        response = requests.get(new_url)
    response = response.json()
    random_doggy = response[0].get('url')
    bot.send_photo(message.chat.id, random_doggy)


# Handle all other messages
#@bot.message_handler(func=lambda message: True, content_types=['text'])
#def echo_message(message):
#    bot.send_message(message.chat.id, 'I don\'t understand.')


@bot.message_handler(func=lambda message: True, content_types=['location'])
def get_weather_in_location(message):
    if message.location:
        try:
            weather = get_weather_for_location(message.location)
        except WeatherCustomException:
            bot.send_message(message.chat.id, WEATHER_FOR_LOC_FAILED_MESSAGE)
            return

        response =  get_message('weather_in_location_message') \
            .format(weather.name, weather.status, weather.temperature) + '\n\n' + get_hint(weather)

        bot.send_message(message.chat.id, response)
        return

    bot.send_message(message.chat.id, WEATHER_FOR_LOC_FAILED_MESSAGE)



@bot.message_handler(func=lambda message: True, content_types=['text'])
def get_weather_in_city(message):
    if message.text:
        try:
            weather = get_weather_for_city(message.text)
        except WeatherCustomException:
            bot.send_message(message.chat.id, WEATHER_FOR_LOC_FAILED_MESSAGE)
            return

        response =  get_message("weather_in_city_message") \
                    .format(message.text, weather.status, weather.temperature) \
                    + '\n\n' + get_hint(weather)

        bot.send_message(message.chat.id, response)


bot.infinity_polling()


# # Remove webhook, it fails sometimes the set if there is a previous webhook
# try:
#     bot.remove_webhook()
# except Exception as error:
#     message = 'An error has occurred while removing webhook.'
#     logger.error(message, error)
#
# time.sleep(1)
#
# # Set webhook
# try:
#     bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
#                 certificate=open(WEBHOOK_SSL_CERT, 'r'))
#
# except Exception as error:
#     message = 'An error has occurred while setting webhook.'
#     logger.error(message, error)
#
# logger.debug('Webhook set!')
#
# # Start flask server
# app.run(host=WEBHOOK_LISTEN,
#         port=WEBHOOK_PORT,
#         ssl_context=(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV),
#         debug=True)
