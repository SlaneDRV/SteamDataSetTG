import json


def transform_json(input_file_path, output_file_path):
    """Read JSON data from input file, transform it, and write to output file."""
    try:
        with open(input_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)  # Load data from the original JSON file

        transformed_data = {}
        for item in data:  # Assume 'data' is a list of dictionaries
            item_id = item['ID']  # Extract the ID to use as a key in the new dictionary
            transformed_data[item_id] = item  # Map the entire record to its ID

        with open(output_file_path, 'w', encoding='utf-8') as file:
            json.dump(transformed_data, file, indent=4,
                      ensure_ascii=False)  # Write the transformed data to a new JSON file
        print(f"Data successfully transformed and saved to {output_file_path}")

    except FileNotFoundError:
        print(f"Error: File not found - {input_file_path}")
    except json.JSONDecodeError:
        print("Error: File is not a valid JSON - unable to read.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


# Usage example
input_file_path = 'detailed_games_actual.json'
output_file_path = 'detailed_games_transformed.json'
transform_json(input_file_path, output_file_path)
