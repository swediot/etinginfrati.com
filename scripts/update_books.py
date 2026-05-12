import os
import re
import sys
import yaml
import subprocess
from pathlib import Path

USERNAME = "swediot"
BASE_URL = "https://app.thestorygraph.com"
FETCH_BASE_URL = os.getenv("STORYGRAPH_FETCH_BASE_URL", "https://r.jina.ai/http://https://app.thestorygraph.com")
OUTPUT_FILE = "_data/books.yml"
DEBUG_DIR = Path("tmp/storygraph-debug")

SECTION_URLS = {
    "profile": f"/profile/{USERNAME}",
    "currently_reading": f"/currently-reading/{USERNAME}",
    "recently_read": f"/books-read/{USERNAME}",
    "recent_five_star": f"/five_star_reads/{USERNAME}",
    "to_read": f"/to-read/{USERNAME}",
}

IMAGE_LINK_RE = re.compile(
    r"\[!\[(?:Image \d+: )?(?P<alt>.+?)\]\((?P<image>https://[^)]+)\)\]\((?P<url>https://app\.thestorygraph\.com/books/[^)]+)\)"
)
COUNT_RE = re.compile(r"\[(?P<label>[^\]]+) \((?P<count>\d+)\)\]\(https://app\.thestorygraph\.com/(?P<path>[^)]+)\)")
YEAR_RE = re.compile(r"\b(?P<count>\d+)\s+This Year\b", re.IGNORECASE)


def ensure_debug_dir():
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def fetch_markdown(section_name, path):
    primary_url = f"{FETCH_BASE_URL}{path}"
    fallback_url = f"{BASE_URL}{path}"

    commands = [
        (primary_url, ["curl", "-fsSL", "-A", "Mozilla/5.0", primary_url]),
        (
            fallback_url,
            [
                "curl",
                "-fsSL",
                "-A",
                "Mozilla/5.0",
                "--http1.1",
                "--compressed",
                "-H",
                "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "-H",
                "Accept-Language: en-GB,en-US;q=0.9,en;q=0.8",
                "-H",
                "Cache-Control: no-cache",
                "-H",
                "Pragma: no-cache",
                fallback_url,
            ],
        ),
    ]

    last_error = None
    challenge_text = None

    for url, command in commands:
        print(f"Fetching {url}...")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            last_error = f"curl failed for {section_name} via {url}: {stderr or 'unknown error'}"
            continue

        text = result.stdout
        lowered = text.lower()
        if "title: just a moment..." in lowered or "cf-mitigated" in lowered or "enable javascript and cookies to continue" in lowered:
            challenge_text = text
            last_error = f"StoryGraph fetch for {section_name} via {url} hit Cloudflare"
            continue

        if "https://app.thestorygraph.com/books/" not in text and section_name != "profile":
            last_error = f"Fetch for {section_name} via {url} returned unexpected content"
            continue

        return text

    ensure_debug_dir()
    debug_path = DEBUG_DIR / f"{section_name}.txt"
    debug_path.write_text(challenge_text or (last_error or "Unknown fetch failure"), encoding="utf-8")
    raise RuntimeError(f"{last_error}. Saved debug response to {debug_path}")


def parse_counts(profile_markdown):
    counts = {
        "year_count": "0",
        "to_read_count": "0",
    }

    year_match = YEAR_RE.search(profile_markdown)
    if year_match:
        counts["year_count"] = year_match.group("count")

    for match in COUNT_RE.finditer(profile_markdown):
        path = match.group("path")
        if path == f"to-read/{USERNAME}":
            counts["to_read_count"] = match.group("count")

    return counts


def normalise_alt(alt_text):
    if " by " in alt_text:
        title, author = alt_text.rsplit(" by ", 1)
    elif " — " in alt_text:
        title, author = alt_text.rsplit(" — ", 1)
    else:
        title, author = alt_text, ""
    return title.strip(), author.strip()


def parse_books(markdown_text, limit=None):
    books = []
    seen = set()

    for match in IMAGE_LINK_RE.finditer(markdown_text):
        url = match.group("url")
        if url in seen:
            continue
        seen.add(url)

        title, author = normalise_alt(match.group("alt"))
        books.append(
            {
                "title": title,
                "author": author,
                "url": url,
                "image": match.group("image"),
            }
        )

    if limit is not None:
        books = books[:limit]
    return books


def validate_data(data):
    errors = []

    if data.get("to_read_count", "0") == "0":
        errors.append("To Read count is 0 or missing")
    if data.get("year_count", "0") == "0":
        errors.append("Year count is 0 or missing")
    if not data.get("recently_read"):
        errors.append("Recently read list is empty")
    if not data.get("recent_five_star"):
        errors.append("Recent 5 Star list is empty")
    if not data.get("currently_reading"):
        errors.append("Currently reading list is empty")

    if errors:
        raise RuntimeError("Validation failed: " + "; ".join(errors))


def main():
    try:
        profile = fetch_markdown("profile", SECTION_URLS["profile"])
        currently_reading = fetch_markdown("currently_reading", SECTION_URLS["currently_reading"])
        recently_read = fetch_markdown("recently_read", SECTION_URLS["recently_read"])
        recent_five_star = fetch_markdown("recent_five_star", SECTION_URLS["recent_five_star"])
    except Exception as error:
        print(f"Error fetching StoryGraph data: {error}")
        sys.exit(1)

    data = parse_counts(profile)
    data["currently_reading"] = parse_books(currently_reading)
    data["recently_read"] = parse_books(recently_read, limit=5)
    data["recent_five_star"] = parse_books(recent_five_star, limit=5)

    try:
        validate_data(data)
    except Exception as error:
        print(str(error))
        sys.exit(1)

    print(f"Saving to {OUTPUT_FILE}...")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as handle:
        yaml.dump(data, handle, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print("Done!")


if __name__ == "__main__":
    main()
