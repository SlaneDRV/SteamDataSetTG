import json

def load_json_data(file_path):
    """Load JSON data from a file and handle potential exceptions."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
    except json.JSONDecodeError:
        print(f"Error: File is not a valid JSON - {file_path}")
    return None

def check_for_duplicates_and_completeness(data):
    """Check for duplicate IDs and completeness of game data, return any issues found."""
    seen_ids = set()
    duplicates = set()
    incomplete_entries = []

    essential_fields = [
        "ID", "Name", "ImageURL", "Price", "Developer", "Publisher", "PositiveReviews",
        "NegativeReviews", "DayPeak", "TopTags", "LanguagesSub", "LanguagesAudio",
        "ShortDesc", "ReleaseDate", "Platforms"
    ]

    for entry in data:
        game_id = entry.get("ID")
        if game_id in seen_ids:
            duplicates.add(game_id)
        seen_ids.add(game_id)

        if any(entry.get(field) is None for field in essential_fields):
            incomplete_entries.append(game_id)

    return duplicates, incomplete_entries

def report_findings(duplicates, incomplete_entries):
    """Print the findings of the data check."""
    if duplicates:
        print(f"Duplicate IDs found: {duplicates}")
    else:
        print("No duplicate IDs found.")

    if incomplete_entries:
        print(f"Incomplete entries found for IDs: {incomplete_entries}")
    else:
        print("All entries are complete.")

def main(file_path):
    """Load data, check it, and report findings."""
    data = load_json_data(file_path)
    if data is None:
        print("No data to process.")
        return

    duplicates, incomplete_entries = check_for_duplicates_and_completeness(data)
    report_findings(duplicates, incomplete_entries)

# Usage
file_path = 'detailed_games_new.json'
main(file_path)
