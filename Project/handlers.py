from telebot import types
from data_manager import read_database, find_games_by_category, format_game_list

def setup_handlers(bot):
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        markup = types.ReplyKeyboardMarkup(row_width=1)
        itembtn1 = types.KeyboardButton('Show My Wishlist')
        itembtn2 = types.KeyboardButton('Find a New Game')
        markup.add(itembtn1, itembtn2)
        bot.send_message(message.chat.id, "Welcome! Choose an option:", reply_markup=markup)

    @bot.message_handler(func=lambda message: message.text == "Find a New Game")
    def find_new_game(message):
        markup = types.ReplyKeyboardMarkup(row_width=2)
        itembtn1 = types.KeyboardButton('Find by name')
        itembtn2 = types.KeyboardButton('Find by category')
        markup.add(itembtn1, itembtn2)
        bot.send_message(message.chat.id, "Choose a search option:", reply_markup=markup)

    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        if message.text.startswith("/"):
            return
        elif message.text == "Find by name":
            bot.send_message(message.chat.id, "Please enter the name of the game you're looking for.")
        elif message.text == "Find by category":
            bot.send_message(message.chat.id, "Please enter the category of the game you're looking for.")
        else:
            database = read_database()
            if database is None:
                bot.send_message(message.chat.id, "Failed to connect to JSON database.")
                return
            category = message.text
            games = find_games_by_category(category, database)
            game_list = format_game_list(games)
            if game_list:
                bot.send_message(message.chat.id, f"Found games:\n{game_list}")
            else:
                bot.send_message(message.chat.id, "No games found for this category.")
#search by name
            name = find_games_by_name(category, database)
            name_list = format_game_list(name)
            if name_list:
                bot.send_message(message.chat.id, f" {name_list}")
            else:
                bot.send_message(message.chat.id, "No games found for this name.")