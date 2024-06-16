import telebot
import config
import handlers

bot = telebot.TeleBot(config.TOKEN)

handlers.setup_handlers(bot)

if __name__ == '__main__':
    bot.infinity_polling()
