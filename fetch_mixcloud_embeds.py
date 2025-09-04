import os
import re
import time
import requests
from datetime import datetime, timezone, timedelta
from urllib.parse import quote
from dotenv import load_dotenv
from thefuzz import fuzz

# Load environment variables if needed
load_dotenv()

# === Configuration ===
BASE_URL = "https://api.mixcloud.com/margateradio/cloudcasts/"
EXPORT_FOLDER = "mixcloud_embeds"
FUZZY_MATCH_THRESHOLD = 85
CUTOFF_DATE = datetime.now(timezone.utc) - timedelta(days=150)

# Create export folder if it doesn't exist
os.makedirs(EXPORT_FOLDER, exist_ok=True)
today_str = datetime.now().strftime("%Y-%m-%d")
OUTPUT_FILE = os.path.join(EXPORT_FOLDER, f"grouped_{today_str}.txt")

# Manual overrides for title cleaning and grouping
TITLE_OVERRIDES = {
    "Margate Voices": "Margate Voices",
    "Margate Voices Episode": "Margate Voices",
    "Ghost Papa": "Kier - Ghost Papa",
    "Bernadette Hawkes": "Bernadette Hawkes - The Happening",
    "The Happening": "Bernadette Hawkes - The Happening",
    "Dulcie May Moreno": "Bernadette Hawkes - The Happening",
    "Yasmine Presents Nava Roots": "Yasmine - Nava Roots",
    "Yasmine - Nava Roots": "Yasmine - Nava Roots",
    "Kit Griffiths": "Kit Griffith",
    "Kit Big Woes": "Kit Griffith",
    "Clementine Blue": "Clementine Blue",
    "TYTHE": "TYTHE",
    "Rob SMCS": "Rob Stereo MCs",
}

# === Mixcloud API ===
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

# === Embed Code Generation ===
def generate_embed_code(slug):
    encoded_slug = quote(f"/{slug}/")
    return (
        f'<iframe width="100%" height="60" src="https://player-widget.mixcloud.com/widget/iframe/?hide_cover=1&mini=1&feed={encoded_slug}" '
        f'frameborder="0" allow="encrypted-media; fullscreen; autoplay; idle-detection; speaker-selection; web-share;"></iframe>'
    )

# === Title Cleaning and Grouping ===
def clean_group_title(title):
    title = re.sub(r"[-–]\s?\d{2}[./]\d{2}$", "", title.strip())
    for key, val in TITLE_OVERRIDES.items():
        if key.lower() in title.lower():
            return val
    return title

def group_titles_fuzzily(shows):
    grouped = []
    for show in shows:
        cleaned_title = clean_group_title(show["name"])
        found_group = False
        for group in grouped:
            existing_cleaned = clean_group_title(group[0]["name"])
            if fuzz.partial_ratio(existing_cleaned, cleaned_title) >= FUZZY_MATCH_THRESHOLD:
                group.append(show)
                found_group = True
                break
        if not found_group:
            grouped.append([show])
    return grouped

# === Main ===
def run():
    print("🚀 Fetching Mixcloud shows...")
    shows = fetch_all_shows()

    filtered = [s for s in shows if datetime.fromisoformat(s["created_time"].replace("Z", "+00:00")) > CUTOFF_DATE]
    sorted_shows = sorted(filtered, key=lambda s: s["created_time"], reverse=True)

    grouped_shows = group_titles_fuzzily(sorted_shows)
    grouped_shows.sort(key=lambda g: clean_group_title(g[0]["name"]).lower())

    with open(OUTPUT_FILE, "w") as f:
        for group in grouped_shows:
            display_title = clean_group_title(group[0]["name"])
            f.write(f"# {display_title}\n")
            for show in group:
                full_title = show["name"]
                slug = show["key"].strip("/")
                embed = generate_embed_code(slug)
                f.write('<hr style="border: none; height: 1px; background-color: #676767;margin: 2em auto;">\n')
                f.write(f"{full_title}\n{embed}\n\n")
            f.write("\n")
    print(f"✅ Grouped titles written to {OUTPUT_FILE}")

if __name__ == "__main__":
    run()
