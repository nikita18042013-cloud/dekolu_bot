import os
import asyncio
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ===== Настройки =====
TOKEN = os.getenv("BOT_TOKEN")  # токен Telegram
URL = "https://energy-ua.info/cherga/1-2"
TZ = pytz.timezone("Europe/Kyiv")

# Множество для хранения chat_id подписчиков
CHAT_IDS = set()


# ===== Функции =====
def get_schedule() -> str:
    """Получение текущего графика (заглушка для парсинга)"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # Здесь можно добавить реальный парсинг таблицы
        return "⚡ График обновлён"
    except Exception as e:
        return f"❌ Ошибка при получении графика: {e}"


async def notify(app, text: str):
    """Отправка уведомлений всем подписчикам"""
    for chat_id in CHAT_IDS:
        try:
            await app.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            print(f"Ошибка отправки уведомления в {chat_id}: {e}")


async def scheduler(app):
    """Асинхронный планировщик уведомлений"""
    while True:
        now = datetime.now(TZ)
        print("⏱ Проверка графика:", now.strftime("%H:%M"))

        schedule_text = get_schedule()
        print(schedule_text)

        # Пример уведомлений: за 10 минут до возможного отключения
        if now.minute == 50:
            await notify(app, "⚠️ Через 10 минут возможное отключение света")
        if now.minute == 10:
            await notify(app, "✅ Через 10 минут возможное включение света")

        await asyncio.sleep(20 * 60)  # проверка каждые 20 минут


# ===== Хендлеры =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    CHAT_IDS.add(chat_id)
    await update.message.reply_text(
        "✅ Бот активирован!\n"
        "Я буду уведомлять об отключениях света."
    )


# ===== Главная часть =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Добавляем хендлер команды /start
    app.add_handler(CommandHandler("start", start))

    # Запуск планировщика уведомлений в фоновом режиме
    asyncio.create_task(scheduler(app))

    # Запуск бота (без asyncio.run!)
    app.run_polling()


# ===== Точка входа =====
if __name__ == "__main__":
    main()