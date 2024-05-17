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
    # Приводим имя игры к нижнему регистру для регистронезависимого поиска
    search_query = game_name.lower()
    for game_id, game_data in database.items():
        # Проверяем, содержится ли поисковый запрос в названии игры (также в нижнем регистре)
        if search_query in game_data["name"].lower():
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

def format_game_list(games):
    message = ""
    for i, item in enumerate(games, start=1):
        if isinstance(item, dict):  # Если элемент списка - словарь
            game_data = item
        elif isinstance(item, tuple) and len(item) > 0:  # Если элемент списка - кортеж
            game_data = item[0]  # Предполагаем, что данные игры находятся в первом элементе кортежа
        else:
            continue  # Пропускаем некорректные данные
        message += f"{i}. {game_data['name']}\n"
    return message

