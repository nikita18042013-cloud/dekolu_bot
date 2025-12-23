import asyncio
import logging
import aiohttp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "YOUR_BOT_TOKEN"

# Список пользователей, которые подписались на уведомления
subscribers = set()

logging.basicConfig(level=logging.INFO)

# ----------------- Команды -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscribers.add(update.effective_chat.id)
    await update.message.reply_text("Вы подписаны на уведомления об отключении света!")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscribers.discard(update.effective_chat.id)
    await update.message.reply_text("Вы отписаны от уведомлений.")

# ----------------- Проверка графика -----------------
async def fetch_schedule():
    url = "https://energy-ua.info/cherga/1-2"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    logging.warning(f"Ошибка при получении графика: {response.status}")
                    return None
                html = await response.text()
                # Здесь нужно добавить разбор HTML
                # Для примера вернем фиктивное событие
                return "Сегодня будет отключение: 18:50 - 19:10"
        except Exception as e:
            logging.error(f"Ошибка при запросе графика: {e}")
            return None

# ----------------- Фоновая задача -----------------
async def scheduler(app):
    while True:
        logging.info("Проверка графика...")
        schedule = await fetch_schedule()
        if schedule:
            for chat_id in subscribers:
                try:
                    await app.bot.send_message(chat_id=chat_id, text=schedule)
                except Exception as e:
                    logging.error(f"Не удалось отправить сообщение {chat_id}: {e}")
        await asyncio.sleep(600)  # проверка каждые 10 минут

# ----------------- Функция запуска после старта -----------------
async def on_startup(app):
    app.create_task(scheduler(app))

# ----------------- Основная функция -----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))

    # Запуск polling с post_init для фоновой задачи
    app.run_polling(post_init=on_startup)

if __name__ == "__main__":
    main()