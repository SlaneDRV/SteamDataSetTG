from telebot import types
import os
import re
from data_manager import (
    read_database, find_games_by_category, format_game_list, find_games_by_name, save_wishlist,
    read_wishlist, add_game_to_wishlist, remove_game_from_wishlist, find_game_by_exact_name,
    check_wishlist,get_wishlist_count, generate_wishlist_file_txt, generate_wishlist_file_json,
    generate_wishlist_file_yaml, read_json_wishlist, get_wishlist_path, read_wishlist

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

    @bot.message_handler(func=lambda message: message.text == "Find by name")
    def find_by_name(message):
        msg = bot.send_message(message.chat.id, "Please enter the name of the game you're looking for.")
        bot.register_next_step_handler(msg, search_game_by_name)



    @bot.message_handler(func=lambda message: message.text in ["Wishlist", "View Wishlist"])
    def show_wishlist(message):
        user_id = message.chat.id
        wishlist = read_wishlist(user_id)
        markup_inline = types.InlineKeyboardMarkup()
        if not wishlist:
            bot.send_message(message.chat.id, "Your wishlist is empty.")
        else:
            for game in wishlist:
                price = f"{game['Price']}" if game['Price'] != 0.0 else 'Free'
                markup_inline.add(
                    types.InlineKeyboardButton(f"{game['Name']} - {price}", callback_data=f"wishlist_{game['Name']}"))

        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        itembtn_view = types.KeyboardButton('View Wishlist')
        itembtn_import = types.KeyboardButton('Import Wishlist')
        itembtn_download = types.KeyboardButton('Download Wishlist')
        itembtn_remove = types.KeyboardButton('Remove Game from Wishlist')
        itembtn_back = types.KeyboardButton('Back')
        markup.add(itembtn_view, itembtn_download, itembtn_import, itembtn_remove,  itembtn_back )

        wishlist_count = get_wishlist_count(user_id)

        bot.send_message(message.chat.id, "Your Wishlist:", reply_markup=markup_inline)
        bot.send_message(message.chat.id, f"You have {wishlist_count} games in your Wishlist.")
        bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)

    def find_game_by_exact_name_wish(game_name,user_id):

        wishlist = read_wishlist(user_id)  # Читаем список желаемых игр из файла или базы данных
        for game in wishlist:
            if game['Name'] == game_name:
                return game
        return None

    @bot.callback_query_handler(func=lambda call: call.data.startswith('wishlist_'))
    def show_game_details(call):
        game_name = call.data.split('_', 1)[1]
        print("NAME:   ",game_name)
        # Находим игру в списке желаемых игр по имени
        game_data = find_game_by_exact_name_wish(game_name, call.message.chat.id)
        # Проверяем, найдена ли игра в списке
        if game_data:
            print("DATA:   ", game_data)
            # Получаем информацию об игре из базы данных бота
            game_info = find_game_by_exact_name(game_name, read_database())
            # Проверяем, найдена ли информация об игре в базе данных
            print("Info:  ", game_info)
            if game_info:
                image_url = game_info[0][0]['ImageURL']
                total_reviews = game_info[0][0]['PositiveReviews'] + game_info[0][0]['NegativeReviews']
                positive_percentage = (game_info[0][0]['PositiveReviews'] / total_reviews) * 100 if total_reviews > 0 else 0
                developer = ", ".join(game_info[0][0]['Developer']).strip("'\"") if isinstance(game_info[0][0]['Developer'],
                                                                                         list) else \
                    game_info[0][0]['Developer'].strip("'\"")
                publisher = ", ".join(game_info[0][0]['Publisher']).strip("'\"") if isinstance(game_info[0][0]['Publisher'],
                                                                                         list) else \
                    game_info[0][0]['Publisher'].strip("'\"")
                price = f"{game_info[0][0]['Price']}" if game_info[0][0]['Price'] != 0.0 else 'Free'
                href = f"https://store.steampowered.com/app/{game_info[0][0]['ID']}"

                # Экранируем специальные символы для HTML
                def escape_html(text):
                    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

                name = escape_html(game_info[0][0]['Name'])
                short_description = escape_html(game_info[0][0]['ShortDesc'])
                developer = escape_html(developer)
                publisher = escape_html(publisher)
                release_date = escape_html(game_info[0][0]['ReleaseDate'])

                caption = (
                    f"<b>{name}</b>\n\n"
                    f"<i>{short_description}</i>\n\n"
                    f"<b>Total reviews:</b>        {total_reviews:,} ({positive_percentage:.2f}% positive)\n"
                    f"<b>Release date:</b>           {release_date}\n"
                    f"<b>Developer:</b>               {developer}\n"
                    f"<b>Publisher:</b>                 {publisher}\n\n"
                    f"<b>Price:</b>     {price}\n"
                    f"{href}"
                )

                if image_url:
                    bot.send_photo(call.message.chat.id, image_url, caption=caption, parse_mode='HTML')
                else:
                    bot.send_message(call.message.chat.id, caption, parse_mode='HTML')

                # Добавляем кнопку "Remove from Wishlist"
                markup_inline = types.InlineKeyboardMarkup()
                markup_inline.add(
                    types.InlineKeyboardButton(f"Remove {game_info[0][0]['Name']} from Wishlist",
                                               callback_data=f"remove_{game_info[0][0]['Name']}"))
                bot.send_message(call.message.chat.id, "Would you like to remove this game from your Wishlist?",
                                 reply_markup=markup_inline)
            else:
                bot.send_message(call.message.chat.id, f"Информация об игре '{game_name}' не найдена в базе данных.")
        else:
            bot.send_message(call.message.chat.id, f"Игра '{game_name}' не найдена в списке желаемых игр.")




    @bot.callback_query_handler(func=lambda call: call.data.startswith('list_'))
    def show_game_details_list(call):
        print("Processing list callback...")
        game_id = call.data.split('_', 1)[1]
        game_name = call.data.split('_', 1)[1]
        print("Game name extracted:", game_name)
        database = read_database()
        print("Database loaded.")

        game = database.get(game_id)
        print("Games found:", game)

        if game:
            image_url = game.get('ImageURL', None)
            total_reviews = game['PositiveReviews'] + game['NegativeReviews']
            positive_percentage = (game['PositiveReviews'] / total_reviews) * 100 if total_reviews > 0 else 0
            developer = ", ".join(game['Developer']).strip("'\"") if isinstance(game['Developer'], list) else game[
                'Developer'].strip("'\"")
            publisher = ", ".join(game['Publisher']).strip("'\"") if isinstance(game['Publisher'], list) else game[
                'Publisher'].strip("'\"")
            price = f"{game['Price']}" if game['Price'] != 0.0 else 'Free'
            href = f"https://store.steampowered.com/app/{game['ID']}"

            def escape_html(text):
                return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

            name = escape_html(game['Name'])
            short_description = escape_html(game['ShortDesc'])
            developer = escape_html(developer)
            publisher = escape_html(publisher)
            release_date = escape_html(game['ReleaseDate'])

            caption = (
                f"<b>{name}</b>\n\n"
                f"<i>{short_description}</i>\n\n"
                f"<b>Total reviews:</b>        {total_reviews:,} ({positive_percentage:.2f}% positive)\n"
                f"<b>Release date:</b>           {release_date}\n"
                f"<b>Developer:</b>               {developer}\n"
                f"<b>Publisher:</b>                 {publisher}\n\n"
                f"<b>Price:</b>     {price}\n"
                f"{href}"
            )

            if image_url:
                bot.send_photo(call.message.chat.id, image_url, caption=caption, parse_mode='HTML')
            else:
                bot.send_message(call.message.chat.id, caption, parse_mode='HTML')

            markup_inline = types.InlineKeyboardMarkup()
            if check_wishlist(call.message.chat.id, game['Name']):
                # Если игры нет в вишлисте, добавляем кнопку для добавления в вишлист
                markup_inline.add(types.InlineKeyboardButton(f"Remove {game['Name']} from Wishlist", callback_data=f"remove_{game['Name']}"))
                bot.send_message(call.message.chat.id, "Would you like to remove this game from your Wishlist?",reply_markup=markup_inline)

            else:
                markup_inline.add(types.InlineKeyboardButton(f"Add {game['Name']} to Wishlist", callback_data=f"add_{game['Name']}"))
                bot.send_message(call.message.chat.id, "Would you like to add this game to your Wishlist?",reply_markup=markup_inline)
        else:
            bot.send_message(call.message.chat.id, f"No details found for the game: {game_name}")



    def search_game_by_name(message):
        search_msg = bot.send_message(message.chat.id, f"Searching for games with name '{message.text}'...")
        games = find_games_by_name(message.text, read_database())[:10]
        markup = types.InlineKeyboardMarkup()
        for game_id, (game_data, _) in games:
            callback_data = f'list_{game_id}'
            markup.add(types.InlineKeyboardButton(game_data["Name"], callback_data=callback_data))
        if games:
            bot.edit_message_text("Select a game:", message.chat.id, search_msg.message_id, reply_markup=markup)
        else:
            bot.edit_message_text("No games found with that name.", message.chat.id, search_msg.message_id)

    def search_game_by_category(message):
        search_msg = bot.send_message(message.chat.id, f"Searching for games by category '{message.text}'...")
        games = find_games_by_category(message.text, read_database())[:10]
        markup = types.InlineKeyboardMarkup()
        for game_id, (game_data, _) in games:
            callback_data = f'list_{game_id}'
            markup.add(types.InlineKeyboardButton(game_data["Name"], callback_data=callback_data))
        if games:
            bot.edit_message_text("Select a game:", message.chat.id, search_msg.message_id, reply_markup=markup)
        else:
            bot.edit_message_text("No games found with that category.", message.chat.id, search_msg.message_id)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('add_'))
    def add_to_wishlist(call):

        game_name = call.data.split('_', 1)[1]
        database = read_database()
        games = find_game_by_exact_name(game_name, database)

        if games:  # Проверяем, что данные игры доступны
            game_data = games[0][0]  # Extract game data from tuple
            add_game_to_wishlist(call.message.chat.id, game_data)
            bot.edit_message_text(f"{game_data['Name']} added to your wishlist.", call.message.chat.id,call.message.message_id)


        else:
            bot.answer_callback_query(call.id, "Game not found in database.")

    @bot.message_handler(func=lambda message: message.text == "Remove Game from Wishlist")
    def prompt_for_game_removal(message):
        wishlist = read_wishlist(message.chat.id)
        if not wishlist:
            bot.send_message(message.chat.id, "Your wishlist is empty.")
            return
        markup = types.InlineKeyboardMarkup()
        for game in wishlist:
            callback_data = f'remove_{game["Name"]}'
            markup.add(types.InlineKeyboardButton(game["Name"], callback_data=callback_data))
        bot.send_message(message.chat.id, "Choose a game to remove from your wishlist:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('remove_'))
    def remove_game_from_wishlist_callback(call):
        game_name = call.data.split('_', 1)[1]
        remove_game_from_wishlist(call.message.chat.id, game_name)
        bot.answer_callback_query(call.id, f"{game_name} removed from your wishlist.")
        bot.edit_message_text("Game removed from your wishlist.", call.message.chat.id, call.message.message_id)

    @bot.message_handler(func=lambda message: message.text == "Download Wishlist")
    def choose_download_format(message):
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        itembtn_txt = types.KeyboardButton('Download as TXT')
        itembtn_json = types.KeyboardButton('Download as JSON')
        itembtn_yaml = types.KeyboardButton('Download as YAML')
        itembtn_back = types.KeyboardButton('Back')
        markup.add(itembtn_txt, itembtn_json, itembtn_yaml, itembtn_back)

        bot.send_message(message.chat.id, "Choose a format to download your wishlist:", reply_markup=markup)

    @bot.message_handler(func=lambda message: message.text.startswith("Download as"))
    def download_wishlist(message):
        user_id = message.chat.id
        format_choice = message.text.split()[-1].lower()
        if format_choice == 'txt':
            filename = generate_wishlist_file_txt(user_id)
        elif format_choice == 'json':
            filename = generate_wishlist_file_json(user_id)
        elif format_choice == 'yaml':
            filename = generate_wishlist_file_yaml(user_id)
        else:
            bot.send_message(message.chat.id, "Unknown format. Please choose again.")
            return

        with open(filename, 'rb') as file:
            bot.send_document(message.chat.id, file)

        os.remove(filename)  # Удаляем файл после отправки



    @bot.message_handler(func=lambda message: message.text == "Import Wishlist")
    def import_wishlist(message):
        user_id = message.chat.id
        msg = bot.send_message(user_id, "Please send the wishlist file.")
        bot.register_next_step_handler(msg, process_import_file)

    def process_import_file(message):
        user_id = message.chat.id
        try:

            if message.document:
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)

                # Сохранение файла для последующей обработки
                file_path = get_wishlist_path(user_id)
                with open(file_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                print("File downloaded and saved.")

                """
                # Чтение и обработка файла вишлиста
                wishlist_data = read_wishlist(user_id)
                if wishlist_data:
                    print("Wishlist data loaded successfully.")
                    for game in wishlist_data:
                        game_name = game.get('Name', '')
                        if game_name:
                            add_game_to_wishlist_by_name(user_id, game_name)
                        else:
                            print("Game name not found in the wishlist entry.")
                    bot.send_message(user_id, "Wishlist imported and updated successfully.")
                else:
                    bot.send_message(user_id, "Failed to read the JSON wishlist file.")
                    print("Failed to read the JSON wishlist file.")
                    """


            else:
                bot.send_message(user_id, "Please send a valid document file.")
                print("No document file received.")

        except Exception as e:
            bot.send_message(user_id, f"An error occurred: {str(e)}")
            print(f"An error occurred: {str(e)}")








