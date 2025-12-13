import logging
import requests
from bs4 import BeautifulSoup
import re
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# =========================================================================
# 1. КОНФІГУРАЦІЯ
# =========================================================================

# Отримуємо токен з Environment Variables, які ви встановите на Scalingo
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN") 
URL = "https://energy-ua.info/cherga/1-2"

# ID чату або користувача, куди надсилатимуться автоматичні сповіщення
# ВАЖЛИВО: Замініть на реальний ID! 
# Його можна дізнатися, надіславши повідомлення боту @userinfobot
TARGET_CHAT_ID = os.environ.get("657522185") 

# Налаштування логування
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Словник для зберігання поточної інформації (можна замінити на БД для більших проектів)
CURRENT_STATE = {
    'last_notified_status': None, # Зберігатиме останній статус для уникнення спаму
    'last_schedule': ""
}

# =========================================================================
# 2. ФУНКЦІЯ ПАРСИНГУ
# =========================================================================

def get_schedule_data():
    """
    Завантажує сторінку та витягує дані про графік. 
    Повертає рядок з графіком та булеве значення (чи успішний парсинг).
    """
    # ... (Весь код функції get_schedule_data з попереднього повідомлення залишається тут) ...
    try:
        response = requests.get(URL, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        schedule_block = soup.find('div', class_='col-lg-12 col-xl-10')
        
        if not schedule_block:
            return "❌ Не вдалося знайти блок з графіком.", False

        schedule_parts = []
        cherga_blocks = schedule_block.find_all('div', class_=re.compile(r'cherga_\d'))
        
        if not cherga_blocks:
            return "❌ Не вдалося знайти окремі блоки черг.", False
            
        for block in cherga_blocks:
            header = block.find('h4', class_='card-title')
            header_text = header.text.strip() if header else "Черга без назви"
            schedule_parts.append(f"**⚡️ {header_text} ⚡️**")
            
            content = block.find('div', class_='card-body')
            if content:
                text_content = content.get_text(separator='\n', strip=True)
                schedule_parts.append(text_content + "\n")
            
        final_schedule = "\n".join(schedule_parts)
        
        if not final_schedule.strip():
             return "❌ Графік відключень порожній.", False
             
        return final_schedule, True

    except requests.exceptions.RequestException as e:
        return f"❌ Помилка при запиті до сайту: {e}", False
    except Exception as e:
        return f"❌ Невідома помилка при парсингу: {e}", False

# =========================================================================
# 3. ФУНКЦІЯ АВТОМАТИЧНОЇ ПЕРЕВІРКИ ТА СПОВІЩЕННЯ
# =========================================================================

async def check_schedule_for_outages(context: ContextTypes.DEFAULT_TYPE):
    """
    Регулярно перевіряє графік та сповіщає про зміни або поточний статус.
    """
    global CURRENT_STATE
    
    if not TARGET_CHAT_ID:
        logger.warning("TARGET_CHAT_ID не встановлено. Автоматичні сповіщення не працюють.")
        return

    logger.info("Початок регулярної перевірки графіка...")
    
    schedule_data, success = get_schedule_data()
    
    if not success:
        # Сповіщаємо лише про серйозні помилки парсингу, але не щоразу
        if CURRENT_STATE.get('last_schedule') != schedule_data:
            await context.bot.send_message(chat_id=TARGET_CHAT_ID, text=f"⚠️ Помилка парсингу: {schedule_data}")
            CURRENT_STATE['last_schedule'] = schedule_data
        return

    # Тут має бути логіка визначення, чи є відключення для вашої черги.
    # Оскільки ви не вказали, яка ваша черга, і як вона виглядає в даних, 
    # ми просто сповіщаємо, якщо графік змінився.
    
    # ----------------------------------------------------------------------
    # ПРИКЛАД ПРОСТОЇ ЛОГІКИ (Сповіщення про зміну або оновлення)
    # ----------------------------------------------------------------------
    
    now = datetime.now().strftime("%H:%M:%S")
    
    if schedule_data != CURRENT_STATE['last_schedule']:
        logger.info("Виявлено зміни в графіку. Надсилання сповіщення.")
        
        message_text = (
            f"🔔 **ОНОВЛЕННЯ ГРАФІКА ВІДКЛЮЧЕНЬ** (о {now}) 🔔\n"
            f"Зверніть увагу: Графік на сайті, ймовірно, змінився!\n\n"
            f"{schedule_data}\n"
        )
        await context.bot.send_message(chat_id=TARGET_CHAT_ID, text=message_text, parse_mode='Markdown')
        CURRENT_STATE['last_schedule'] = schedule_data
    else:
        logger.info("Графік не змінився. Пропускаємо сповіщення.")
        
# =========================================================================
# 4. ФУНКЦІЇ ОБРОБКИ КОМАНД TELEGRAM
# =========================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (Залишається без змін) ...
    user = update.effective_user
    await update.message.reply_html(
        f"Привіт, {user.mention_html()}! 👋\n"
        "Я бот для моніторингу графіків відключень світла.\n"
        "Використовуйте команду /schedule, щоб отримати актуальний графік.",
    )

async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє команду /schedule."""
    await update.message.reply_text("⏳ Завантажую актуальний графік відключень...")
    
    data, success = get_schedule_data()
    
    now = datetime.now().strftime("%d.%m.%Y о %H:%M")
    
    response_text = (
        f"🔋 **ОНОВЛЕНИЙ ГРАФІК ВІДКЛЮЧЕНЬ** 🔋\n"
        f"_(Дані з {URL})_\n\n"
        f"{data}\n\n"
        f"**Оновлено: {now}**"
    )
    
    await update.message.reply_text(response_text, parse_mode='Markdown')

# ... (інші команди help_command, error_handler без змін) ...
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє команду /help."""
    await update.message.reply_text(
        "Доступні команди:\n"
        "/start - Привітання\n"
        "/schedule - Отримати актуальний графік відключень\n"
        "/help - Показати цю довідку"
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Логує помилки, спричинені оновленнями."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


# =========================================================================
# 5. ГОЛОВНА ФУНКЦІЯ ЗАПУСКУ З ПЛАНУВАЛЬНИКОМ
# =========================================================================

def main():
    """Запускає бота та планувальник."""
    if not TELEGRAM_BOT_TOKEN:
        print("🔴 ПОМИЛКА: Не встановлено змінну середовища TELEGRAM_TOKEN.")
        return
    
    # Створення об'єкта Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Реєстрація обробників команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("schedule", schedule_command))
    application.add_handler(CommandHandler("help", help_command))

    # Реєстрація обробника помилок
    application.add_error_handler(error_handler)

    # Ініціалізація планувальника
    scheduler = AsyncIOScheduler()
    
    # Додаємо завдання: перевіряти графік кожні 15 хвилин
    scheduler.add_job(
        check_schedule_for_outages, 
        IntervalTrigger(minutes=15), 
        kwargs={'context': application}
    )
    
    # Запуск планувальника
    scheduler.start()
    
    print("🤖 Бот запущено. Планувальник активний. Очікування команд...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()