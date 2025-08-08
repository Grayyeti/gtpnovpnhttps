import telebot
from telebot import types
import feedparser
import time
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
PASSWORD = "DoxieMonya77"
AUTHORIZED_USERS = set()
TASS_RSS = "https://tass.ru/rss/v2.xml"
YANDEX_RSS = "https://news.yandex.ru/quotes/1.html"  # Пример, будет парситься иначе

bot = telebot.TeleBot(BOT_TOKEN)
last_news_update = 0
cached_news = []

def fetch_tass_news():
    global last_news_update, cached_news
    now = time.time()
    if now - last_news_update > 4 * 3600 or not cached_news:
        feed = feedparser.parse(TASS_RSS)
        cached_news = [entry.title for entry in feed.entries[:30]]
        last_news_update = now
    return cached_news

def fetch_currency_info():
    # Пример: курс валют с banki.ru через RSS не получается корректно,
    # подставьте свой метод или API, если нужно
    return "Актуальные курсы валют доступны по ссылке: https://www.banki.ru/products/currency/cb/"
  
@bot.message_handler(commands=['start'])
def handle_start(message):
    if message.chat.type != "private":
        return

    user_id = message.from_user.id
    if user_id in AUTHORIZED_USERS:
        send_main_menu(message.chat.id, "Добро пожаловать обратно!")
    else:
        bot.send_message(message.chat.id, "🔐 Введите пароль для доступа:")

@bot.message_handler(func=lambda message: message.chat.type == "private")
def handle_password_or_buttons(message):
    user_id = message.from_user.id
    if user_id in AUTHORIZED_USERS:
        if message.text == "Погода":
            bot.send_message(message.chat.id, "🌦 Информацию о погоде можно посмотреть на: https://yandex.ru/pogoda/")
        elif message.text == "Курс валют":
            bot.send_message(message.chat.id, fetch_currency_info())
        elif message.text == "Новости за день":
            news = fetch_tass_news()
            response = "\n\n".join(news) if news else "Нет свежих новостей."
            bot.send_message(message.chat.id, response)
        else:
            bot.send_message(message.chat.id, "Я вас не понял. Используйте кнопки ниже.")
            send_main_menu(message.chat.id)
    else:
        if message.text == PASSWORD:
            AUTHORIZED_USERS.add(user_id)
            send_main_menu(message.chat.id, "✅ Доступ разрешён!")
        else:
            bot.send_message(message.chat.id, "❌ Неверный пароль. Попробуйте снова.")

def send_main_menu(chat_id, text="Выберите действие:"):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Погода", "Курс валют")
    markup.add("Новости за день")
    bot.send_message(chat_id, text, reply_markup=markup)

bot.polling()
