import json


def load_json_file(file_path):
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: File is not a valid JSON - {file_path}")
        return None


def save_json_file(data, file_path):
    """Save data to a JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        print(f"Data successfully saved to {file_path}")
    except IOError:
        print(f"Error: Could not write to file - {file_path}")


def merge_json_files(file_path1, file_path2, output_file_path):
    """FileCheckNEdit two JSON files and save the combined data."""
    data1 = load_json_file(file_path1)
    data2 = load_json_file(file_path2)

    if data1 is None or data2 is None:
        print("Merging failed due to file loading issues.")
        return

    # Assuming both files contain lists of items
    combined_data = data1 + data2

    # Save the combined data to a new file
    save_json_file(combined_data, output_file_path)


# Usage
file_path1 = 'detailed_games_actual.json'
file_path2 = '../detailed_steam_games.json'
output_file_path = 'detailed_games_new.json'
merge_json_files(file_path1, file_path2, output_file_path)



