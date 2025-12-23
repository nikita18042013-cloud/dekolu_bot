import asyncio
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")  # токен зададим в Railway

URL = "https://energy-ua.info/cherga/1-2"
TZ = pytz.timezone("Europe/Kyiv")

bot = Bot(token=TOKEN)


def get_schedule():
    """Заглушка — позже можно улучшить парсинг"""
    response = requests.get(URL, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    return "⚡ График обновлён"


async def notify(text):
    for chat_id in CHAT_IDS:
        await bot.send_message(chat_id=chat_id, text=text)


async def scheduler():
    while True:
        now = datetime.now(TZ)
        print("⏱ Проверка графика:", now.strftime("%H:%M"))

        schedule = get_schedule()

        # пример уведомлений
        if now.minute == 50:
            await notify("⚠️ Через 10 минут возможное отключение света")

        if now.minute == 10:
            await notify("✅ Через 10 минут возможное включение света")

        await asyncio.sleep(20 * 60)


async def start(update, context):
    chat_id = update.effective_chat.id
    CHAT_IDS.add(chat_id)
    await update.message.reply_text(
        "✅ Бот активирован\n"
        "Я буду уведомлять об отключениях света."
    )


async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    asyncio.create_task(scheduler())
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())