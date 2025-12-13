import telebot

# Создаем экземпляр бота

bot = telebot.TeleBot('8452703687:AAE9Wtfs1vAWQQtkRk7nYvCgXAv0i13wuqE')

# Функция, обрабатывающая команду /start

@bot.message_handler(commands=["start"])

def start(m, res=False):

    bot.send_message(m.chat.id, 'Бот запущен. Начните общение с ним.')

# Получение сообщений от пользователя

@bot.message_handler(content_types=["text"])

def handle_text(message):

    bot.send_message(message.chat.id, 'Вы написали: ' + message.text)

# Запускаем бота

bot.polling(none_stop=True, interval=0)