import asyncio
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")  # токен задаём в Railway
URL = "https://energy-ua.info/cherga/1-2"
TZ = pytz.timezone("Europe/Kyiv")

# Множество для хранения chat_id подписчиков
CHAT_IDS = set()


def get_schedule() -> str:
    """Простейший парсер страницы с графиком"""
    try:
        response = requests.get(URL, timeout=15)
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

        # Пример уведомлений
        if now.minute == 50:
            await notify(app, "⚠️ Через 10 минут возможное отключение света")
        if now.minute == 10:
            await notify(app, "✅ Через 10 минут возможное включение света")

        await asyncio.sleep(20 * 60)  # проверка каждые 20 минут


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    CHAT_IDS.add(chat_id)
    await update.message.reply_text(
        "✅ Бот активирован\n"
        "Я буду уведомлять об отключениях света."
    )


async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    # Запускаем планировщик
    asyncio.create_task(scheduler(app))

    # Запуск бота
    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())