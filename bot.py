import asyncio
import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------- Настройки ----------
TOKEN = "BOT_TOKEN"
URL = "https://energy-ua.info/cherga/1-2"

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ---------- Команды ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот для уведомлений об отключении света.")

# ---------- Функция проверки графика ----------
def get_schedule():
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(URL, headers=headers, timeout=15)
        r.raise_for_status()  # проверка HTTP ошибок
        soup = BeautifulSoup(r.text, "html.parser")
        # Пример: берем текст со страницы
        schedule_text = soup.get_text()[:200]  # первые 200 символов
        return schedule_text
    except requests.exceptions.HTTPError as e:
        logging.error(f"Ошибка при получении графика: {e}")
        return None
    except Exception as e:
        logging.error(f"Ошибка при получении графика: {e}")
        return None

# ---------- Фоновая задача ----------
async def scheduler(app):
    while True:
        schedule = get_schedule()
        if schedule:
            logging.info(f"Проверка графика: {schedule[:100]}...")  # логируем первые 100 символов
            # Здесь можно отправлять уведомления всем пользователям
            # await app.bot.send_message(chat_id=USER_ID, text=f"График: {schedule}")
        else:
            logging.warning("График недоступен")
        await asyncio.sleep(600)  # ждем 10 минут

# ---------- Главная функция ----------
def main():
    # Создаем приложение
    app = ApplicationBuilder().token(TOKEN).build()

    # Добавляем команды
    app.add_handler(CommandHandler("start", start))

    # Запускаем фоновые задачи
    app.create_task(scheduler(app))

    # Запускаем бот (сам управляет event loop)
    app.run_polling()

# ---------- Запуск ----------
if __name__ == "__main__":
    main()