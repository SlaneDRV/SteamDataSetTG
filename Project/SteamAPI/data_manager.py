import json
import os
from difflib import SequenceMatcher
import asyncio
import yaml

# Global variable to store the database
DATABASE = None

# Asynchronously preload the database from the JSON file
async def preload_database():
    global DATABASE
    try:
        with open("SteamAPI/JSON/detailed_games_transformed.json", 'r', encoding='utf-8') as f:
            DATABASE = json.load(f)
            print("Database preloaded successfully.")
    except FileNotFoundError:
        print("JSON database file not found.")
    except json.JSONDecodeError as e:
        print("Error decoding JSON data:", e)

# Run the preload_database coroutine to load the database at startup
asyncio.run(preload_database())

# Function to read the preloaded database
def read_database():
    global DATABASE
    if DATABASE is None:
        print("Database is not loaded.")
        return None
    else:
        print("Connected to JSON database successfully.")
        return DATABASE

# Function to find games by name
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

# Function to find games by tag
def find_games_by_tag(searchTag, database):
    print("Search games by tag has been started.")
    results = {}
    for game_id, game_data in database.items():
        if isinstance(game_data.get("TopTags"), list):
            top_tags = game_data["TopTags"]
            if any(searchTag.lower() in tag.lower() for tag in top_tags):
                total_reviews = game_data["PositiveReviews"] + game_data["NegativeReviews"]
                results[game_id] = (game_data, total_reviews)
    sorted_results = sorted(results.items(), key=lambda x: x[1][1], reverse=True)
    print("Search games by tag is done.")
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

# Function to format a list of games for display
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

# Directory for storing wishlists
WISHLIST_DIR = '../Wishlists'
if not os.path.exists(WISHLIST_DIR):
    os.makedirs(WISHLIST_DIR)

# Function to get the path of a user's wishlist
def get_wishlist_path(user_id):
    return os.path.join(WISHLIST_DIR, f'{user_id}_wishlist.json')

# Function to read a user's wishlist from file
def read_wishlist(user_id):
    filename = get_wishlist_path(user_id)
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Function to save a user's wishlist to file
def save_wishlist(user_id, wishlist):
    filename = get_wishlist_path(user_id)
    with open(filename, 'w', encoding='utf-8') as file:
        print("Save wishlist for user: ", user_id)
        json.dump(wishlist, file, indent=4)

# Function to add a game to a user's wishlist
def add_game_to_wishlist(user_id, game):
    wishlist = read_wishlist(user_id)
    if game not in wishlist:
        wishlist.append(game)
        save_wishlist(user_id, wishlist)
        print("Add game to wishlist of user: ", user_id)
    return wishlist

# Function to check if a game is in a user's wishlist
def check_wishlist(user_id, game_name):
    wishlist = read_wishlist(user_id)
    for game in wishlist:
        if game['Name'] == game_name:
            return True
    return False

# Function to get the count of games in a user's wishlist
def get_wishlist_count(user_id):
    wishlist = read_wishlist(user_id)
    return len(wishlist)

# Function to remove a game from a user's wishlist
def remove_game_from_wishlist(user_id, game_name):
    print("Remove game from wishlist of user: ", user_id)
    wishlist = read_wishlist(user_id)
    new_wishlist = [game for game in wishlist if game['Name'] != game_name]
    save_wishlist(user_id, new_wishlist)
    return new_wishlist

# Function to generate a wishlist file in text format
def generate_wishlist_file_txt(user_id):
    wishlist = read_wishlist(user_id)
    filename = f'wishlist_{user_id}.txt'
    with open(filename, 'w', encoding='utf-8') as file:
        for game in wishlist:
            price = f"{game['Price']}" if game['Price'] != 0.0 else 'Free'
            file.write(f"{game['ID']}: {game['Name']} - {price}\n")
    return filename

# Function to filter wishlist fields for exporting
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

# Function to generate a wishlist file in JSON format
def generate_wishlist_file_json(user_id):
    wishlist = read_wishlist(user_id)
    filtered_wishlist = filter_wishlist_fields(wishlist)
    filename = f'wishlist_{user_id}.json'
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(filtered_wishlist, file, ensure_ascii=False, indent=4)
    return filename

# Function to generate a wishlist file in YAML format
def generate_wishlist_file_yaml(user_id):
    wishlist = read_wishlist(user_id)
    filtered_wishlist = filter_wishlist_fields(wishlist)
    filename = f'wishlist_{user_id}.yaml'
    with open(filename, 'w', encoding='utf-8') as file:
        yaml.dump(filtered_wishlist, file, allow_unicode=True)
    return filename

# Function to read a user's wishlist from a JSON file
def read_json_wishlist(user_id):
    filename = get_wishlist_path(user_id)
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        return []

    return existing_data

# Function to find a game by exact ID
def find_game_by_exact_id(game_id, database):
    print("Search game by exact id has been started.")
    results = []
    search_query = str(game_id).strip()
    for db_game_id, game_data in database.items():
        db_game_id_str = str(game_data["ID"]).strip()
        if db_game_id_str == search_query:
            results.append(game_data)
    print("Search game by exact id is done.")
    return results[:1]

# Function to import a wishlist from external data
def import_wishlist(user_id, imported_data):
    existing_data = read_json_wishlist(user_id)

    existing_data.extend(imported_data)

    filename = get_wishlist_path(user_id)
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)

# Function to read a wishlist from a file
def read_wishlist_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON data from {filepath}: {e}")
        return []

# Function to merge wishlists
def merge_wishlists(user_id, imported_data):
    current_wishlist = read_wishlist(user_id)

    for game in imported_data:
        if game not in current_wishlist:
            current_wishlist.append(game)

    save_wishlist(user_id, current_wishlist)

# Function to update a user's wishlist with imported data
def update_wishlist(user_id, imported_data):
    current_wishlist = read_wishlist(user_id)

    for game in imported_data:
        game_id = game.get('ID')
        game_name = game.get('Name')
        game_price = game.get('Price')

        if game_id and game_name:
            existing_game_by_id = find_game_by_exact_id(game_id, DATABASE)
            existing_game_by_name = find_game_by_exact_name(game_name, DATABASE)

            if existing_game_by_id and existing_game_by_name:
                game_info = {
                    'ID': game_id,
                    'Name': game_name,
                    'Price': game_price
                }
                if game_info not in current_wishlist:
                    current_wishlist.append(game_info)
                else:
                    print(f"Game with ID {game_id} and Name {game_name} exists on the wishlist.")
            else:
                print(f"Game with ID {game_id} and Name {game_name} not found in the database.")
        else:
            print(f"Invalid game data received: ID={game_id}, Name={game_name}")

    save_wishlist(user_id, current_wishlist)

# Function to read a TXT file and parse the wishlist data
def read_txt_file(file_content):
    imported_data = []
    lines = file_content.decode('utf-8').strip().split('\n')
    for line in lines:
        last_dash_index = line.rfind(' - ')
        if last_dash_index != -1:
            id_and_name = line[:last_dash_index]
            price = line[last_dash_index + 3:]

            first_colon_index = id_and_name.find(':')
            if first_colon_index != -1:
                game_id = id_and_name[:first_colon_index].strip()
                game_name = id_and_name[first_colon_index + 1:].strip()
                game_info = {
                    'ID': int(game_id),
                    'Name': game_name,
                    'Price': price.strip()
                }
                imported_data.append(game_info)
            else:
                print(f"Error parsing line (ID and Name): {line}")
        else:
            print(f"Error parsing line (Price): {line}")

    return imported_data

# Function to read a YAML file and parse the wishlist data
def read_yaml_file(file_content):
    imported_data = yaml.safe_load(file_content)
    return imported_data if imported_data is not None else []