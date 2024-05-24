import json

def load_json_data(file_path):
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

def remove_duplicates(data):
    """Remove duplicates from data based on the 'ID' key."""
    unique_data = {}
    for item in data:
        item_id = item.get("ID")
        if item_id not in unique_data:
            unique_data[item_id] = item
    return list(unique_data.values())

def save_json_data(data, file_path):
    """Save the cleaned data to a JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        print(f"Data successfully saved to {file_path}")
    except IOError:
        print(f"Error: Could not write to file - {file_path}")

def main(input_file_path, output_file_path):
    """Main function to process the JSON file and remove duplicates."""
    data = load_json_data(input_file_path)
    if data is None:
        return

    cleaned_data = remove_duplicates(data)
    save_json_data(cleaned_data, output_file_path)

# Usage
input_file_path = 'detailed_games_actual.json'
output_file_path = 'detailed_games_actual.json'
main(input_file_path, output_file_path)

input_file_path = 'invalid_games_actual.json'
output_file_path = 'invalid_games_actual.json'
main(input_file_path, output_file_path)
