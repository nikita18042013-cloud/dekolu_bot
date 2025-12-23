from telegram.ext import ApplicationBuilder, CommandHandler
import asyncio

async def on_startup(app):
    print("Бот запущен!")
    # сюда можно добавить любые задачи
    asyncio.create_task(scheduler(app))

async def scheduler(app):
    while True:
        print("Выполняю планировщик...")
        await asyncio.sleep(60)  # пауза 1 минута

async def start(update, context):
    await update.message.reply_text("Привет!")

async def main():
    app = ApplicationBuilder().token("YOUR_TOKEN").build()
    app.add_handler(CommandHandler("start", start))

    # запуск планировщика после старта бота
    asyncio.create_task(on_startup(app))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())