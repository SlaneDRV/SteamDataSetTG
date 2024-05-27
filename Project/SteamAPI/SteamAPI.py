import html
import os
import time
from pathlib import Path
from TgBot import config

import requests
import json
from tqdm import tqdm
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def save_invalid_game(appid):
    json_file_path = "invalid_games.json"
    game_info = {
        "ID": appid,
        "Name": "Invalid Game"  # Placeholder name indicating lack of valid data
    }
    if Path(json_file_path).exists():
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    else:
        data = []
    data.append(game_info)
    with open(json_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def is_data_complete(details):
    developers = details.get('developers', [])
    publishers = details.get('publishers', [])
    has_developers = any(dev for dev in developers if dev and dev != "Unknown")
    has_publishers = any(pub for pub in publishers if pub and pub != "Unknown")
    return has_developers and has_publishers

def create_session_with_retries():
    session = requests.Session()
    retry = Retry(
        total=10,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def load_existing_game_ids():
    def load_ids_from_file(json_file_path):
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return {game["ID"] for game in data}
        except (FileNotFoundError, json.JSONDecodeError):
            return set()

    valid_ids = load_ids_from_file("JSON/detailed_games_actual.json")
    invalid_ids = load_ids_from_file("JSON/invalid_games_actual.json")
    combined_ids = valid_ids.union(invalid_ids)
    return combined_ids

def parse_supported_languages(languages_html):
    languages_html = re.sub(r'<br><strong>\*</strong>languages with full audio support', '', languages_html)
    languages_html = re.sub(r'<[^>]*>', '', languages_html)
    all_languages = languages_html.split(',')
    all_languages = [lang.strip() for lang in all_languages if lang.strip()]
    full_audio = [lang.strip().strip('*') for lang in all_languages if '*' in lang]
    subtitles = [lang.strip().strip('*') for lang in all_languages]
    return {
        "Full Audio": full_audio if full_audio else ["Not available"],
        "Subtitles": subtitles if subtitles else ["Not available"]
    }

def get_game_data_from_steamspy(appid):
    url = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
    response = requests.get(url)
    data = response.json()
    return data

def get_all_games():
    response = requests.get("http://api.steampowered.com/ISteamApps/GetAppList/v2")
    games = response.json()['applist']['apps']
    return games

def fetch_game_details_from_steam(appid, session, api_key, country='US'):
    url = f"http://store.steampowered.com/api/appdetails?appids={appid}&cc={country}&key={api_key}"
    while True:
        try:
            response = session.get(url)
            response.raise_for_status()
            if not response.content:
                raise ValueError(f"Empty response for appid {appid}")
            return response.json()
        except requests.exceptions.HTTPError as err:
            if response.status_code == 429:
                time.sleep(5)
                continue
            else:
                raise err
        except ValueError as e:
            print(e)
            return None

def get_top_tags_for_game(appid):
    data = get_game_data_from_steamspy(appid)
    tags = data.get('tags', {})
    if isinstance(tags, dict):
        sorted_tags = sorted(tags.items(), key=lambda item: item[1], reverse=True)
        top_tags = sorted_tags[:5]
        return [tag for tag, count in top_tags]
    return ["No tags found"]

def save_games_details(game_info, file_path):
    json_file_path = file_path
    if file_path == "invalid_games.json":
        game_info = {
            "ID": game_info["ID"],
            "Name": game_info["Name"]
        }
    if Path(json_file_path).exists() and os.path.getsize(json_file_path) > 0:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    else:
        data = []

    for key, value in game_info.items():
        if isinstance(value, str):
            game_info[key] = html.unescape(value)

    data.append(game_info)
    with open(json_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def load_json_file(file_path):
    try:
        if os.path.getsize(file_path) == 0:
            return []
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None

def save_json_file(data, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
    except IOError:
        print(f"Error: Could not write to file - {file_path}")

def merge_json_files(file_path1, file_path2, output_file_path):
    data1 = load_json_file(file_path1)
    data2 = load_json_file(file_path2)

    if data1 is None or data2 is None:
        return

    combined_data = data1 + data2
    save_json_file(combined_data, output_file_path)

    # Удаление файла file_path2 после объединения данных
    try:
        os.remove(file_path2)
        print(f"File {file_path2} has been removed.")
    except OSError as e:
        print(f"Error: {file_path2} : {e.strerror}")

def check_for_duplicates_and_completeness(data, file_name):
    seen_ids = set()
    duplicates = set()
    incomplete_entries = []

    essential_fields = [
        "ID", "Name", "ImageURL", "Price", "Developer", "Publisher", "PositiveReviews",
        "NegativeReviews", "DayPeak", "TopTags", "LanguagesSub", "LanguagesAudio",
        "ShortDesc", "ReleaseDate", "Platforms"
    ]

    if file_name == 'invalid_games_actual.json':
        essential_fields = [
            "ID", "Name"
        ]

    for entry in data:
        game_id = entry.get("ID")
        if game_id in seen_ids:
            duplicates.add(game_id)
        seen_ids.add(game_id)

        if any(entry.get(field) is None for field in essential_fields):
            incomplete_entries.append(game_id)

    return duplicates, incomplete_entries

def remove_duplicates(data):
    unique_data = {}
    for item in data:
        item_id = item.get("ID")
        if item_id not in unique_data:
            unique_data[item_id] = item
    return list(unique_data.values())

def transform_json(input_file_path, output_file_path):
    try:
        with open(input_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        transformed_data = {item['ID']: item for item in data}

        with open(output_file_path, 'w', encoding='utf-8') as file:
            json.dump(transformed_data, file, indent=4, ensure_ascii=False)
    except FileNotFoundError:
        print(f"Error: File not found - {input_file_path}")
    except json.JSONDecodeError:
        print("Error: File is not a valid JSON - unable to read.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def process_game(appid, session, api_key):
    try:
        steam_data = fetch_game_details_from_steam(appid, session, api_key)
        if not steam_data or not steam_data.get(str(appid), {}).get('success'):
            save_invalid_game(appid)
            return None

        steam_details = steam_data[str(appid)]['data']
        steamspy_data = get_game_data_from_steamspy(appid)
        top_tags = get_top_tags_for_game(appid)
        price = "N/A"
        if steam_details.get('is_free', False):
            price = "Free"
        elif 'price_overview' in steam_details:
            price = steam_details['price_overview'].get('final_formatted', 'Price not available')
        elif 'release_date' in steam_details and steam_details['release_date'].get('coming_soon'):
            price = "Coming Soon"
        elif 'packages' in steam_details:
            for package in steam_details['packages']:
                if isinstance(package, dict) and 'price' in package:
                    price = package['price']
                    break
        game_info = {
            "ID": appid,
            "Name": steam_details.get('name', 'Unknown'),
            "ImageURL": steam_details.get('header_image', 'No image available'),
            "Price": price,
            "Developer": steam_details.get('developers', ['Unknown'])[0],
            "Publisher": steam_details.get('publishers', ['Unknown'])[0],
            "PositiveReviews": steamspy_data.get("positive", 0),
            "NegativeReviews": steamspy_data.get("negative", 0),
            "DayPeak": steamspy_data.get("ccu", 0),
            "TopTags": top_tags,
            "LanguagesSub": parse_supported_languages(steam_details.get('supported_languages', 'Not available'))["Subtitles"],
            "LanguagesAudio": parse_supported_languages(steam_details.get('supported_languages', 'Not available'))["Full Audio"],
            "ShortDesc": steam_details.get('short_description', 'No description available'),
            "ReleaseDate": steam_details.get('release_date', {}).get('date', 'Unknown'),
            "Platforms": ', '.join(platform for platform, available in steam_details.get('platforms', {}).items() if available),
        }
        if is_data_complete(steam_details):
            save_games_details(game_info, "detailed_steam_games.json")
        else:
            save_games_details(game_info, "invalid_games.json")
        return appid
    except Exception as e:
        print(f"Failed to process game ID {appid}: {e}")
        return None

def main(api_key):
    existing_ids = load_existing_game_ids()
    all_games = get_all_games()
    steam_game_ids = set(int(game['appid']) for game in all_games)
    games = steam_game_ids - existing_ids
    if games:
        session = create_session_with_retries()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(process_game, appid, session, api_key) for appid in games]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing new games"):
                future.result()

        merge_json_files("JSON/detailed_games_actual.json", "detailed_steam_games.json",
                         "JSON/detailed_games_actual.json")
        merge_json_files("JSON/invalid_games_actual.json", "invalid_games.json", "JSON/invalid_games_actual.json")
        data1 = load_json_file("JSON/detailed_games_actual.json")
        duplicates1, incomplete_entries1 = check_for_duplicates_and_completeness(data1,
                                                                                 "JSON/detailed_games_actual.json")
        data2 = load_json_file("JSON/invalid_games_actual.json")
        duplicates2, incomplete_entries2 = check_for_duplicates_and_completeness(data2,
                                                                                 "JSON/invalid_games_actual.json")
        if duplicates1:
            cleaned_data = remove_duplicates(data1)
            save_json_file(cleaned_data, "JSON/detailed_games_actual.json")
        if duplicates2:
            cleaned_data = remove_duplicates(data2)
            save_json_file(cleaned_data, "JSON/invalid_games_actual.json")
        transform_json("JSON/detailed_games_actual.json", "JSON/detailed_games_transformed.json")
    else:
        print("No new games found")

if __name__ == "__main__":
    api_key = config.SteamKey  # Replace with your actual Steam API key
    main(api_key)
