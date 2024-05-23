import json

def analyze_games(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            games = json.load(file)  # Load all games from the file

        total_games = len(games)
        games_with_reviews = []  # List to hold games with more than 5000 reviews combined

        for game in games:
            # Calculate the total reviews if available and check if it exceeds 5000
            if game.get("PositiveReviews", 0) > 5000:
                games_with_reviews.append(game["Name"])

        return {
            "Total games": total_games,
            "Number of games with > 5000 reviews": len(games_with_reviews),
            "Games list": games_with_reviews
        }

    except FileNotFoundError:
        print(f"Файл не найден: {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Ошибка чтения JSON в файле: {file_path}")
        return {}

# Paths to JSON files with game information
detailed_file_path = 'FileCheckNEdit/detailed_games_actual.json'
invalid_file_path = 'invalid_games.json'

# Analyze detailed and invalid games separately
detailed_result = analyze_games(detailed_file_path)
invalid_result = analyze_games(invalid_file_path)

# Print the results for both files
print("Detailed Games Analysis:")
print(json.dumps(detailed_result, indent=4, ensure_ascii=False))
print("Invalid Games Analysis:")
print(json.dumps(invalid_result, indent=4, ensure_ascii=False))
