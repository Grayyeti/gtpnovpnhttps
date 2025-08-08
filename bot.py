...
    elif "курс" in text or "доллар" in text:
        extra_info = get_exchange_rate()
    elif "новости" in text:
        extra_info = get_news()
    elif "найди" in text or "поиск" in text or "ищи" in text or "что такое" in text:
        extra_info = search_web(message.text)

    prompt = message.text
    if extra_info:
        prompt = (
            f'Пользователь задал вопрос: "{message.text}"\n'
            f"Актуальная информация из интернета:\n{extra_info}\n"
            "Ответь, опираясь строго на эти данные, без выдумок."
        )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    "Ты помощник на базе GPT-4o. Ты должен использовать информацию из поиска, новостей, погоды и т.д., "
                    "если она передана. Не выдумывай информацию, если она не найдена."
                )},
                {"role": "user", "content": prompt}
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
