import os

import telebot

# from gpt import get_response

from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start','hello'])
def send_welcome(message):
    print('[user]', bot.get_my_name())
    print('[chat]', bot.get_chat())
    bot.reply_to(message, bot.get_me())
    # await bot.reply_to(message, await get_response(message))

# this function replies the same message if it doesn't match with above commands in previous function
@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.reply_to(message, message.text)


