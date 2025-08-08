import os
import telebot
import requests
from flask import Flask, request
from openai import OpenAI
from telebot import types

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
MEDIASTACK_API_KEY = os.getenv("MEDIASTACK_API_KEY")

PASSWORD = "DoxieMonya77"
authorized_users = set()

bot = telebot.TeleBot(TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)

def brave_search(query):
    try:
        url = f"https://api.search.brave.com/res/v1/web/search?q={requests.utils.quote(query)}"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_API_KEY
        }
        response = requests.get(url, headers=headers).json()
        results = response.get("web", {}).get("results", [])[:3]
        return "\n".join([f"{r['title']}: {r['description']}" for r in results]) if results else "Ничего не найдено."
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

def get_exchange_rate():
    try:
        r = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=EUR,RUB,UAH")
        rates = r.json().get("rates", {})
        return f"Курс USD: EUR={rates.get('EUR', '?')}, RUB={rates.get('RUB', '?')}, UAH={rates.get('UAH', '?')}"
    except Exception as e:
        return f"Ошибка получения курса валют: {e}"

def get_news():
    try:
        url = "http://api.mediastack.com/v1/news"
        params = {
            "access_key": MEDIASTACK_API_KEY,
            "languages": "ru",
            "limit": 1,
            "sort": "published_desc"
        }
        r = requests.get(url, params=params)
        article = r.json().get("data", [{}])[0]
        title = article.get("title", "Нет заголовка")
        desc = article.get("description", "Нет описания")
        return f"{title}\n{desc}"
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
    markup.add("🌦 Погода сейчас", "💱 Курс валют", "📰 Новости дня")
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
        bot.reply_to(message, get_exchange_rate())
    elif text == "📰 новости дня":
        bot.reply_to(message, get_news())
    else:
        search_results = brave_search(message.text)
        prompt = (
            f"Вопрос: {message.text}\n"
            f"Информация из интернета:\n{search_results}\n"
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
