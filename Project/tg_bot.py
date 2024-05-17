import telebot
import json
from telebot import types

token = '7132632075:AAH14iDGSS9-WKbcZ8N5tYRermCmla5nIdE'
bot = telebot.TeleBot(token)

# test text
def read_database():
    try:
        with open('games.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            print("Connected to JSON database successfully.")
            return data
    except FileNotFoundError:
        print("JSON database file not found.")
        return None
    except json.JSONDecodeError:
        print("Error decoding JSON data.")
        return None


# proverka identicznosti
def find_games_by_category(category, database):
    results = []
    final_result = []
    seen_names = set()  # Множество для отслеживания уникальных названий игр
    for game_id, game_data in database.items():
        game_name = game_data["name"]
        if game_name in seen_names:  # Пропустить, если игра уже добавлена в результаты
            continue
        if isinstance(game_data["tags"], list):
            if any(category.lower() in tag.lower() for tag in game_data["tags"]):
                results.append((game_name, game_data["positive"] - game_data["negative"]))
                seen_names.add(game_name)
        elif isinstance(game_data["tags"], dict):
            if any(category.lower() in tag.lower() for tag in game_data["tags"].keys()):
                results.append((game_name, game_data["positive"] - game_data["negative"]))
                seen_names.add(game_name)
    results.sort(key=lambda x: x[1], reverse=True)  # Sort by score (positive-negative)
    for result in results[:20] :
        final_result.append(result)
    return final_result  # Return only game data

#game name search function
def find_games_by_name(game_name, database):
    results = []
    for game_id, game_data in database.items():
        if game_data["name"].lower() == game_name.lower():
            results.append(game_data)
    return results

def format_game_list(games):
    message = ""
    for i, (game_data, _) in enumerate(games, start=1):
        message += f"{i}. {game_data['name']}\n"
    return message

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

@bot.message_handler(func=lambda message: message.text == "Find by name")
def find_by_name(message):
    bot.send_message(message.chat.id, "Please enter the name of the game you're looking for.")

@bot.message_handler(func=lambda message: message.text == "Find by category")
def find_by_category(message):
    bot.send_message(message.chat.id, "Please enter the category of the game you're looking for.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text.startswith("/"):
        return
    if message.text == "Find by name":
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
            bot.send_message(message.chat.id,f" {game_list}")
        else:
            bot.send_message(message.chat.id, "No games found for this category.")

        #name search
        category = message.text
        name = find_games_by_name(category, database)
        if name:
            bot.send_message(message.chat.id,f" {name}")
        else:
            bot.send_message(message.chat.id, "No games found for this name.")

if __name__ == '__main__':
    bot.infinity_polling()