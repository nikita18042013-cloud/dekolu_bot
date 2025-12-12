import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types
import asyncio
import os
from datetime import datetime, timedelta

API_TOKEN = os.environ["8452703687:AAE9Wtfs1vAWQQtkRk7nYvCgXAv0i13wuqE"]
CHAT_ID = int(os.environ["657522185"])
URL = "https://energy-ua.info/cherga/1-2"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

last_state = None
last_notify_update = None
notified_pre_off = set()
notified_pre_on = set()


def parse_schedule():
    r = requests.get(URL, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    periods = []

    for line in soup.text.split("\n"):
        line = line.strip()
        if "З " in line and " до " in line:
            try:
                parts = line.replace("З ", "").split(" до ")
                start = datetime.strptime(parts[0], "%H:%M").time()
                end = datetime.strptime(parts[1], "%H:%M").time()
                periods.append((start, end))
            except:
                pass

    return periods


def is_now_in_period(periods):
    now = datetime.now().time()
    for start, end in periods:
        if start <= now <= end:
            return True
    return False


def next_event(periods):
    now = datetime.now()
    events = []

    for start, end in periods:
        start_dt = datetime.combine(now.date(), start)
        end_dt = datetime.combine(now.date(), end)

        if start_dt > now:
            events.append(("off", start_dt))
        if end_dt > now:
            events.append(("on", end_dt))

    if not events:
        return None

    return sorted(events, key=lambda x: x[1])[0]


async def check_loop():
    global last_state, last_notify_update, notified_pre_off, notified_pre_on

    while True:
        try:
            periods = parse_schedule()
            now = datetime.now()

            current_off = is_now_in_period(periods)

            if last_state is None:
                last_state = current_off

            if current_off != last_state:
                last_state = current_off
                if current_off:
                    await bot.send_message(CHAT_ID, "🔌 Світло ВИМКНЕНО!")
                else:
                    await bot.send_message(CHAT_ID, "💡 Світло УВІМКНЕНО!")

            ne = next_event(periods)
            if ne:
                ev_type, ev_time = ne
                delta = ev_time - now

                if timedelta(minutes=14) < delta <= timedelta(minutes=15):
                    if ev_type == "off" and ev_time not in notified_pre_off:
                        notified_pre_off.add(ev_time)
                        await bot.send_message(
                            CHAT_ID,
                            f"⏳ Через 15 хвилин БУДЕ ВІДКЛЮЧЕННЯ ({ev_time.strftime('%H:%M')})!",
                        )

                    if ev_type == "on" and ev_time not in notified_pre_on:
                        notified_pre_on.add(ev_time)
                        await bot.send_message(
                            CHAT_ID,
                            f"⏳ Через 15 хвилин БУДЕ УВІМКНЕННЯ ({ev_time.strftime('%H:%M')})!",
                        )

            if not last_notify_update or (now - last_notify_update).seconds >= 1800:
                state = "🔌 ВИМКНЕНО" if current_off else "💡 УВІМКНЕНО"
                txt = f"ℹ️ Стан: {state}\n"

                ne = next_event(periods)
                if ne:
                    t = "Відключення" if ne[0] == "off" else "Увімкнення"
                    txt += f"➡️ Наступна подія: {t} о {ne[1].strftime('%H:%M')}"

                await bot.send_message(CHAT_ID, txt)
                last_notify_update = now

        except Exception as e:
            await bot.send_message(CHAT_ID, f"⚠️ Помилка перевірки: {e}")

        await asyncio.sleep(60)


@dp.message_handler(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer(
        "Бот запущено. Буду сповіщати за 15 хвилин до вимкнення/увімкнення і кожні 30 хв."
    )


async def main():
    asyncio.create_task(check_loop())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
