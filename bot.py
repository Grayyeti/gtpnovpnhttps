import os
import telebot
import requests
from flask import Flask, request
from openai import OpenAI

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
MEDIASTACK_API_KEY = os.getenv("MEDIASTACK_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

bot = telebot.TeleBot(TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)

def search_web(query):
    try:
        url = f"https://api.search.brave.com/res/v1/web/search?q={requests.utils.quote(query)}"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_API_KEY
        }
        r = requests.get(url, headers=headers)
        results = r.json().get("web", {}).get("results", [])
        if results:
            first = results[0]
            return f"{first.get('title', '')}: {first.get('description', '')} ({first.get('url', '')})"
        return "Ничего не найдено."
    except Exception as e:
        return f"Ошибка при поиске: {e}"

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

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    text = message.text.lower()
    extra_info = ""

    if "погода" in text:
        extra_info = get_weather()
    elif "курс" in text or "доллар" in text:
        extra_info = get_exchange_rate()
    elif "новости" in text:
        extra_info = get_news()
    elif "найди" in text or "поиск" in text or "ищи" in text or "что такое" in text:
        extra_info = search_web(message.text)

    prompt = message.text
    if extra_info:
        prompt = (
            f"Пользователь задал вопрос: "{message.text}"
"
            f"Вот актуальная информация из интернета, которую удалось найти:
{extra_info}
"
            "Ответь, опираясь строго на эти данные, без фантазии."
        )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    "Ты помощник, который обязан включать найденные данные в ответ. "
                    "Не придумывай факты, если нет данных."
                )},
                {"role": "user", "content": prompt}
            ]
        )
        answer = resp.choices[0].message.content
        bot.reply_to(message, f"(GPT-4o)

{answer}")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

@app.route("/", methods=["GET"])
def index():
    return "Бот работает!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=10000)
