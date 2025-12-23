import os
import json
import asyncio
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
URL = "https://energy-ua.info/cherga/1-2"
TZ = pytz.timezone("Europe/Kyiv")
CHATS_FILE = "chats.json"

# --- Загрузка подписчиков из файла ---
if os.path.exists(CHATS_FILE):
    with open(CHATS_FILE, "r") as f:
        CHAT_IDS = set(json.load(f))
else:
    CHAT_IDS = set()


def save_chats():
    with open(CHATS_FILE, "w") as f:
        json.dump(list(CHAT_IDS), f)


def get_schedule() -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://energy-ua.info/"
        }
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        return "⚡ График обновлён"
    except Exception as e:
        return f"❌ Ошибка при получении графика: {e}"


async def notify(app, text: str):
    for chat_id in CHAT_IDS:
        try:
            await app.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"Ошибка отправки уведомления в {chat_id}: {e}")


async def scheduler(app):
    while True:
        now = datetime.now(TZ)
        print("⏱ Проверка графика:", now.strftime("%H:%M"))
        print(get_schedule())

        if now.minute == 50:
            await notify(app, "⚠️ Через 10 минут возможное отключение света")
        if now.minute == 10:
            await notify(app, "✅ Через 10 минут возможное включение света")

        await asyncio.sleep(20 * 60)  # каждые 20 минут


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in CHAT_IDS:
        CHAT_IDS.add(chat_id)
        save_chats()
    await update.message.reply_text(
        "✅ Бот активирован!\nЯ буду уведомлять об отключениях света."
    )


# --- Создаём приложение PTB ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

# --- Запускаем планировщик в фоне ---
asyncio.create_task(scheduler(app))

# --- Запуск бота (без asyncio.run) ---
app.run_polling()