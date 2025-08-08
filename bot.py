import os
import telebot
from flask import Flask, request
from openai import OpenAI

TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = telebot.TeleBot(TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)
app = Flask(__name__)

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    "Ты ChatGPT на базе GPT-4o. "
                    "Если спросят про модель, обязательно укажи GPT-4o. "
                    "Если спрашивают про актуальность, говори, что ты обучен на данных до октября 2023 года. "
                    "Отвечай чётко и дружелюбно."
                )},
                {"role": "user", "content": message.text}
            ]
        )
        answer = resp.choices[0].message.content
        bot.reply_to(message, f"(GPT-4o)\n\n{answer}")
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
