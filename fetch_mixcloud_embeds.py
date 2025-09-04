import os
import requests
import time
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from dotenv import load_dotenv
from thefuzz import fuzz

load_dotenv()

BASE_URL = "https://api.mixcloud.com/margateradio/cloudcasts/"
OUTPUT_FILE = "mixcloud_embeds.txt"
from datetime import datetime

# Create an archive folder path
EXPORT_FOLDER = "mixcloud_embeds"
os.makedirs(EXPORT_FOLDER, exist_ok=True)

# Dynamic filename with today's date
today_str = datetime.now().strftime("%Y-%m-%d")
GROUPED_OUTPUT_FILE = os.path.join(EXPORT_FOLDER, f"grouped_{today_str}.txt")


# Set 5-month cutoff dynamically
CUTOFF_DATE = datetime.now(timezone.utc) - timedelta(days=150)
FUZZY_MATCH_THRESHOLD = 85

# Manual group overrides for known aliases / similarities
MANUAL_GROUP_OVERRIDES = {
    "Margate Voices": "Margate Voices",
    "Bernadette Hawkes": "Bernadette Hawkes - The Happening",
    "Yasmine Presents Nava Roots": "Yasmine - Nava Roots",
    "Yasmine - Nava Roots": "Yasmine - Nava Roots",
    "Kit Big Woes": "Kit Griffith",
    "Kit Griffiths": "Kit Griffith",
    "Clementine Blue": "Clementine Blue",
    "TYTHE": "TYTHE",
    "Rob SMCS": "Rob Stereo MCs",
}

def fetch_all_shows():
    shows = []
    next_url = BASE_URL

    while next_url:
        print(f"🔄 Fetching: {next_url}")
        res = requests.get(next_url)
        data = res.json()
        shows.extend(data.get("data", []))
        next_url = data.get("paging", {}).get("next")
        time.sleep(0.25)

    return shows

from urllib.parse import quote

def generate_embed_code(slug):
    encoded_slug = quote(f"/{slug}/")
    return f'<iframe width="100%" height="60" src="https://player-widget.mixcloud.com/widget/iframe/?hide_cover=1&mini=1&feed={encoded_slug}" frameborder="0" allow="encrypted-media; fullscreen; autoplay; idle-detection; speaker-selection; web-share;"></iframe>'


def clean_title_for_grouping(title):
    # Strip date-like suffixes: " - 08.25" or " - 07.24"
    import re
    title = re.sub(r"\s*-\s*\d{2}\.\d{2}$", "", title).strip()

    # Manual override for fuzzy aliases
    for match, override in MANUAL_GROUP_OVERRIDES.items():
        if match.lower() in title.lower():
            return override
    return title

def group_titles_fuzzily(shows):
    grouped = []
    for show in shows:
        cleaned_title = clean_title_for_grouping(show["name"])
        found_group = False
        for group in grouped:
            existing_title = clean_title_for_grouping(group[0]["name"])
            if fuzz.partial_ratio(existing_title, cleaned_title) >= FUZZY_MATCH_THRESHOLD:
                group.append(show)
                found_group = True
                break
        if not found_group:
            grouped.append([show])
    return grouped


import re

# Map of known group name overrides
MANUAL_TITLE_OVERRIDES = {
    "Margate Voices": "Margate Voices",
    "Margate Voices Episode": "Margate Voices",
    "Ghost Papa": "Kier - Ghost Papa",
    "Bernadette Hawkes - The Happening": "Bernadette Hawkes - The Happening",
    "Dulcie May Moreno": "Bernadette Hawkes - The Happening",
    "Yasmine Presents Nava Roots": "Yasmine - Nava Roots",
    "Yasmine - Nava Roots": "Yasmine - Nava Roots",
    "Kit Griffiths": "Kit Griffith",
    "Kit Big Woes": "Kit Griffith",
    "Clementine Blue": "Clementine Blue",
    "TYTHE": "TYTHE",
    "Rob SMCS": "Rob Stereo MCs"
}

def clean_group_title(title):
    # Remove date suffix like ' - 08.25' or ' - 08/25'
    title = re.sub(r"[-–]\s?\d{2}[./]\d{2}$", "", title.strip())

    # Check manual overrides
    for key, value in MANUAL_TITLE_OVERRIDES.items():
        if key.lower() in title.lower():
            return value

    return title


def run():
    print("🚀 Fetching Mixcloud shows...")
    shows = fetch_all_shows()

    # Filter and sort shows
    filtered_shows = [s for s in shows if datetime.fromisoformat(s["created_time"].replace("Z", "+00:00")) > CUTOFF_DATE]
    sorted_shows = sorted(filtered_shows, key=lambda x: x["created_time"], reverse=True)

    # Fuzzy group
    grouped_shows = group_titles_fuzzily(sorted_shows)

    # Alphabetical sort by first show title in group
    grouped_shows = sorted(grouped_shows, key=lambda group: group[0]["name"].lower())

    # Create export folder
    EXPORT_FOLDER = "mixcloud_embeds"
    os.makedirs(EXPORT_FOLDER, exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    GROUPED_OUTPUT_FILE = os.path.join(EXPORT_FOLDER, f"grouped_{today_str}.txt")

    # Write to timestamped grouped output
    with open(GROUPED_OUTPUT_FILE, "w") as f:
        for group in grouped_shows:
            display_title = clean_group_title(group[0]["name"])
            f.write(f"# {display_title}\n")
            for show in group:
                full_title = show["name"]
                slug = show["key"].strip("/")
                embed = generate_embed_code(slug)
                f.write(f'<hr style="border: none; height: 1px; background-color: #676767;margin: 2em auto;">\n')
                f.write(f"{full_title}\n{embed}\n\n")
            f.write("\n")
    print(f"✅ Grouped titles written to {GROUPED_OUTPUT_FILE}")

if __name__ == "__main__":
    run()