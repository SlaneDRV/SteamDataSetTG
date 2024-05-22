import json
import os
from difflib import SequenceMatcher
import asyncio

# Глобальная переменная для хранения данных базы данных
DATABASE = None

# Функция для предварительной загрузки базы данных
async def preload_database():
    global DATABASE
    try:
        with open('detailed_games.json', 'r', encoding='utf-8') as f:
            DATABASE = json.load(f)
            print(type(DATABASE))
            print("Database preloaded successfully.")
    except FileNotFoundError:
        print("JSON database file not found.")
    except json.JSONDecodeError as e:
        print("Error decoding JSON data:", e)

# Вызов функции предварительной загрузки базы данных при запуске бота
asyncio.run(preload_database())

# Остальной код без изменений...
def read_database():
    global DATABASE
    if DATABASE is None:
        print("Database is not loaded.")
        return None
    else:
        print("Connected to JSON database successfully.")
        return DATABASE


def find_games_by_name(game_name, database):
    print("Search games by name has been started.")
    results = {}
    search_query = game_name.lower().replace(" ", "")
    for game_id, game_data in database.items():
        name = game_data["Name"].lower().replace(" ", "")
        ratio = SequenceMatcher(None, search_query, name).ratio()
        if ratio > 0.7 or search_query in name:
            total_reviews = game_data["PositiveReviews"] + game_data["NegativeReviews"]
            results[game_id] = (game_data, total_reviews)

    sorted_results = sorted(results.items(), key=lambda x: x[1][1], reverse=True)
    print("Search games by name is done.")
    return sorted_results[:10]

def find_games_by_category(category, database):
    print("Search games by category has been started.")
    results = {}
    for game_id, game_data in database.items():
        if isinstance(game_data.get("TopTags"), list):
            top_tags = game_data["TopTags"]
            if any(category.lower() in tag.lower() for tag in top_tags):
                total_reviews = game_data["PositiveReviews"] + game_data["NegativeReviews"]
                results[game_id] = (game_data, total_reviews)
    sorted_results = sorted(results.items(), key=lambda x: x[1][1], reverse=True)
    print("Search games by category is done.")
    return sorted_results[:20]



#search game for showing details
def find_game_by_exact_name(game_name, database):
    print("Search game by exact name has been started.")
    results = []
    search_query = game_name.lower().strip()  # Приводим запрос к нижнему регистру и убираем лишние пробелы
    for game_id, game_data in database.items():
        name = game_data["Name"].lower().strip()  # Приводим название игры к нижнему регистру и убираем лишние пробелы
        if name == search_query:
            total_reviews = game_data["PositiveReviews"] + game_data["NegativeReviews"]
            results.append((game_data, total_reviews))

    # Сортировка результатов по количеству отзывов
    sorted_results = sorted(results, key=lambda x: x[1], reverse=True)

    print("Search game by exact name is done.")
    return sorted_results[:1]  # Возвращаем только первый результат (если есть)



def format_game_list(games):
    message = ""
    for i, (game_data, total_reviews) in enumerate(games, start=1):
        if total_reviews > 0:
            positive_percentage = (game_data["PositiveReviews"] / total_reviews) * 100
        else:
            positive_percentage = 0
        message += (f"{i}. {game_data['Name']} (Reviews: {total_reviews})\n"
                    f"\tPositive: {positive_percentage:.2f}%\n")
    return message

WISHLIST_DIR = 'Wishlists'

if not os.path.exists(WISHLIST_DIR):
    os.makedirs(WISHLIST_DIR)

def get_wishlist_path(user_id):
    return os.path.join(WISHLIST_DIR, f'{user_id}_wishlist.json')


def read_wishlist(user_id):
    filename = get_wishlist_path(user_id)
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_wishlist(user_id, wishlist):
    filename = get_wishlist_path(user_id)
    with open(filename, 'w', encoding='utf-8') as file:
        print("Save wishlist for user: ", user_id)
        json.dump(wishlist, file, indent=4)

def add_game_to_wishlist(user_id, game):
    wishlist = read_wishlist(user_id)
    if game not in wishlist:
        wishlist.append(game)
        save_wishlist(user_id, wishlist)
        print("Add game to wishlist of user: ", user_id)
    return wishlist

def check_wishlist(user_id, game_name):
    wishlist = read_wishlist(user_id)
    for game in wishlist:
        if game['Name'] == game_name:
            return True  # Игра уже есть в вишлисте
    return False  # Игра не найдена в вишлисте

def get_wishlist_count(user_id):
    wishlist = read_wishlist(user_id)
    return len(wishlist)


def remove_game_from_wishlist(user_id, game_name):
    print("Remove game from wishlist of user: ", user_id)
    wishlist = read_wishlist(user_id)
    new_wishlist = [game for game in wishlist if game['Name'] != game_name]
    save_wishlist(user_id, new_wishlist)
    return new_wishlist

# Функция для генерации файла вишлиста
def generate_wishlist_file_txt(user_id):
    wishlist = read_wishlist(user_id)
    filename = f'wishlist_{user_id}.txt'
    with open(filename, 'w', encoding='utf-8') as file:
        for game in wishlist:
            price = f"{game['Price']}" if game['Price'] != 0.0 else 'Free'
            file.write(f"{game['ID']}: {game['Name']} - {price}\n")
    return filename



