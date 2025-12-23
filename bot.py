import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, JobQueue

TOKEN = os.getenv("BOT_TOKEN")
URL = "https://energy-ua.info/cherga/1-2"
TZ = pytz.timezone("Europe/Kyiv")
CHATS_FILE = "chats.json"
SCHEDULE_FILE = "schedule.json"  # для хранения последнего графика

# --- Загрузка подписчиков ---
if os.path.exists(CHATS_FILE):
    with open(CHATS_FILE, "r") as f:
        CHAT_IDS = set(json.load(f))
else:
    CHAT_IDS = set()

def save_chats():
    with open(CHATS_FILE, "w") as f:
        json.dump(list(CHAT_IDS), f)

# --- Загрузка последнего графика ---
def load_last_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_last_schedule(schedule):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule, f)

# --- Парсинг сайта ---
def get_schedule() -> dict:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://energy-ua.info/",
            "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
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
        print(f"Ошибка при получении графика: {e}")
        return {}

# --- Отправка уведомлений только при изменениях ---
async def notify(context: ContextTypes.DEFAULT_TYPE):
    new_schedule = get_schedule()
    if not new_schedule:
        return

    last_schedule = load_last_schedule()

    if new_schedule != last_schedule:
        text = "⚡ График відключень:\n"
        for time, area in new_schedule.items():
            text += f"{time} — {area}\n"

        for chat_id in CHAT_IDS:
            try:
                await context.bot.send_message(chat_id=chat_id, text=text)
            except Exception as e:
                print(f"Ошибка отправки уведомления в {chat_id}: {e}")

        save_last_schedule(new_schedule)
    else:
        print("График не изменился, уведомления не отправлены.")

# --- Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in CHAT_IDS:
        CHAT_IDS.add(chat_id)
        save_chats()
    await update.message.reply_text("✅ Бот активирован!\nЯ буду уведомлять об отключениях света при изменении графика.")

# --- Планирование фоновой задачи ---
def schedule_jobs(app):
    job_queue: JobQueue = app.job_queue
    job_queue.run_repeating(
        callback=lambda ctx: notify(ctx),
        interval=600,  # каждые 10 минут
        first=0
    )

# --- Создание приложения ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

# --- Функция инициализации ---
async def on_startup(app):
    schedule_jobs(app)
    print("✅ Фоновые задачи запущены")

# --- Запуск бота ---
if __name__ == "__main__":
    app.run_polling(close_loop=False, post_init=on_startup)