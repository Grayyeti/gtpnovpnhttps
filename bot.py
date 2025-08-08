
import telebot
import feedparser
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привет! Нажми кнопку:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    if message.text == "Покажи новости за день":
        entries = get_tass_news()
        if entries:
            text = "\n".join([f"{e['title']}: {e['summary']}" for e in entries])
        else:
            text = "Не удалось получить новости."
        bot.send_message(message.chat.id, text)
    else:
        bot.send_message(message.chat.id, "Неизвестная команда.")

def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Покажи новости за день")
    return markup

def get_tass_news():
    rss_url = "https://tass.ru/rss/v2.xml"
    feed = feedparser.parse(rss_url)
    return feed.entries[:30]

bot.infinity_polling()
