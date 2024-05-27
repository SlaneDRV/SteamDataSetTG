import json
import os
from difflib import SequenceMatcher
import asyncio
import yaml

# Global variable for database storage
DATABASE = None

# Preload the database function
async def preload_database():
    global DATABASE
    try:
        with open('../SteamAPI/JSON/detailed_games_transformed.json', 'r', encoding='utf-8') as f:
            DATABASE = json.load(f)
            print("Database preloaded successfully.")
    except FileNotFoundError:
        print("JSON database file not found.")
    except json.JSONDecodeError as e:
        print("Error decoding JSON data:", e)

# Call the preload function on bot startup
asyncio.run(preload_database())

# Function to read the database
def read_database():
    global DATABASE
    if DATABASE is None:
        print("Database is not loaded.")
        return None
    else:
        print("Connected to JSON database successfully.")
        return DATABASE

# Functions to find games by various criteria
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

# Function to find a game by exact name
def find_game_by_exact_name(game_name, database):
    print("Search game by exact name has been started.")
    results = []
    search_query = game_name.lower().strip()
    for game_id, game_data in database.items():
        name = game_data["Name"].lower().strip()
        if name == search_query:
            total_reviews = game_data["PositiveReviews"] + game_data["NegativeReviews"]
            results.append((game_data, total_reviews))

    sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
    print("Search game by exact name is done.")
    return sorted_results[:1]

# Function to format the game list
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

# Wishlist directory management
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
            return True  # Game already in wishlist
    return False  # Game not found in wishlist

def get_wishlist_count(user_id):
    wishlist = read_wishlist(user_id)
    return len(wishlist)

def remove_game_from_wishlist(user_id, game_name):
    print("Remove game from wishlist of user: ", user_id)
    wishlist = read_wishlist(user_id)
    new_wishlist = [game for game in wishlist if game['Name'] != game_name]
    save_wishlist(user_id, new_wishlist)
    return new_wishlist

# Functions for generating wishlist files
def generate_wishlist_file_txt(user_id):
    wishlist = read_wishlist(user_id)
    filename = f'wishlist_{user_id}.txt'
    with open(filename, 'w', encoding='utf-8') as file:
        for game in wishlist:
            price = f"{game['Price']}" if game['Price'] != 0.0 else 'Free'
            file.write(f"{game['ID']}: {game['Name']} - {price}\n")
    return filename

def filter_wishlist_fields(wishlist):
    filtered_wishlist = []
    for game in wishlist:
        filtered_game = {
            'ID': game['ID'],
            'Name': game['Name'],
            'Price': f"{game['Price']}" if game['Price'] != 0.0 else 'Free'
        }
        filtered_wishlist.append(filtered_game)
    return filtered_wishlist

def generate_wishlist_file_json(user_id):
    wishlist = read_wishlist(user_id)
    filtered_wishlist = filter_wishlist_fields(wishlist)
    filename = f'wishlist_{user_id}.json'
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(filtered_wishlist, file, ensure_ascii=False, indent=4)
    return filename

def generate_wishlist_file_yaml(user_id):
    wishlist = read_wishlist(user_id)
    filtered_wishlist = filter_wishlist_fields(wishlist)
    filename = f'wishlist_{user_id}.yaml'
    with open(filename, 'w', encoding='utf-8') as file:
        yaml.dump(filtered_wishlist, file, allow_unicode=True)
    return filename

def read_json_wishlist(user_id):
    filename = get_wishlist_path(user_id)
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            # Читаем существующие данные из файла
            existing_data = json.load(file)
    except FileNotFoundError:
        # Если файл не существует, возвращаем пустой список
        return []

    # Возвращаем существующие данные
    return existing_data


def import_wishlist(user_id, imported_data):
    # Читаем существующие данные из вишлиста
    existing_data = read_json_wishlist(user_id)

    # Добавляем импортированные данные к существующим данным
    existing_data.extend(imported_data)

    # Записываем обновленные данные обратно в файл
    filename = f"{user_id}_wishlist.json"
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)


