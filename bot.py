import os
import logging
import asyncio
import traceback
import html
import json
import tempfile
import pydub
from pathlib import Path
from datetime import datetime
import openai

import telegram
from telegram import (
    Update,
    User,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    AIORateLimiter,
    filters
)
from telegram.constants import ParseMode, ChatAction


from gpt import get_response

from dotenv import load_dotenv
load_dotenv()

start_reply_text = """
Hey There!

Commands:
/start
"""
async def start(update: Update, context: CallbackContext):
    print('[+] /start')
    await update.message.reply_text(start_reply_text)

async def ask(update: Update, context: CallbackContext):
    message = update.message.text[5:]
    print('[+] /ask', message)
    await update.message.chat.send_action(action="typing")
    placeholder_message = await update.message.reply_text('generating...')
    response = await get_response(message)
    await update.message.chat.send_action(action="typing")
    await context.bot.edit_message_text(response['choices'][0]['message']['content'], chat_id=placeholder_message.chat_id, message_id=placeholder_message.message_id)
    await update.message.reply_text(response['choices'][0]['related_links'])

async def message_handler(update: Update, context: CallbackContext, message=None):
    print('[+] message_handler :', update.message.text)
    await update.message.chat.send_action(action="typing")
    await update.message.reply_text('message: '+update.message.text)

def run_bot() -> None:
    application = ApplicationBuilder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('ask', ask))
    application.add_handler(MessageHandler(filters.TEXT, message_handler))
    
    print('Bot getting online...')
    application.run_polling()

if __name__ == '__main__':
    run_bot()