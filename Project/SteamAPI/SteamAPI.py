import html
import time
from pathlib import Path

import requests
import json
from tqdm import tqdm
import re

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
    # Validate that the 'developers' and 'publishers' lists are not only non-empty but also do not contain empty or 'Unknown' entries
    developers = details.get('developers', [])
    publishers = details.get('publishers', [])

    # Check that developers and publishers exist, are not empty, and are not just "Unknown"
    has_developers = any(dev for dev in developers if dev and dev != "Unknown")
    has_publishers = any(pub for pub in publishers if pub and pub != "Unknown")

    # Debug print to understand what's going on
    print(f"Developers: {developers}, Publishers: {publishers}, Valid: {has_developers and has_publishers}")

    return has_developers and has_publishers


def create_session_with_retries():
    session = requests.Session()
    retry = Retry(
        total=10,  # Total number of retries
        backoff_factor=1,  # Exponential backoff factor
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

    valid_ids = load_ids_from_file("FileCheckNEdit/detailed_games_actual.json")
    invalid_ids = load_ids_from_file("FileCheckNEdit/invalid_games_actual.json")
    combined_ids = valid_ids.union(invalid_ids)
    print(f"Loaded {len(combined_ids)} existing game IDs from files.")
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
    print(f"Total games fetched from Steam: {len(games)}")
    return games

def fetch_game_details_from_steam(appid, api_key, country='US'):
    url = f"http://store.steampowered.com/api/appdetails?appids={appid}&cc={country}&key={api_key}"
    session = create_session_with_retries()
    while True:
        try:
            response = session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as err:
            if response.status_code == 429:
                print(f"Rate limit exceeded for appid {appid}. Retrying...")
                time.sleep(5)
                continue
            else:
                raise err

def get_top_tags_for_game(appid, top_n=5):
    data = get_game_data_from_steamspy(appid)
    tags = data.get('tags', {})
    if isinstance(tags, dict):
        sorted_tags = sorted(tags.items(), key=lambda item: item[1], reverse=True)
        top_tags = sorted_tags[:top_n]
        return [tag for tag, count in top_tags]
    return ["No tags found"]


def save_games_details(game_info, file_path):
    json_file_path = file_path
    if file_path == "invalid_games.json":
        # If saving to the invalid games file, only save the ID and Name
        game_info = {
            "ID": game_info["ID"],
            "Name": game_info["Name"]
        }
    if Path(json_file_path).exists():
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    else:
        data = []

    # Decode HTML entities and save data
    for key, value in game_info.items():
        if isinstance(value, str):
            game_info[key] = html.unescape(value)

    data.append(game_info)
    with open(json_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)



def load_progress():
    try:
        with open("progress.json", "r") as file:
            progress = json.load(file)
            return progress['last_index']
    except FileNotFoundError:
        return 0

def save_progress(last_index):
    with open("progress.json", "w") as file:
        json.dump({"last_index": last_index}, file)

def main(api_key):
    existing_ids = load_existing_game_ids()
    all_games = get_all_games()
    steam_game_ids = set(int(game['appid']) for game in all_games)
    games = steam_game_ids - existing_ids
    print(f"Number of new games to process: {len(games)}")
    for appid in tqdm(games, desc="Processing new games"):
        print(f"Processing game ID: {appid}")
        try:
            steam_data = fetch_game_details_from_steam(appid, api_key)
            if not steam_data or not steam_data.get(str(appid), {}).get('success'):
                print(f"No valid data for {appid}, skipping...")
                save_invalid_game(appid)  # Save this ID as invalid
                continue
            if steam_data and str(appid) in steam_data and steam_data[str(appid)].get('success'):
                steam_details = steam_data[str(appid)]['data']
                steamspy_data = get_game_data_from_steamspy(appid)
                top_tags = get_top_tags_for_game(appid)
                price = "Not available in this region"
                if steam_details.get('is_free', False):
                    price = "Free"
                elif 'price_overview' in steam_details:
                    price = steam_details['price_overview'].get('final_formatted', 'Price not available')
                elif 'release_date' in steam_details and steam_details['release_date'].get('coming_soon'):
                    price = "Coming Soon"
                elif 'packages' in steam_details:
                    for package in steam_details['packages']:
                        if 'price' in package:
                            price = package['price']
                            break
                game_info = {
                    "ID": appid,
                    "Name": steam_details.get('name', 'Unknown'),
                    "ImageURL": steam_details.get('header_image', 'No image available'),
                    "Price": price,
                    "Developer": steam_details.get('developers', ['Unknown'])[0],
                    "Publisher": steam_details.get('publishers', ['Unknown'])[0],
                    "PositiveReviews": steamspy_data["positive"],
                    "NegativeReviews": steamspy_data["negative"],
                    "DayPeak": steamspy_data["ccu"],
                    "TopTags": top_tags,
                    "LanguagesSub": parse_supported_languages(steam_details.get('supported_languages', 'Not available'))["Subtitles"],
                    "LanguagesAudio": parse_supported_languages(steam_details.get('supported_languages', 'Not available'))["Full Audio"],
                    "ShortDesc": steam_details.get('short_description', 'No description available'),
                    "ReleaseDate": steam_details.get('release_date', {}).get('date', 'Unknown'),
                    "Platforms": ', '.join(platform for platform, available in steam_details.get('platforms', {}).items() if available),
                }
                for key, value in game_info.items():
                    print(f"{key}: {value}")
                print(f"Checking game {appid}: Developer - {steam_details.get('developers')}, Publisher - {steam_details.get('publishers')}")
                if is_data_complete(steam_details):
                    save_games_details(game_info, "detailed_steam_games.json")
                else:
                    save_games_details(game_info, "invalid_games.json")
        except Exception as e:
            print(f"Failed to process game ID {appid}: {e}")
            time.sleep(5)
            continue

if __name__ == "__main__":
    api_key = 'D350BB8AC6A45C05FA8B4EF538CEAE64'  # Replace with your actual Steam API key
    main(api_key)