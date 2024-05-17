import json

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
#search name
def find_games_by_name(game_name, database):
    results = []
    for game_id, game_data in database.items():
        if game_data["name"].lower() == game_name.lower():
            results.append(game_data)
    return results

def find_games_by_category(category, database):
    results = []
    for game_id, game_data in database.items():
        if isinstance(game_data["tags"], list) or isinstance(game_data["tags"], dict):
            if any(category.lower() in tag.lower() for tag in (game_data["tags"] if isinstance(game_data["tags"], list) else game_data["tags"].keys())):
                results.append((game_data, game_data["positive"] - game_data["negative"]))
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:20]

def format_game_list(list):
    message = ""
    for i, (game_data, _) in enumerate(list, start=1):
        message += f"{i}. {game_data['name']}\n"
    return message
