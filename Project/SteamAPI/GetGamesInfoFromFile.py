import json

def analyze_games(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            games = json.load(file)  # Загружаем все игры из файла

        total_games = len(games)
        games_with_reviews = []

        for game in games:
            if game.get("PositiveReviews", 0) > 5000:
                games_with_reviews.append(game["Name"])

        return {
            "Total games": total_games,
            "Number of games with > 5000 positive reviews": len(games_with_reviews),
            "Games list": games_with_reviews
        }

    except FileNotFoundError:
        print("Файл не найден.")
        return {}
    except json.JSONDecodeError:
        print("Ошибка чтения JSON.")
        return {}

# Путь к файлу JSON с информацией об играх
file_path = 'detailed_steam_games.json'

# Получаем и печатаем результаты анализа
result = analyze_games(file_path)
print(json.dumps(result, indent=4, ensure_ascii=False))
