import os
import telebot
import requests
from flask import Flask, request
from openai import OpenAI

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

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

@bot.message_handler(func=lambda m: True)
def handle(message):
    user_text = message.text
    search_results = brave_search(user_text)

    prompt = (
        f"Вопрос: {user_text}\n"
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
