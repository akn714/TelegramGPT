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
/ask
"""
async def start(update: Update, context: CallbackContext):

    await update.message.reply_text(start_reply_text)

async def ask(update: Update, context: CallbackContext, message=None):
    await update.message.reply_text('this is your message: '+(message if message!=None else ''))

def run_bot() -> None:
    application = ApplicationBuilder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('ask', ask))
    
    print('Bot getting online...')
    application.run_polling()

if __name__ == '__main__':
    run_bot()