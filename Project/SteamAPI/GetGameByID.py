import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import json

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

def get_game_details_from_steam(appid, api_key, country='UA'):
    url = f"http://store.steampowered.com/api/appdetails?appids={appid}&cc={country}&key={api_key}"
    session = create_session_with_retries()
    while True:
        try:
            response = session.get(url)
            response.raise_for_status()
            data = response.json()
            if str(appid) in data and data[str(appid)].get('success'):
                return data[str(appid)]['data']
            else:
                return None
        except requests.exceptions.HTTPError as err:
            if response.status_code == 429:
                print(f"Rate limit exceeded for appid {appid}. Retrying...")
                time.sleep(5)
                continue
            else:
                raise err
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch data for appid {appid}: {e}")
            return None

def save_to_json(data, filename='game_info.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_game_data_from_steamspy(appid):
    url = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
    response = requests.get(url)
    data = response.json()
    return data
def get_game_info(appid, api_key):
    steam_details = get_game_details_from_steam(appid, api_key)
    steamspy_data = get_game_data_from_steamspy(appid)
    if not steam_details:
        return "Game details could not be retrieved."

    price = "Not available in this region"
    if steam_details.get('is_free', False):
        price = "Free"
    elif 'price_overview' in steam_details:
        price = steam_details['price_overview'].get('final_formatted', 'Price not available')
    elif 'release_date' in steam_details and steam_details['release_date'].get('coming_soon'):
        price = "Coming Soon"

    result = {
        "Developer": steam_details.get('developers', ['Unknown'])[0],
        "Publisher": steam_details.get('publishers', ['Unknown'])[0],
        "Price": price,
        "ID": appid,
        "Name": steam_details.get('name', 'Unknown'),
        "ImageURL": steam_details.get('header_image', 'No image available'),
        "ShortDesc": steam_details.get('short_description', 'No description available'),
        "ReleaseDate": steam_details.get('release_date', {}).get('date', 'Unknown'),
        "Platforms": ', '.join(
            platform for platform, available in steam_details.get('platforms', {}).items() if available),
        "PositiveReviews": steamspy_data["positive"],
        "NegativeReviews": steamspy_data["negative"],
    }

    return result

if __name__ == "__main__":
    api_key = 'D350BB8AC6A45C05FA8B4EF538CEAE64'  # Replace with your actual Steam API key
    appid = 553850  # Replace with the actual appid of the game
    result = get_game_info(appid, api_key)
    print(json.dumps(result, indent=4))  # This prints the JSON to the console
    save_to_json(result)  # This saves the JSON to a file
