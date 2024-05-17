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

    @bot.message_handler(func=lambda message: message.text == "Find by category")
    def find_by_category(message):
        msg = bot.send_message(message.chat.id, "Please enter the category of the game you're looking for.")
        bot.register_next_step_handler(msg, process_category_search)

    def process_category_search(message):
        search_msg = bot.send_message(message.chat.id, "Searching for games in the category '{}'...".format(message.text))
        database = read_database()
        if database is None:
            bot.send_message(message.chat.id, "Failed to connect to JSON database.")
            return
        games = find_games_by_category(message.text, database)
        game_list = format_game_list(games)
        if game_list:
            bot.edit_message_text("Found games:\n" + game_list, message.chat.id, search_msg.message_id)
        else:
            bot.edit_message_text("No games found for this category.", message.chat.id, search_msg.message_id)

    #search by name
    @bot.message_handler(func=lambda message: message.text == "Find by name")
    def find_by_name(message):
        msg = bot.send_message(message.chat.id, "Please enter the name of the game you're looking for.")
        bot.register_next_step_handler(msg, process_name_search)

    def process_name_search(message):
        search_msg = bot.send_message(message.chat.id, "Searching for games by name '{}'...".format(message.text))
        database = read_database()
        if database is None:
            bot.send_message(message.chat.id, "Failed to connect to JSON database.")
            return
        names = find_games_by_name(message.text, database)
        name_list = format_game_list(names)
        if name_list:
            bot.edit_message_text("Found games:\n" + name_list, message.chat.id, search_msg.message_id)
        else:
            bot.edit_message_text("No games found for this category.", message.chat.id, search_msg.message_id)
