import logging
import requests
import random
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from googletrans import Translator
from langdetect import detect
import pytesseract
from PIL import Image
from io import BytesIO
import persian

translator = Translator()

# Dictionnary to store user-specific data
user_data = {}

# Define your token and chat IDs here
TOKEN = "1661364096:AAFLlxnJA79hsvTc_8q8kgS6zeZhXKUvvUU"
SOURCE_CHAT_ID = 102412904  # Replace with your source chat ID
TARGET_CHAT_ID = 102412904  # Replace with your target chat ID
CHANNEL_ID = -1002166152197

def forward_message(update: Update, context) -> None:
    message = update.message
    if message.from_user.id not in [102412904, 1371243348]:
        if message and update.message.chat.type == "private":
            context.bot.forward_message(chat_id=CHANNEL_ID, from_chat_id=message.chat_id, message_id=message.message_id)
            first_name = message.from_user.first_name
            user_id = message.from_user.id
            user_name = message.from_user.username
            info_text = f"فرستنده: {first_name}\nآی‌دی عددی: {user_id}\n یوزرنیم: {user_name}"
            context.bot.send_message(chat_id=CHANNEL_ID, text=info_text)

def start(update, context):
    message = "WELCOME " + update.message.from_user.first_name + "\n" + "For start translating enter /translate \n For image to text try /img2txt "
    context.bot.send_message(chat_id=update.message.from_user.id, text=message)

def translate(update, context):
    user_id = update.message.from_user.id
    user_data[user_id] = {'is_translating': True, 'target_language': 'en'}
    
    keyboard = [
        [InlineKeyboardButton("English", callback_data='en')],
        [InlineKeyboardButton("Persian", callback_data='fa')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.message.from_user.id, text="Please select the target language for translation:", reply_markup=reply_markup)

def stop(update, context):
    user_id = update.message.from_user.id
    if user_id in user_data:
        user_data[user_id]['is_translating'] = False
    context.bot.send_message(chat_id=update.message.from_user.id, text="Translating stopped...")

def translate_message(update, context):
    user_id = update.message.from_user.id
    if user_id in user_data and user_data[user_id]['is_translating']:
        msg = update.message.text
        detected_lang = detect(msg)
        if msg == "حانیه":
            context.bot.send_message(chat_id=update.message.from_user.id, text="⁪⁬⁮⁮⁮⁮⁪⁬⁮⁮⁮⁮")
            return None
        
        target_language = user_data[user_id]['target_language']
        if detected_lang == target_language:
            context.bot.send_message(chat_id=update.message.from_user.id, text="The text is already in the target language.")
        else:
            try:
                translated = translator.translate(msg, dest=target_language).text
                context.bot.send_message(chat_id=update.message.from_user.id, text=translated)
            except Exception as e:
                context.bot.send_message(chat_id=update.message.from_user.id, text=f"Error occurred: {e}")

def img2txt(update, context):
    user_id = update.message.from_user.id
    user_data[user_id] = {'is_translating': False, 'target_language': None}
    context.bot.send_message(chat_id=update.message.from_user.id, text="Please send an image.")


def persianchar(update, context):
    context.bot.send_message(chat_id=update.message.from_user.id, text="For organization type persian message with english keyboard. \n (this is ordered by owner LOL)")

def organization(update, context):
    msg = update.message.text
    org = persian.enToPersianChar(msg)
    context.bot.send_message(chat_id=update.message.from_user.id, text=org)

def button(update: Update, context):
    query = update.callback_query
    user_id = query.message.chat_id
    if user_id in user_data:
        user_data[user_id]['target_language'] = query.data
    query.answer()
    context.bot.send_message(chat_id=query.message.chat_id, text=f"Selected target language: {query.data}\nYou can now send the text to translate.")

import requests

joke_apis = [
    'https://v2.jokeapi.dev/joke/Any?type=single',
    'https://v2.jokeapi.dev/joke/Any?lang=en',
    'https://api.icndb.com/jokes/random',
    'https://icanhazdadjoke.com/',
]

def get_random_joke():
    try:
        api_url = random.choice(joke_apis)
        if 'icanhazdadjoke' in api_url:
            response = requests.get(api_url, headers={'Accept': 'application/json'})
            joke_data = response.json()
            joke_text = joke_data.get('joke', 'No joke found!')
        else:
            response = requests.get(api_url)
            joke_data = response.json()
            if joke_data.get('type') == 'single':
                joke_text = joke_data.get('joke', 'No joke found!')
            else:
                joke_text = f"{joke_data.get('setup', 'No joke found!')} - {joke_data.get('delivery', '')}"
        return joke_text
    except Exception as e:
        return f"Error occurred while fetching joke: {e}"

def joke(update, context):
    chat_id = update.message.chat_id
    joke_text = get_random_joke()
    
    # Send joke to the chat where the command was issued
    context.bot.send_message(chat_id=chat_id, text=joke_text)

def main():
    # ساخت آپدیتر و دیسپچر
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # ثبت هندلرهای خاص‌تر اول
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("translate", translate))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("img2txt", img2txt))
    dp.add_handler(CommandHandler("PersianCh", persianchar))
    dp.add_handler(CommandHandler("joke", joke))  # اضافه کردن هندلر برای دستور /joke
    
    # هندلر برای دریافت دکمه‌ها
    dp.add_handler(CallbackQueryHandler(button))

    # فقط برای پیام‌های متنی در چت‌های خصوصی که دستور نیستند
    dp.add_handler(MessageHandler(Filters.text & Filters.chat_type.private & ~Filters.command, translate_message))

    # هندلر برای پیام‌های متنی در چت‌های خصوصی برای سازماندهی پیام
    dp.add_handler(MessageHandler(Filters.text & Filters.chat_type.private, organization))

    # هندلر برای دریافت عکس در چت‌های خصوصی


    # فوروارد کردن پیام‌ها فقط در چت‌های خصوصی
    dp.add_handler(MessageHandler(Filters.all & Filters.chat_type.private, forward_message), group=1)

    # شروع ربات
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

