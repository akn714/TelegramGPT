import os
import telebot
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start','hello'])
def send_welcome(message):
    bot.reply_to(message, "Hello, what's up Dude!")

# this function replies the same message if it doesn't match with above commands in previous function
@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.reply_to(message, message.text)


