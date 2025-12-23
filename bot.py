import os
import json
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
URL = "https://energy-ua.info/cherga/1-2"
CHATS_FILE = "chats.json"
SCHEDULE_FILE = "schedule.json"

# --- Подписчики ---
if os.path.exists(CHATS_FILE):
    with open(CHATS_FILE, "r") as f:
        CHAT_IDS = set(json.load(f))
else:
    CHAT_IDS = set()

def save_chats():
    with open(CHATS_FILE, "w") as f:
        json.dump(list(CHAT_IDS), f)

# --- Последний график ---
def load_last_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_last_schedule(schedule):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule, f)

# --- Парсинг ---
def get_schedule():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(URL, headers=headers, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")
        schedule = {}
        if not table:
            return schedule
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) >= 2:
                time = cols[0].get_text(strip=True)
                area = cols[1].get_text(strip=True)
                schedule[time] = area
        return schedule
    except Exception as e:
        print("Ошибка при получении графика:", e)
        return {}

# --- Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in CHAT_IDS:
        CHAT_IDS.add(chat_id)
        save_chats()
    await update.message.reply_text("✅ Бот активирован!")

# --- Фоновая задача ---
async def scheduler(app):
    while True:
        new_schedule = get_schedule()
        if new_schedule:
            last_schedule = load_last_schedule()
            if new_schedule != last_schedule:
                text = "⚡ График відключень:\n"
                for t, a in new_schedule.items():
                    text += f"{t} — {a}\n"
                for chat_id in CHAT_IDS:
                    try:
                        await app.bot.send_message(chat_id=chat_id, text=text)
                    except Exception as e:
                        print(f"Ошибка отправки в {chat_id}: {e}")
                save_last_schedule(new_schedule)
            else:
                print("График не изменился")
        await asyncio.sleep(600)  # проверка каждые 10 минут

# --- Основная функция ---
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    # Запуск фоновой задачи после старта бота
    asyncio.create_task(scheduler(app))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())