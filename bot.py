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
⚪ /start
🤖 /ask
"""

gpt_mode = False

async def start(update: Update, context: CallbackContext):
    print('[+] /start')
    global gpt_mode
    gpt_mode = False
    await update.message.reply_text(start_reply_text)

# async def gpt_modes(update: Update, context: CallbackContext):

async def ask(update: Update, context: CallbackContext):
    global gpt_mode
    if gpt_mode:
        gpt_mode = False
        await update.message.reply_text('GPT Mode Turned Off')
    else:
        gpt_mode = True
        await update.message.reply_text('GPT Mode Turned On')

async def gpt_chat_handler(update: Update, context: CallbackContext):
    message = update.message.text
    print(f'[+] gpt query: "{message}"')
    if message=="":
        await update.message.reply_text('Query is empty, Please provide some query!')
        return
    await update.message.chat.send_action(action="typing")
    placeholder_message = await update.message.reply_text('generating...')
    response = await get_response(message)
    # response = {
    #     'choices':[{
    #         'message':{'content':'asdf'},
    #         'related_links':['no related links']
    #     }]
    # }
    await update.message.chat.send_action(action="typing")
    await context.bot.edit_message_text(response['choices'][0]['message']['content'], chat_id=placeholder_message.chat_id, message_id=placeholder_message.message_id)
    for _ in response['choices'][0]['related_links']:
        await update.message.reply_text(_)
    await update.message.reply_text('<i>*use /ask to turn off gpt mode</i>', parse_mode=ParseMode.HTML)

async def message_handler(update: Update, context: CallbackContext, message=None):
    print('[+] message_handler :', update.message.text)
    await update.message.chat.send_action(action="typing")
    await update.message.reply_text(f'<i>⚪ query: {update.message.text}</i>', parse_mode=ParseMode.HTML)
    global gpt_mode
    if gpt_mode:
        await gpt_chat_handler(update, context)
    else:
        await update.message.reply_text('GPT Mode is Off!\nplease use /ask to turn On of Off')

async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("/start", "Start Bot"),
        BotCommand("/ask", "Turn GPT Mode On or Off")
    ])

def run_bot() -> None:
    application = (ApplicationBuilder()
        .token(os.getenv('TELEGRAM_BOT_TOKEN'))
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('ask', ask))
    application.add_handler(MessageHandler(filters.TEXT, message_handler))

    # application.add_handler(CallbackQueryHandler(gpt_modes, pattern='^turn_gpt_mode_off_on'))
    
    print('Bot getting online...')
    application.run_polling()

if __name__ == '__main__':
    run_bot()