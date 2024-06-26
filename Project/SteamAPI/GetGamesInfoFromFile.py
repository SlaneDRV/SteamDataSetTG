import json


def analyze_games(file_path, specific_tag):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            games = json.load(file)

        total_games = len(games)
        games_with_reviews = []
        no_reviews_and_online = 0
        games_with_specific_tag = 0

        for game in games:
            total_reviews = game.get("PositiveReviews", 0) + game.get("NegativeReviews", 0)
            if total_reviews > 1000:
                games_with_reviews.append(game["Name"])

            if total_reviews == 0 and game.get("DayPeak", 0) == 0:
                no_reviews_and_online += 1

            if any(specific_tag.lower() in tag.lower() for tag in game.get("TopTags", [])):
                games_with_specific_tag += 1

        return {
            "Total games": total_games,
            "Number of games with 0 reviews and 0 online": no_reviews_and_online,
            f"Number of games with '{specific_tag}' tag": games_with_specific_tag,
            "Number of games with > 1000 reviews": len(games_with_reviews),
            "Games with > 1000 reviews": games_with_reviews
        }

    except FileNotFoundError:
        print(f"Файл не найден: {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Ошибка чтения JSON в файле: {file_path}")
        return {}


detailed_file_path = '../JSON/detailed_games_actual.json'
invalid_file_path = '../JSON/invalid_games_actual.json'

detailed_result = analyze_games(detailed_file_path, "rogue")
invalid_result = analyze_games(invalid_file_path,"")

print("Detailed Games Analysis:")
print(json.dumps(detailed_result, indent=4, ensure_ascii=False))
print("Invalid Games Analysis:")
print(json.dumps(invalid_result, indent=4, ensure_ascii=False))
