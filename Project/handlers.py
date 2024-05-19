from telebot import types
import re
from data_manager import (
    read_database, find_games_by_category, format_game_list, find_games_by_name,
    read_wishlist, add_game_to_wishlist, remove_game_from_wishlist
)

def setup_handlers(bot):
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        show_main_menu(message)

    @bot.message_handler(func=lambda message: message.text == "Back")
    def handle_back(message):
        show_main_menu(message)

    def show_main_menu(message):
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        itembtn1 = types.KeyboardButton('Find a New Game')
        itembtn2 = types.KeyboardButton('Wishlist')
        markup.add(itembtn1, itembtn2)
        bot.send_message(message.chat.id, "Welcome! Choose an option:", reply_markup=markup)

    @bot.message_handler(func=lambda message: message.text == "Find a New Game")
    def find_new_game(message):
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        itembtn1 = types.KeyboardButton('Find by name')
        itembtn2 = types.KeyboardButton('Find by category')
        itembtn_back = types.KeyboardButton('Back')
        markup.add(itembtn1, itembtn2, itembtn_back)
        bot.send_message(message.chat.id, "Choose a search option or go back:", reply_markup=markup)

    @bot.message_handler(func=lambda message: message.text == "Find by category")
    def find_by_category(message):
        msg = bot.send_message(message.chat.id, "Please enter the category of the game you're looking for.")
        bot.register_next_step_handler(msg, search_game_by_category)

    """
    def process_category_search(message):
        search_msg = bot.send_message(message.chat.id, f"Searching for games in the category '{message.text}'...")
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
"""
    @bot.message_handler(func=lambda message: message.text == "Find by name")
    def find_by_name(message):
        msg = bot.send_message(message.chat.id, "Please enter the name of the game you're looking for.")
        bot.register_next_step_handler(msg, search_game_by_name)

    """
    def process_name_search(message):
        search_msg = bot.send_message(message.chat.id, f"Searching for games by name '{message.text}'...")
        database = read_database()
        if database is None:
            bot.send_message(message.chat.id, "Failed to connect to JSON database.")
            return
        names = find_games_by_name(message.text, database)
        name_list = format_game_list(names)
        if name_list:
            bot.edit_message_text("Found names:\n" + name_list, message.chat.id, search_msg.message_id)
        else:
            bot.edit_message_text("No games found by that name.", message.chat.id, search_msg.message_id)
"""
    @bot.message_handler(func=lambda message: message.text in ["Wishlist", "View Wishlist"])
    def show_wishlist(message):
        wishlist = read_wishlist(message.chat.id)
        markup_inline = types.InlineKeyboardMarkup()
        if not wishlist:
            bot.send_message(message.chat.id, "Your wishlist is empty.")
        else:
            for game in wishlist:
                price = f"{game['price']}$" if game['price'] != 0.0 else 'Free'
                markup_inline.add(types.InlineKeyboardButton(f"{game['name']} - {price}", callback_data=f"wishlist_{game['name']}"))

        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        itembtn_view = types.KeyboardButton('View Wishlist')
        itembtn_add = types.KeyboardButton('Add Game to Wishlist')
        itembtn_remove = types.KeyboardButton('Remove Game from Wishlist')
        itembtn_back = types.KeyboardButton('Back')
        markup.add(itembtn_view, itembtn_add, itembtn_remove, itembtn_back)

        bot.send_message(message.chat.id, "Your Wishlist:", reply_markup=markup_inline)
        bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('wishlist_'))
    def show_game_details(call):
        game_name = call.data.split('_', 1)[1]
        wishlist = read_wishlist(call.message.chat.id)
        for game in wishlist:
            if game['name'] == game_name:
                image_url = game.get('header_image', None)
                total_reviews = game['positive'] + game['negative']
                positive_percentage = (game['positive'] / total_reviews) * 100 if total_reviews > 0 else 0
                developer = ", ".join(game['developers']).strip("'\"") if isinstance(game['developers'], list) else \
                game['developers'].strip("'\"")
                publisher = ", ".join(game['publishers']).strip("'\"") if isinstance(game['publishers'], list) else \
                game['publishers'].strip("'\"")
                price = f"${game['price']}" if game['price'] != 0.0 else 'Free'

                # Экранируем специальные символы для HTML
                def escape_html(text):
                    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

                name = escape_html(game['name'])
                short_description = escape_html(game['short_description'])
                developer = escape_html(developer)
                publisher = escape_html(publisher)
                release_date = escape_html(game['release_date'])

                caption = (
                    f"<b>{name}</b>\n\n"
                    f"<i>{short_description}</i>\n\n"
                    f"<b>Total reviews:</b>        {total_reviews:,} ({positive_percentage:.2f}% positive)\n"
                    f"<b>Release date:</b>           {release_date}\n"
                    f"<b>Developer:</b>               {developer}\n"
                    f"<b>Publisher:</b>                 {publisher}\n\n"
                    f"<b>Price:</b>     {price}"
                )
                if image_url:
                    bot.send_photo(call.message.chat.id, image_url, caption=caption, parse_mode='HTML')
                else:
                    bot.send_message(call.message.chat.id, caption, parse_mode='HTML')
                break

    @bot.message_handler(func=lambda message: message.text == "Add Game to Wishlist")
    def prompt_for_game_name(message):
        msg = bot.send_message(message.chat.id, "Please enter the name of the game you want to add:")
        bot.register_next_step_handler(msg, search_game_by_name)
    """
    def search_game_by_name_wishlist(message):
        search_msg = bot.send_message(message.chat.id, f"Searching for games with name '{message.text}'...")
        games = find_games_by_name(message.text, read_database())[:10]  # Показываем только первые 5 результатов
        markup = types.InlineKeyboardMarkup()
        for game, _ in games:  # Извлекаем данные игры из кортежа
            callback_data = f'add_{game["name"]}'  # Пример: add_Half-Life
            markup.add(types.InlineKeyboardButton(game["name"], callback_data=callback_data))
        if games:
            bot.edit_message_text("Select a game to add to your wishlist:", message.chat.id, search_msg.message_id, reply_markup=markup)
        else:
            bot.edit_message_text("No games found with that name.", message.chat.id, search_msg.message_id)
"""
    def search_game_by_name(message):
        search_msg = bot.send_message(message.chat.id, f"Searching for games with name '{message.text}'...")
        games = find_games_by_name(message.text, read_database())[:10]  # Показываем только первые 5 результатов
        markup = types.InlineKeyboardMarkup()
        for game, _ in games:  # Извлекаем данные игры из кортежа
            callback_data = f'add_{game["name"]}'  # Пример: add_Half-Life
            markup.add(types.InlineKeyboardButton(game["name"], callback_data=callback_data))
        if games:
            bot.edit_message_text("Select a game to add to your wishlist:", message.chat.id, search_msg.message_id, reply_markup=markup)
        else:
            bot.edit_message_text("No games found with that name.", message.chat.id, search_msg.message_id)
    def search_game_by_category(message):
        search_msg = bot.send_message(message.chat.id, f"Searching for games by category '{message.text}'...")
        games = find_games_by_category(message.text, read_database())[:10]  # Показываем только первые 5 результатов
        markup = types.InlineKeyboardMarkup()
        for game, _ in games:  # Извлекаем данные игры из кортежа
            callback_data = f'add_{game["name"]}'  # Пример: add_Half-Life
            markup.add(types.InlineKeyboardButton(game["name"], callback_data=callback_data))
        if games:
            bot.edit_message_text("Select a game to add to your wishlist:", message.chat.id, search_msg.message_id, reply_markup=markup)
        else:
            bot.edit_message_text("No games found with that name.", message.chat.id, search_msg.message_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('add_'))
    def add_game_to_wishlist_callback(call):
        bot.answer_callback_query(call.id, f"Processing your request...")  # Immediate response

        game_name = call.data.split('_', 1)[1]
        games = find_games_by_name(game_name, read_database())

        if games:
            game_data = games[0][0]  # Extract game data from tuple
            add_game_to_wishlist(call.message.chat.id, game_data)
            bot.edit_message_text(f"{game_data['name']} added to your wishlist.", call.message.chat.id,
                                  call.message.message_id)
        else:
            bot.edit_message_text(f"Game {game_name} not found.", call.message.chat.id, call.message.message_id)

    @bot.message_handler(func=lambda message: message.text == "Remove Game from Wishlist")
    def prompt_for_game_removal(message):
        wishlist = read_wishlist(message.chat.id)
        if not wishlist:
            bot.send_message(message.chat.id, "Your wishlist is empty.")
            return
        markup = types.InlineKeyboardMarkup()
        for game in wishlist:
            callback_data = f'remove_{game["name"]}'
            markup.add(types.InlineKeyboardButton(game["name"], callback_data=callback_data))
        bot.send_message(message.chat.id, "Choose a game to remove from your wishlist:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('remove_'))
    def remove_game_from_wishlist_callback(call):
        game_name = call.data.split('_', 1)[1]
        remove_game_from_wishlist(call.message.chat.id, game_name)
        bot.answer_callback_query(call.id, f"{game_name} removed from your wishlist.")
        bot.edit_message_text("Game removed from your wishlist.", call.message.chat.id, call.message.message_id)
