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
🤖 /gpt_modes
"""

is_gpt_mode_on = False

async def start(update: Update, context: CallbackContext):
    print('[+] /start')
    global is_gpt_mode_on
    is_gpt_mode_on = False
    await update.message.reply_text(start_reply_text)

async def show_gpt_modes(update: Update, context: CallbackContext):
    text = 'Turn GPT Mode ON or OFF'
    keyboard = []
    keyboard.append([InlineKeyboardButton('ON', callback_data='True'),InlineKeyboardButton('OFF', callback_data='False')])
    # keyboard.append([InlineKeyboardButton('OFF', callback_data=f"turn_gpt_mode_off_on|")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)

async def set_gpt_mode(update: Update, context: CallbackContext):
    global is_gpt_mode_on
    query = update.callback_query
    await query.answer()

    is_gpt_mode_on = eval(query.data)
    print('is_gpt_mode_on:', is_gpt_mode_on)

    await context.bot.send_message(query.message.chat.id, f"GPT Mode is {'ON' if is_gpt_mode_on else 'OFF'}")

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

async def transcribe_audio(audio_file):
    r = await openai.Audio.atranscribe("whisper-1", audio_file)
    return r["text"]

async def voice_message_handler(update: Update, context: CallbackContext):
    voice = update.message.voice
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        voice_ogg_path = tmp_dir / "voice.ogg"

        # download
        voice_file = await context.bot.get_file(voice.file_id)
        await voice_file.download_to_drive(voice_ogg_path)

        # convert to mp3
        voice_mp3_path = tmp_dir / "voice.mp3"
        pydub.AudioSegment.from_file(voice_ogg_path).export(
            voice_mp3_path, format="mp3")

        # transcribe
        with open(voice_mp3_path, "rb") as f:
            transcribed_text = await transcribe_audio(f)

            if transcribed_text is None:
                transcribed_text = ""

    text = f"🎤: <i>{transcribed_text}</i>"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    await update.message.reply_text('hi')

async def message_handler(update: Update, context: CallbackContext, message=None):
    print('[+] message_handler :', update.message.text)
    await update.message.chat.send_action(action="typing")
    await update.message.reply_text(f'<i>⚪ query: {update.message.text}</i>', parse_mode=ParseMode.HTML)
    global is_gpt_mode_on
    if is_gpt_mode_on:
        await gpt_chat_handler(update, context)
    else:
        await update.message.reply_text('GPT Mode is Off!\nplease use /ask to turn On of Off')

async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("/start", "Start Bot"),
        BotCommand("/ask", "Turn GPT Mode On or Off"),
        BotCommand("/gpt_modes", "Turn GPT Mode On or Off")
    ])

def run_bot() -> None:
    application = (ApplicationBuilder()
        .token(os.getenv('TELEGRAM_BOT_TOKEN'))
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('gpt_modes', show_gpt_modes))
    application.add_handler(MessageHandler(filters.TEXT, message_handler))
    application.add_handler(MessageHandler(filters.VOICE, voice_message_handler))
    application.add_handler(CallbackQueryHandler(set_gpt_mode))

    # application.add_handler(CallbackQueryHandler(gpt_modes, pattern='^turn_gpt_mode_off_on'))
    
    print('Bot getting online...')
    application.run_polling()

if __name__ == '__main__':
    run_bot()