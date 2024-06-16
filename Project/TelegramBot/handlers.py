import os
import json
import asyncio
import requests
from telebot import TeleBot, types
from config import TgID, SteamKey
from data_manager import (
    find_game_by_exact_id, read_database, find_games_by_tag, format_game_list, find_games_by_name, read_txt_file, read_yaml_file, save_wishlist,
    read_wishlist, add_game_to_wishlist, remove_game_from_wishlist, find_game_by_exact_name,
    check_wishlist, get_wishlist_count, generate_wishlist_file_txt, generate_wishlist_file_json,
    generate_wishlist_file_yaml, read_json_wishlist, get_wishlist_path, read_wishlist, preload_database,
    sort_wishlist_by_date, update_wishlist, sort_wishlist_by_reviews
)

exchange_rates = {
    'RUB': 0.013,
    'UAH': 0.027,
    'TRY': 0.060,
    'KZT': 0.0023,
    'PLN': 0.24,
    'CNY': 0.14,
    'USD': 1
}

def setup_handlers(bot):
    # Handler for the /start command, displays the main menu
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        show_main_menu(message)

    # Handler for the "Back" button, shows the main menu
    @bot.message_handler(func=lambda message: message.text == "Back")
    def handle_back(message):
        show_main_menu(message)

    # Function to display the main menu
    def show_main_menu(message):
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        itembtn1 = types.KeyboardButton('Find a New Game')
        itembtn2 = types.KeyboardButton('Wishlist')
        markup.add(itembtn1, itembtn2)
        if message.chat.id == config.TgID:
            steam_api_btn = types.KeyboardButton('Run SteamAPI')
            markup.add(steam_api_btn)
        bot.send_message(message.chat.id, "Welcome! Choose an option:", reply_markup=markup)

    # Handler for the "Run SteamAPI" button, executes SteamAPI script and sends progress messages
    @bot.message_handler(func=lambda message: message.text == 'Run SteamAPI')
    def run_steam_api(message):
        if message.chat.id == config.TgID:
            bot.send_message(message.chat.id, "Starting SteamAPI process...")
            process = subprocess.Popen(['../.venv/Scripts/python.exe', 'SteamAPI.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, bufsize=1, encoding='utf-8', errors='ignore')
            for line in iter(process.stdout.readline, ''):
                clean_line = line.strip()
                if clean_line:
                    bot.send_message(message.chat.id, clean_line)
            process.stdout.close()
            process.wait()
            bot.send_message(message.chat.id, "SteamAPI process completed!")

    # Handler for "Find a New Game" button, displays options to search by name or tag
    @bot.message_handler(func=lambda message: message.text == "Find a New Game")
    def find_new_game(message):
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        itembtn1 = types.KeyboardButton('Find by name')
        itembtn2 = types.KeyboardButton('Find by tag')
        itembtn_back = types.KeyboardButton('Back')
        markup.add(itembtn1, itembtn2, itembtn_back)
        bot.send_message(message.chat.id, "Choose a search option or go back:", reply_markup=markup)

    # Handler for "Find by tag" button, prompts user to enter the tag
    @bot.message_handler(func=lambda message: message.text == "Find by tag")
    def find_by_tag(message):
        msg = bot.send_message(message.chat.id, "Please enter the tag of the game you're looking for.")
        bot.register_next_step_handler(msg, search_game_by_tag)

    # Handler for "Find by name" button, prompts user to enter the game name
    @bot.message_handler(func=lambda message: message.text == "Find by name")
    def find_by_name(message):
        msg = bot.send_message(message.chat.id, "Please enter the name of the game you're looking for.")
        bot.register_next_step_handler(msg, search_game_by_name)

    # Handler for "Wishlist" and "View Wishlist" buttons, displays user's wishlist
    @bot.message_handler(func=lambda message: message.text in ["Wishlist", "View Wishlist"])
    def show_wishlist(message):
        user_id = message.chat.id
        wishlist = read_wishlist(user_id)
        markup_inline = types.InlineKeyboardMarkup(row_width=2)
        if not wishlist:
            bot.send_message(message.chat.id, "Your wishlist is empty.")
        else:
            for game in wishlist:
                price = f"{game['Price']}" if game['Price'] != 0.0 else 'Free'
                markup_inline.add(
                    types.InlineKeyboardButton(f"{game['Name']} - {price}", callback_data=f"wishlist_{game['Name']}"))

        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        itembtn_view = types.KeyboardButton('View Wishlist')
        itembtn_import = types.KeyboardButton('Import Wishlist')
        itembtn_download = types.KeyboardButton('Download Wishlist')
        itembtn_remove = types.KeyboardButton('Remove Game from Wishlist')
        itembtn_total_price = types.KeyboardButton('Calculate Total Price')
        itembtn_tag_count = types.KeyboardButton('Count Tags')
        itembtn_sort = types.KeyboardButton('Sort')
        itembtn_back = types.KeyboardButton('Back')
        markup.add(itembtn_total_price, itembtn_tag_count)
        markup.add(itembtn_download, itembtn_import)
        markup.add(itembtn_remove, itembtn_sort, itembtn_back)

        wishlist_count = get_wishlist_count(user_id)

        bot.send_message(message.chat.id, "Your Wishlist:", reply_markup=markup_inline)
        bot.send_message(message.chat.id, f"You have {wishlist_count} games in your Wishlist.")
        bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)

    @bot.message_handler(func=lambda message: message.text == "Sort")
    def handle_sort(message):
        markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
        itembtn_sort_alphabet = types.KeyboardButton('Sort by alhpabet')
        itembtn_sort_date = types.KeyboardButton('Sort by date')
        itembtn_sort_reviews = types.KeyboardButton('Sort by reviews')
        itembtn_back = types.KeyboardButton('Back')
        markup.add(itembtn_sort_reviews, itembtn_sort_date, itembtn_sort_alphabet)
        markup.add(itembtn_back)

        bot.send_message(message.chat.id, "Sort Wishlist by:", reply_markup=markup)

    @bot.message_handler(func=lambda message: message.text == "Sort by date")
    def sort_wishlist_by_date_handler(message):
        user_id = message.chat.id
        database = read_database()

        wishlist = read_wishlist(user_id)

        sorted_wishlist = sort_wishlist_by_date(wishlist, database)
        markup_inline = types.InlineKeyboardMarkup(row_width=2)
        for game in sorted_wishlist:
            price = f"{game['Price']}" if game['Price'] != 0.0 else 'Free'
            markup_inline.add(
                types.InlineKeyboardButton(f"{game['Name']} - {price}", callback_data=f"wishlist_{game['Name']}"))

        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        itembtn_sort = types.KeyboardButton('Sort')
        itembtn_view = types.KeyboardButton('View Wishlist')
        itembtn_back = types.KeyboardButton('Back')
        markup.add(itembtn_view, itembtn_sort, itembtn_back)

        bot.send_message(message.chat.id, "Sorted Wishlist by Release date:", reply_markup=markup_inline)
        bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)

    @bot.message_handler(func=lambda message: message.text == "Sort by reviews")
    def sort_wishlist_by_reviews_handler(message):
        user_id = message.from_user.id
        database = read_database()

        wishlist = read_wishlist(user_id)

        sorted_wishlist = sort_wishlist_by_reviews(wishlist, database)
        markup_inline = types.InlineKeyboardMarkup(row_width=2)
        for game in sorted_wishlist:
            price = f"{game['Price']}" if game['Price'] != 0.0 else 'Free'
            markup_inline.add(
                types.InlineKeyboardButton(f"{game['Name']} - {price}", callback_data=f"wishlist_{game['Name']}"))

        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        itembtn_sort = types.KeyboardButton('Sort')
        itembtn_view = types.KeyboardButton('View Wishlist')
        itembtn_back = types.KeyboardButton('Back')
        markup.add(itembtn_view, itembtn_sort, itembtn_back)

        bot.send_message(message.chat.id, "Sorted Wishlist by Total Reviews:", reply_markup=markup_inline)
        bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)

    @bot.message_handler(func=lambda message: message.text == "Sort by alhpabet")
    def sort_wishlist_by_alphabet(message):
        user_id = message.chat.id
        wishlist = read_wishlist(user_id)
        sorted_wishlist = sorted(wishlist, key=lambda x: x.get('Name', '').lower())  # Sort by 'Name' alphabetically

        markup_inline = types.InlineKeyboardMarkup(row_width=2)
        for game in sorted_wishlist:
            price = f"{game['Price']}" if game['Price'] != 0.0 else 'Free'
            markup_inline.add(
                types.InlineKeyboardButton(f"{game['Name']} - {price}", callback_data=f"wishlist_{game['Name']}"))

        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        itembtn_sort = types.KeyboardButton('Sort')
        itembtn_view = types.KeyboardButton('View Wishlist')
        itembtn_back = types.KeyboardButton('Back')
        markup.add(itembtn_view, itembtn_sort, itembtn_back)

        bot.send_message(message.chat.id, "Sorted Wishlist by alphabet:", reply_markup=markup_inline)
        bot.send_message(message.chat.id, "Choose an option:", reply_markup=markup)

        # Handler for "Count Tags" button, calculates and displays top 10 tags in the wishlist
        @bot.message_handler(func=lambda message: message.text == "Count Tags")
        def handle_tag_count(message):
            user_id = message.chat.id
            wishlist = read_wishlist(user_id)
            tag_counter = Counter()
            tag_to_games = {}

            game_ids = [game['ID'] for game in wishlist]

            for game_id in game_ids:
                games = find_game_by_exact_id(game_id, read_database())
                if games:
                    game = games[0]
                    tags = game.get('TopTags', [])
                    for tag in tags:
                        if tag not in tag_to_games:
                            tag_to_games[tag] = []
                        tag_to_games[tag].append(game['Name'])
                    tag_counter.update(tags)

            # Plotting the top 10 tags
            fig, ax = plt.subplots(figsize=(12, 8))
            tags, counts = zip(*tag_counter.most_common(10))
            bars = ax.barh(tags, counts, color='skyblue')
            ax.set_xlabel('Count')
            ax.set_title('Top 10 Tags in Wishlist Games')
            ax.invert_yaxis()

            for bar in bars:
                width = bar.get_width()
                ax.text(width + 0.5, bar.get_y() + bar.get_height() / 2, f'{width}', ha='center', va='center',
                        fontsize=12)

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)

            tag_list_text = "Top 10 Tags in Wishlist Games\n\n"
            for tag, count in tag_counter.most_common(10):
                games = ', '.join(tag_to_games[tag])
                tag_list_text += f"{tag}: {games}\n\n"

            MAX_MESSAGE_LENGTH = 4096
            messages = [tag_list_text[i:i + MAX_MESSAGE_LENGTH] for i in
                        range(0, len(tag_list_text), MAX_MESSAGE_LENGTH)]

            bot.send_photo(message.chat.id, buf, caption="Top 10 Tags in Wishlist Games")

            for msg in messages:
                bot.send_message(message.chat.id, msg)

            plt.close(fig)
            buf.close()

        # Handler for "Calculate Total Price" button, displays region options for price calculation
        @bot.message_handler(func=lambda message: message.text == "Calculate Total Price")
        def handle_total_price(message):
            markup = types.InlineKeyboardMarkup()
            button_ru = types.InlineKeyboardButton("🇷🇺", callback_data="price_ru")
            button_ua = types.InlineKeyboardButton("🇺🇦", callback_data="price_ua")
            button_tr = types.InlineKeyboardButton("🇹🇷", callback_data="price_tr")
            button_kz = types.InlineKeyboardButton("🇰🇿", callback_data="price_kz")
            button_pl = types.InlineKeyboardButton("🇵🇱", callback_data="price_pl")
            button_cn = types.InlineKeyboardButton("🇨🇳", callback_data="price_cn")
            markup.add(button_ru, button_ua, button_tr, button_kz, button_pl, button_cn)
            bot.send_message(message.chat.id, "Select region:", reply_markup=markup)

        # Callback handler for region price calculation, calculates and compares prices
        @bot.callback_query_handler(func=lambda call: call.data.startswith("price_"))
        def handle_price_region(call):
            region_code = call.data.split('_')[1]
            user_id = call.message.chat.id
            wishlist = read_wishlist(user_id)

            game_ids = [game['ID'] for game in wishlist]

            game_info = []
            for game_id in game_ids:
                games = find_game_by_exact_id(game_id, read_database())
                if games:
                    game = games[0]
                    game_info.append((game['ID'], game['Name'], game['Price'], game.get('ReleaseDate')))
            total_price, currency, available_games, unavailable_games, free_games, upcoming_games = calculate_regional_prices(
                game_info, region_code)
            us_total_price = calculate_us_prices(game_info, unavailable_games)
            total_price_usd = convert_to_usd(total_price, currency)

            region_names = {
                "ru": "Russia",
                "ua": "Ukraine",
                "tr": "Turkey",
                "kz": "Kazakhstan",
                "pl": "Poland",
                "cn": "China"
            }
            currency_symbols = {
                "RUB": "₽",
                "UAH": "₴",
                "TRY": "₺",
                "KZT": "₸",
                "PLN": "zł",
                "CNY": "¥",
                "USD": "$"
            }

            region_name = region_names.get(region_code, "Unknown region")
            currency_symbol = currency_symbols.get(currency, "$")

            # Plotting the price comparison
            fig, ax = plt.subplots(figsize=(6, 12))
            prices = [us_total_price, total_price_usd]
            labels = ['US Region', region_name]
            bar_width = 0.6
            bar_positions = range(len(prices))

            bars = ax.bar(bar_positions, prices, color=['blue', 'red'],
                          width=bar_width)
            ax.set_ylabel('Total Price in USD')
            ax.set_title('Price Comparison of Wishlist Games')
            ax.set_ylim(0, max(prices) * 1.2)
            ax.set_xticks(bar_positions)
            ax.set_xticklabels(labels)

            for bar in bars:
                yval = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2, yval + 1, f'{yval:.2f}', ha='center', va='bottom',
                        fontsize=12)

            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)

            bot.send_photo(call.message.chat.id, buf, caption=(
                f"Total price of wishlist games available in {region_name}, but priced in the US region: ${us_total_price:.2f}\n\n"
                f"Total price of games in {region_name}: {currency_symbol}{total_price:.2f} (~${total_price_usd:.2f})\n\n"
                f"Available games:\n{('\n'.join(available_games)) if available_games else 'All games are available.'}\n\n"
                f"Free games:\n{('\n'.join(free_games)) if free_games else 'No free games.'}\n\n"
                f"Upcoming games:\n{('\n'.join(upcoming_games)) if upcoming_games else 'No upcoming games.'}\n\n"
                f"Unavailable games:\n{('\n'.join(unavailable_games)) if unavailable_games else 'All games are available.'}\n\n"
            ))

            plt.close(fig)
            buf.close()


    # Function to convert the price to USD based on the given currency
    def convert_to_usd(amount, currency):
        usd_rate = exchange_rates.get(currency, 1)
        return amount * usd_rate

    # Function to calculate regional prices and return various details
    def calculate_regional_prices(game_info, region):
        total_price = 0
        currency = "USD"
        available_games = []
        unavailable_games = []
        free_games = []
        upcoming_games = []

        for game_id, game_name, game_price, release_date in game_info:
            if game_price.lower() == "free":
                free_games.append(game_name)
                continue

            if is_upcoming_game(release_date):
                upcoming_games.append(game_name)
                continue

            price_info, cur, available = get_steam_price(game_id, region)
            if available:
                total_price += price_info
                currency = cur
                available_games.append(game_name)
            else:
                unavailable_games.append(game_name)

        return total_price, currency, available_games, unavailable_games, free_games, upcoming_games

    # Function to check if the game is upcoming based on the release date
    def is_upcoming_game(release_date):
        try:
            if release_date.lower() == "coming soon":
                return True
            release_date = datetime.strptime(release_date, "%b %d, %Y")
            return release_date > datetime.now()
        except ValueError:
            return False

    # Function to get the price of the game from Steam API based on region
    def get_steam_price(game_id, region):
        api_url = f"https://store.steampowered.com/api/appdetails?appids={game_id}&cc={region}&filters=price_overview"
        response = requests.get(api_url)
        data = response.json()

        try:
            if isinstance(data, dict) and data[str(game_id)]['success']:
                price_data = data[str(game_id)]['data']['price_overview']
                price = price_data['final'] / 100.0
                currency = price_data['currency']
                return price, currency, True
            return 0, "USD", False
        except (KeyError, TypeError):
            return 0, "USD", False

    # Function to calculate the total price of US games
    def calculate_us_prices(game_info, unavailable_games):
        total_price = 0
        for game_id, game_name, game_price, release_date in game_info:
            if game_name in unavailable_games:
                continue
            if game_price.lower() == "free" or is_upcoming_game(release_date):
                continue
            price_value = float(game_price.replace("$", "")) if game_price.startswith("$") else 0
            total_price += price_value
        return total_price

    # Function to find a game by exact name in the wishlist
    def find_game_by_exact_name_wish(game_name, user_id):
        wishlist = read_wishlist(user_id)
        for game in wishlist:
            if game['Name'] == game_name:
                return game
        return None

    # Callback handler to show game details when selected from the wishlist
    @bot.callback_query_handler(func=lambda call: call.data.startswith('wishlist_'))
    def show_game_details(call):
        game_name = call.data.split('_', 1)[1]
        game_data = find_game_by_exact_name_wish(game_name, call.message.chat.id)
        if game_data:
            game_info = find_game_by_exact_name(game_name, read_database())
            if game_info:
                game_info = game_info[0][0]
                image_url = game_info['ImageURL']
                total_reviews = game_info['PositiveReviews'] + game_info['NegativeReviews']
                positive_percentage = (game_info['PositiveReviews'] / total_reviews * 100) if total_reviews > 0 else 0
                developer = ", ".join(game_info['Developer']) if isinstance(game_info['Developer'], list) else \
                    game_info['Developer']
                publisher = ", ".join(game_info['Publisher']) if isinstance(game_info['Publisher'], list) else \
                    game_info['Publisher']
                tags = ", ".join(game_info['TopTags']) if game_info['TopTags'] else "No tags found"
                price = f"{game_info['Price']}" if game_info['Price'] != "Free" else 'Free'
                day_peak = game_info.get('DayPeak', 'N/A')
                platforms = game_info.get('Platforms', 'N/A')
                href = f"https://store.steampowered.com/app/{game_info['ID']}"

                # Escape special HTML characters
                def escape_html(text):
                    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

                name = escape_html(game_info['Name'])
                short_description = escape_html(game_info['ShortDesc'])
                developer = escape_html(developer)
                publisher = escape_html(publisher)
                release_date = escape_html(game_info['ReleaseDate'])

                caption = (
                    f"<b>{name}</b>\n\n"
                    f"<i>{short_description}</i>\n\n"
                    f"<b>Total reviews:</b>        {total_reviews:,} ({positive_percentage:.2f}% positive)\n"
                    f"<b>Release date:</b>           {release_date}\n"
                    f"<b>Developer:</b>               {developer}\n"
                    f"<b>Publisher:</b>                 {publisher}\n\n"
                    f"<b>Tags:</b>     {tags}\n"
                    f"<b>Price:</b>     {price}\n"
                    f"<b>Max Online Yesterday:</b>  {day_peak}\n"
                    f"<b>Platforms:</b>  {platforms}\n"
                    f"{href}"
                )

                if image_url:
                    bot.send_photo(call.message.chat.id, image_url, caption=caption, parse_mode='HTML')
                else:
                    bot.send_message(call.message.chat.id, caption, parse_mode='HTML')

                # Add buttons for removing from wishlist or showing available languages
                markup_inline = types.InlineKeyboardMarkup()
                markup_inline.add(
                    types.InlineKeyboardButton(f"Remove {game_info['Name']} from Wishlist",
                                               callback_data=f"remove_{game_info['Name']}"),
                    types.InlineKeyboardButton(f"Show available languages",
                                               callback_data=f"languages_{game_info['ID']}")
                )

                # If user is the admin, add button for updating game info
                if call.message.chat.id == TgID:
                    markup_inline.add(types.InlineKeyboardButton(f"Update game info",
                                                                 callback_data=f"update_{game_info['ID']}"))

                bot.send_message(call.message.chat.id, "Would you like to remove this game from your Wishlist?",
                                 reply_markup=markup_inline)
            else:
                bot.send_message(call.message.chat.id, f"Information about '{game_name}' not found in the database.")
        else:
            bot.send_message(call.message.chat.id, f"Game '{game_name}' not found in your Wishlist.")

    # Callback handler to show game details when selected from the list
    @bot.callback_query_handler(func=lambda call: call.data.startswith('list_'))
    def show_game_details_list(call):
        print("Processing list callback...")
        game_id = call.data.split('_', 1)[1]
        print("Game ID extracted:", game_id)
        database = read_database()
        print("Database loaded.")

        game = database.get(game_id)
        print("Game found:", game)

        if game:
            image_url = game.get('ImageURL', None)
            total_reviews = game['PositiveReviews'] + game['NegativeReviews']
            positive_percentage = (game['PositiveReviews'] / total_reviews) * 100 if total_reviews > 0 else 0
            developer = ", ".join(game['Developer']) if isinstance(game['Developer'], list) else game['Developer']
            publisher = ", ".join(game['Publisher']) if isinstance(game['Publisher'], list) else game['Publisher']
            tags = ", ".join(game['TopTags']) if game['TopTags'] else "No tags found"
            price = f"{game['Price']}" if game['Price'] != "Free" else 'Free'
            day_peak = game.get('DayPeak', 'N/A')
            platforms = game.get('Platforms', 'N/A')
            href = f"https://store.steampowered.com/app/{game['ID']}"

            # Escape special HTML characters
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
                f"<b>Tags:</b>     {tags}\n"
                f"<b>Price:</b>     {price}\n"
                f"<b>Max Online Yesterday:</b>  {day_peak}\n"
                f"<b>Platforms:</b>  {platforms}\n"
                f"{href}"
            )

            if image_url:
                bot.send_photo(call.message.chat.id, image_url, caption=caption, parse_mode='HTML')
            else:
                bot.send_message(call.message.chat.id, caption, parse_mode='HTML')

            # Add buttons for removing or adding to wishlist and showing available languages
            markup_inline = types.InlineKeyboardMarkup()
            if check_wishlist(call.message.chat.id, game['Name']):
                markup_inline.add(types.InlineKeyboardButton(f"Remove {game['Name']} from Wishlist",
                                                             callback_data=f"remove_{game['Name']}"),
                                  types.InlineKeyboardButton(f"Show available languages",
                                                             callback_data=f"languages_{game['ID']}"))
                bot.send_message(call.message.chat.id, "Would you like to remove this game from your Wishlist?",
                                 reply_markup=markup_inline)
            else:
                markup_inline.add(
                    types.InlineKeyboardButton(f"Add {game['Name']} to Wishlist", callback_data=f"add_{game['Name']}"),
                    types.InlineKeyboardButton(f"Show available languages",
                                               callback_data=f"languages_{game['ID']}")
                )
                bot.send_message(call.message.chat.id, "Would you like to add this game to your Wishlist?",
                                 reply_markup=markup_inline)
        else:
            bot.send_message(call.message.chat.id, f"No details found for the game ID: {game_id}")

    # Callback handler to show available languages for the selected game
    @bot.callback_query_handler(func=lambda call: call.data.startswith('languages_'))
    def show_available_languages(call):
        game_id = call.data.split('_', 1)[1]
        database = read_database()
        game = database.get(game_id)

        if game:
            languages_sub = game.get('LanguagesSub', [])
            languages_audio = game.get('LanguagesAudio', [])

            languages_text = (
                f"<b>Available Languages for {game['Name']}:</b>\n\n"
                f"<b>Subtitles:</b>\n{('\n'.join(languages_sub)) if languages_sub else 'No subtitles available.'}\n\n"
                f"<b>Audio:</b>\n{('\n'.join(languages_audio)) if languages_audio else 'No audio available.'}"
            )

            bot.send_message(call.message.chat.id, languages_text, parse_mode='HTML')
        else:
            bot.send_message(call.message.chat.id, "Game details not found.")

    # Function to search games by name
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

    # Function to search games by tag
    def search_game_by_tag(message):
        search_msg = bot.send_message(message.chat.id, f"Searching for games by tag '{message.text}'...")
        games = find_games_by_tag(message.text, read_database())[:20]
        markup = types.InlineKeyboardMarkup()
        for game_id, (game_data, _) in games:
            callback_data = f'list_{game_id}'
            markup.add(types.InlineKeyboardButton(game_data["Name"], callback_data=callback_data))
        if games:
            bot.edit_message_text("Select a game:", message.chat.id, search_msg.message_id, reply_markup=markup)
        else:
            bot.edit_message_text("No games found with that tag.", message.chat.id, search_msg.message_id)

    # Callback handler to add a game to the wishlist
    @bot.callback_query_handler(func=lambda call: call.data.startswith('add_'))
    def add_to_wishlist(call):
        game_name = call.data.split('_', 1)[1]
        database = read_database()
        games = find_game_by_exact_name(game_name, database)

        if games:
            game_data = games[0][0]
            game_data_end = {
                'ID': game_data['ID'],
                'Name': game_data['Name'],
                'Price': game_data['Price']
            }
            add_game_to_wishlist(call.message.chat.id, game_data_end)
            bot.edit_message_text(f"{game_data['Name']} added to your wishlist.", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "Game not found in database.")

    # Handler for "Remove Game from Wishlist" button, displays wishlist for removing a game
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

    # Callback handler to remove a game from the wishlist
    @bot.callback_query_handler(func=lambda call: call.data.startswith('remove_'))
    def remove_game_from_wishlist_callback(call):
        game_name = call.data.split('_', 1)[1]
        remove_game_from_wishlist(call.message.chat.id, game_name)
        bot.answer_callback_query(call.id, f"{game_name} removed from your wishlist.")
        bot.edit_message_text("Game removed from your wishlist.", call.message.chat.id, call.message.message_id)

    # Handler for "Download Wishlist" button, displays format options for downloading the wishlist
    @bot.message_handler(func=lambda message: message.text == "Download Wishlist")
    def choose_download_format(message):
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        itembtn_txt = types.KeyboardButton('Download as TXT')
        itembtn_json = types.KeyboardButton('Download as JSON')
        itembtn_yaml = types.KeyboardButton('Download as YAML')
        itembtn_back = types.KeyboardButton('Back')
        markup.add(itembtn_txt, itembtn_json, itembtn_yaml, itembtn_back)

        bot.send_message(message.chat.id, "Choose a format to download your wishlist:", reply_markup=markup)

    # Handler for format selection, downloads the wishlist in the chosen format
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

        os.remove(filename)

    # Handler for "Import Wishlist" button, prompts user to send the wishlist file
    @bot.message_handler(func=lambda message: message.text == "Import Wishlist")
    def import_wishlist(message):
        user_id = message.chat.id
        msg = bot.send_message(user_id, "Please send the wishlist file.")

        bot.register_next_step_handler(msg, process_import_file)

    # Function to process the imported wishlist file
    def process_import_file(message):
        user_id = message.chat.id
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            file_extension = message.document.file_name.split('.')[-1].lower()

            if file_extension == 'txt':
                imported_data = read_txt_file(downloaded_file)
            elif file_extension == 'yaml' or file_extension == 'yml':
                imported_data = read_yaml_file(downloaded_file)
            else:
                bot.send_message(user_id, "Unsupported file format. Please upload a txt or yaml file.")
                return

            update_wishlist(user_id, imported_data)

            bot.send_message(user_id, "Wishlist imported and updated successfully.")

        except Exception as e:
            bot.send_message(user_id, f"An error occurred: {str(e)}")
            print(f"An error occurred: {str(e)}")

    # Function to update game information using Steam API
    def update_game_info(appid):
        api_key = config.SteamKey
        session = create_session_with_retries()
        process_game(appid, session, api_key)

        with open('detailed_steam_games.json', 'r', encoding='utf-8') as new_data_file:
            new_data = json.load(new_data_file)

        transformed_file_path = 'SteamAPI/JSON/detailed_games_transformed.json'
        with open(transformed_file_path, 'r', encoding='utf-8') as transformed_data_file:
            transformed_data = json.load(transformed_data_file)

        for game in new_data:
            game_id = game['ID']
            transformed_data[str(game_id)] = game

        with open(transformed_file_path, 'w', encoding='utf-8') as transformed_data_file:
            json.dump(transformed_data, transformed_data_file, indent=4)

        os.remove('detailed_steam_games.json')
        asyncio.run(preload_database())

    # Callback handler to update game information from Steam API
    @bot.callback_query_handler(func=lambda call: call.data.startswith('update_'))
    def update_game_info_callback(call):
        game_id = call.data.split('_', 1)[1]
        user_id = call.message.chat.id
        if user_id == TgID:
            update_game_info(game_id)
            bot.answer_callback_query(call.id, f"Game information for ID {game_id} has been updated.")
        else:
            bot.answer_callback_query(call.id, "You are not authorized to update game information.")

    # Callback handler to show game details when selected from the list
    @bot.callback_query_handler(func=lambda call: call.data.startswith('list_'))
    def show_game_details_list(call):
        print("Processing list callback...")
        game_id = call.data.split('_', 1)[1]
        print("Game ID extracted:", game_id)
        database = read_database()
        print("Database loaded.")

        game = database.get(game_id)
        print("Game found:", game)

        if game:
            image_url = game.get('ImageURL', None)
            total_reviews = game['PositiveReviews'] + game['NegativeReviews']
            positive_percentage = (game['PositiveReviews'] / total_reviews) * 100 if total_reviews > 0 else 0
            developer = ", ".join(game['Developer']) if isinstance(game['Developer'], list) else game['Developer']
            publisher = ", ".join(game['Publisher']) if isinstance(game['Publisher'], list) else game['Publisher']
            tags = ", ".join(game['TopTags']) if game['TopTags'] else "No tags found"
            price = f"{game['Price']}" if game['Price'] != "Free" else 'Free'
            day_peak = game.get('DayPeak', 'N/A')
            platforms = game.get('Platforms', 'N/A')
            href = f"https://store.steampowered.com/app/{game['ID']}"

            # Escape special HTML characters
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
                f"<b>Tags:</b>     {tags}\n"
                f"<b>Price:</b>     {price}\n"
                f"<b>Max Online Yesterday:</b>  {day_peak}\n"
                f"<b>Platforms:</b>  {platforms}\n"
                f"{href}"
            )

            if image_url:
                bot.send_photo(call.message.chat.id, image_url, caption=caption, parse_mode='HTML')
            else:
                bot.send_message(call.message.chat.id, caption, parse_mode='HTML')

            # Add buttons for removing or adding to wishlist and showing available languages
            markup_inline = types.InlineKeyboardMarkup()
            if check_wishlist(call.message.chat.id, game['Name']):
                markup_inline.add(types.InlineKeyboardButton(f"Remove {game['Name']} from Wishlist",
                                                             callback_data=f"remove_{game['Name']}"),
                                  types.InlineKeyboardButton(f"Show available languages",
                                                             callback_data=f"languages_{game['ID']}"))
                bot.send_message(call.message.chat.id, "Would you like to remove this game from your Wishlist?",
                                 reply_markup=markup_inline)
            else:
                markup_inline.add(
                    types.InlineKeyboardButton(f"Add {game['Name']} to Wishlist", callback_data=f"add_{game['Name']}"),
                    types.InlineKeyboardButton(f"Show available languages",
                                               callback_data=f"languages_{game['ID']}")
                )
                bot.send_message(call.message.chat.id, "Would you like to add this game to your Wishlist?",
                                 reply_markup=markup_inline)
        else:
            bot.send_message(call.message.chat.id, f"No details found for the game ID: {game_id}")