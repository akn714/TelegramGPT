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
    print('[+] /ask', update.message.text[5:])
    await update.message.chat.send_action(action="typing")
    await update.message.reply_text(update.message.text[5:])

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