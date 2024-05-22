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


def check_for_duplicates_and_completeness(data):
    """Check for duplicate IDs and completeness of game data."""
    seen_ids = set()
    duplicates = set()
    incomplete_entries = []

    # Define essential fields that must be filled in each game entry
    essential_fields = ["ID", "Name", "ImageURL", "Price", "Developer", "Publisher", "PositiveReviews",
                        "NegativeReviews", "DayPeak", "TopTags", "LanguagesSub", "LanguagesAudio", "ShortDesc",
                        "ReleaseDate", "Platforms"]

    for entry in data:
        # Check for duplicates
        if entry["ID"] in seen_ids:
            duplicates.add(entry["ID"])
        else:
            seen_ids.add(entry["ID"])

        # Check for completeness
        if not all(field in entry and entry[field] for field in essential_fields):
            incomplete_entries.append(entry["ID"])

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
    """Main function to load data, check it, and report findings."""
    data = load_json_data(file_path)
    if data is None:
        return

    duplicates, incomplete_entries = check_for_duplicates_and_completeness(data)
    report_findings(duplicates, incomplete_entries)


# Usage
file_path = 'detailed_games.json'
main(file_path)
