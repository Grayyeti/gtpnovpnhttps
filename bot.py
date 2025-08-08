import os
import time
import telebot
import requests
from flask import Flask, request
from openai import OpenAI
from telebot import types
import xml.etree.ElementTree as ET

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

PASSWORD = "DoxieMonya77"
authorized_users = set()

bot = telebot.TeleBot(TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)

# Кэш новостей
cached_news = {"timestamp": 0, "content": ""}

def brave_search(query):
    try:
        url = f"https://api.search.brave.com/res/v1/web/search?q={requests.utils.quote(query)}"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_API_KEY
        }
        response = requests.get(url, headers=headers).json()
        results = response.get("web", {}).get("results", [])[:3]
        return "Бот работает!"
".join([f"{r['title']}: {r['description']}" for r in results]) if results else "Ничего не найдено."
    except Exception as e:
        return f"Ошибка поиска: {e}"

def get_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=52.37&longitude=4.89&current_weather=true"
        r = requests.get(url)
        weather = r.json().get("current_weather", {})
        return f"Температура: {weather.get('temperature', '?')}°C, ветер: {weather.get('windspeed', '?')} км/ч"
    except Exception as e:
        return f"Ошибка получения погоды: {e}"

def get_exchange_rate_rss():
    try:
        rss_url = "https://www.banki.ru/xml/news.rss"
        r = requests.get(rss_url)
        root = ET.fromstring(r.content)
        for item in root.findall("./channel/item"):
            title = item.find("title").text.lower()
            if "курс доллара" in title or "курс евро" in title:
                return f"{item.find('title').text}
{item.find('description').text}"
        return "Курс валют не найден в ленте banki.ru."
    except Exception as e:
        return f"Ошибка получения курса: {e}"

def get_news_rss(limit=30):
    try:
        now = time.time()
        if now - cached_news["timestamp"] < 14400:
            return cached_news["content"]

        rss_url = "https://tass.ru/rss/v2.xml"
        r = requests.get(rss_url)
        root = ET.fromstring(r.content)
        items = root.findall("./channel/item")[:limit]
        news = []
        for item in items:
            title = item.find("title").text
            desc = item.find("description").text
            news.append(f"• {title}
{desc}")
        compiled = "

".join(news)
        cached_news["timestamp"] = now
        cached_news["content"] = compiled
        return compiled
    except Exception as e:
        return f"Ошибка получения новостей: {e}"

@bot.message_handler(commands=["start"])
def send_welcome(message):
    if message.chat.type != "private":
        bot.reply_to(message, "⛔ Я работаю только в личных сообщениях.")
        return
    if message.chat.id in authorized_users:
        show_main_menu(message)
    else:
        bot.reply_to(message, "Введите пароль для доступа:")

@bot.message_handler(func=lambda m: m.chat.id not in authorized_users and m.chat.type == "private")
def check_password(message):
    if message.text.strip() == PASSWORD:
        authorized_users.add(message.chat.id)
        bot.reply_to(message, "✅ Доступ разрешён.")
        show_main_menu(message)
    else:
        bot.reply_to(message, "❌ Неверный пароль. Попробуйте снова.")

def show_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🌦 Погода сейчас", "💱 Курс валют", "🗞 Новости за день")
    bot.send_message(message.chat.id, "Выберите запрос или задайте свой вопрос:", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle(message):
    if message.chat.type != "private":
        bot.reply_to(message, "⛔ Я работаю только в личных сообщениях.")
        return

    if message.chat.id not in authorized_users:
        bot.reply_to(message, "⛔ Вы не авторизованы. Введите /start.")
        return

    text = message.text.strip().lower()

    if text == "🌦 погода сейчас":
        bot.reply_to(message, get_weather())
    elif text == "💱 курс валют":
        bot.reply_to(message, get_exchange_rate_rss())
    elif text == "🗞 новости за день":
        bot.reply_to(message, get_news_rss(limit=30))
    else:
        search_results = brave_search(message.text)
        prompt = (
            f"Вопрос: {message.text}
"
            f"Информация из интернета:
{search_results}
"
            "Ответь максимально полезно, ссылаясь на эти данные. Не придумывай, если не найдено."
        )
        try:
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Ты полезный бот-помощник с доступом к интернету."},
                    {"role": "user", "content": prompt}
                ]
            )
            answer = completion.choices[0].message.content
            bot.reply_to(message, answer)
        except Exception as e:
            bot.reply_to(message, f"Ошибка GPT: {e}")

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/")
def home():
    return "Бот работает!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=10000)
