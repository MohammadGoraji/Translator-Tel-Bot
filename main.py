import os
import logging
import random
import requests
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from googletrans import Translator
from langdetect import detect
import persian
from dotenv import load_dotenv

# ---------------- CONFIG ----------------
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-100123456789"))

translator = Translator()
user_data = {}

# ---------------- HANDLERS ----------------
def start(update, context):
    msg = (
        f"👋 Welcome {update.message.from_user.first_name}!\n\n"
        "➡️ Use /translate to start translating.\n"
        "➡️ Use /img2txt for image-to-text (coming soon).\n"
        "➡️ Use /joke for a random joke."
    )
    context.bot.send_message(chat_id=update.message.chat_id, text=msg)

def translate(update, context):
    uid = update.message.from_user.id
    user_data[uid] = {"is_translating": True, "target_language": "en"}

    keyboard = [
        [InlineKeyboardButton("English", callback_data="en")],
        [InlineKeyboardButton("Persian", callback_data="fa")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=uid, text="Select target language:", reply_markup=reply_markup)

def stop(update, context):
    uid = update.message.from_user.id
    if uid in user_data:
        user_data[uid]["is_translating"] = False
    context.bot.send_message(chat_id=uid, text="✅ Translating stopped.")

def translate_message(update, context):
    uid = update.message.from_user.id
    if uid in user_data and user_data[uid]["is_translating"]:
        msg = update.message.text
        target = user_data[uid]["target_language"]

        try:
            if detect(msg) == target:
                context.bot.send_message(chat_id=uid, text="ℹ️ Already in target language.")
            else:
                translated = translator.translate(msg, dest=target).text
                context.bot.send_message(chat_id=uid, text=translated)
        except Exception as e:
            context.bot.send_message(chat_id=uid, text=f"❌ Error: {e}")

def button(update: Update, context):
    query = update.callback_query
    uid = query.message.chat_id
    if uid in user_data:
        user_data[uid]["target_language"] = query.data
    query.answer()
    query.edit_message_text(text=f"✅ Target language set to {query.data}. Now send text to translate.")

# ---------------- JOKES ----------------
joke_apis = [
    "https://v2.jokeapi.dev/joke/Any?type=single",
    "https://icanhazdadjoke.com/",
]

def get_joke():
    try:
        url = random.choice(joke_apis)
        headers = {"Accept": "application/json"}
        resp = requests.get(url, headers=headers).json()
        return resp.get("joke") or resp.get("setup", "") + " " + resp.get("delivery", "")
    except Exception as e:
        return f"❌ Joke fetch error: {e}"

def joke(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text=get_joke())

# ---------------- MAIN ----------------
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("translate", translate))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("joke", joke))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, translate_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
