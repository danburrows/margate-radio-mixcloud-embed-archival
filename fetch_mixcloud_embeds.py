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
GROUPED_OUTPUT_FILE = "grouped_mixcloud_titles.txt"

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

def generate_embed_code(slug):
    return f'<iframe width="100%" height="120" src="https://www.mixcloud.com/widget/iframe/?hide_cover=1&light=1&feed=/{slug}/" frameborder="0"></iframe>'

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

def run():
    print("🚀 Fetching Mixcloud shows...")
    shows = fetch_all_shows()

    # Filter by last 5 months
    filtered_shows = [s for s in shows if datetime.fromisoformat(s["created_time"].replace("Z", "+00:00")) > CUTOFF_DATE]
    sorted_shows = sorted(filtered_shows, key=lambda x: x["created_time"], reverse=True)

    # Write flat embed list
    with open(OUTPUT_FILE, "w") as f:
        for show in sorted_shows:
            title = show["name"]
            slug = show["key"].strip("/")
            embed = generate_embed_code(slug)
            f.write(f"{title}\n{embed}\n\n")
    print(f"✅ Wrote {len(sorted_shows)} embeds to {OUTPUT_FILE}")

    # Fuzzy group & write grouped embed list
    grouped_shows = group_titles_fuzzily(sorted_shows)
    with open(GROUPED_OUTPUT_FILE, "w") as f:
        for group in grouped_shows:
            group_title = clean_title_for_grouping(group[0]['name'])
            f.write(f"# {group_title}\n")
            for show in group:
                slug = show["key"].strip("/")
                embed = generate_embed_code(slug)
                f.write(f"{embed}\n\n")
            f.write("\n")
    print(f"✅ Grouped titles written to {GROUPED_OUTPUT_FILE}")

if __name__ == "__main__":
    run()
