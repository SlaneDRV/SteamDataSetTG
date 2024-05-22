import json

def convert_json_format(input_file_path, output_file_path):
    # Load the original JSON data
    with open(input_file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Initialize a list to hold the converted data
    converted_data = []

    # Iterate through the original data, converting each entry
    for key, value in data.items():
        converted_data.append(value)

    # Save the converted data to a new JSON file
    with open(output_file_path, 'w', encoding='utf-8') as file:
        json.dump(converted_data, file, indent=4, ensure_ascii=False)
        print(f"Data successfully converted and saved to {output_file_path}")

# Example usage
input_file_path = 'detailed_steam_games1.json'
output_file_path = 'detailed_steam_games1.json'
convert_json_format(input_file_path, output_file_path)
