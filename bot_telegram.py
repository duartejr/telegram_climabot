# climabot = telebot.TeleBot(BOT_APIKEY)
# -*- coding: utf-8 -*-

import requests
import os
from telebot import TeleBot
from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup #States
from telebot.storage import StateMemoryStorage # States storage

BOT_APIKEY = os.environ.get("BOT_APIKEY")
WEATHER_APIKEY = os.environ.get("WEATHER_APIKEY")
MAIN_URL = "http://dataservice.accuweather.com/"

# Now, you can pass storage to bot.
state_storage = StateMemoryStorage() # you can init here another storage

bot = TeleBot(BOT_APIKEY,
              state_storage=state_storage)

menu = "/tempoAgora Para visualizar como está o tempo agora.\n"\
       "/previsaoAmanha Para visualizar a previsao de amanhã.\n"


# States group
class MyStates(StatesGroup):
    # Just name variables differently
    city = State() # creating instances of State class is enough from now
    search = State()


@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, "Bem vindo ao climabot")
    """
    Start command. Here we are starting the bot
    """
    bot.set_state(message.from_user.id, MyStates.city, message.chat.id)
    bot.send_message(message.chat.id, 'Me diga sua cidade: ')


@bot.message_handler(state=MyStates.city)
def name_get(message):
    """
    State 1. Will process when user's city is MyStates.city.
    """
    bot.send_message(message.chat.id, 'Pronto cidade salva.')
    bot.set_state(message.from_user.id, MyStates.search, message.chat.id)
    
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['city'] = message.text
        msg = (f"Agora vamos ver o clima em: <b>{data['city']}\n</b>")
        bot.send_message(message.chat.id, msg, parse_mode="html")
    
    bot.send_message(message.chat.id, menu)


@bot.message_handler(commands=["tempoAgora"], state=MyStates.search)
def current_weather(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        city = data["city"].lower()
        url_city_key = f"{MAIN_URL}/locations/v1/cities/search?apikey={WEATHER_APIKEY}&q={city}"
        location_key = requests.get(url_city_key).json()[0]["Key"]
        weather = requests.get(f"{MAIN_URL}/currentconditions/v1/{location_key}?apikey={WEATHER_APIKEY}&language=pt-br")
        weather = weather.json()[0]
        
        text = f"O tempo em {city} está: {weather['WeatherText']}\n"\
            f"Temperatura de {weather['Temperature']['Metric']['Value']} ºC\n"
        
        if weather["HasPrecipitation"]:
            text += "Está chovendo agora.\n"
        else:
            text += "Não está chovendo agora.\n"
        
        bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["previsaoAmanha"], state=MyStates.search)
def tomorrow_weather(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        city = data["city"].lower()
        url_city_key = f"{MAIN_URL}/locations/v1/cities/search?apikey={WEATHER_APIKEY}&q={city}"
        location_key = requests.get(url_city_key).json()[0]["Key"]
        weather = requests.get(f"{MAIN_URL}/forecasts/v1/daily/1day/{location_key}?apikey={WEATHER_APIKEY}&language=pt-br&metric=true")
        weather = weather.json()["DailyForecasts"][0]
        
        text = f"Amanhã em {city} o dia estará: {weather['Day']['IconPhrase']}. "
        
        if weather["Day"]["HasPrecipitation"]:
            text += "Com probabilidade de chuvas.\n"
        else:
            text += "Sem probabilidade de chover.\n"
        
        text += f"A noite o tempo estará: {weather['Night']['IconPhrase']}. "
        if weather["Night"]["HasPrecipitation"]:
            text += "Com probabilidade de chuvas.\n"
        else:
            text += "Sem probabilidade de chover.\n"
        
        text += f"A temperatura mínima será de: {weather['Temperature']['Minimum']['Value']} ºC.\n"
        text += f"A temperatura máxima será de: {weather['Temperature']['Maximum']['Value']} ºC.\n"
        
        bot.send_message(message.chat.id, text)


@bot.message_handler(state=MyStates.search)
def ready_for_search(message):
    """
    State 3. Will process when user's search is MyStates.search.
    """
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        msg = (f"Estamos vendo o clima para: <b>{data['city']}\n</b>")
        bot.send_message(message.chat.id, msg, parse_mode="html")


bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling()
