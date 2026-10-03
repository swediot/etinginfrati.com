import os
import re
import sys
import yaml
from pathlib import Path
from bs4 import BeautifulSoup
from curl_cffi import requests

USERNAME = os.getenv("STORYGRAPH_USERNAME", "swediot")
BASE_URL = "https://app.thestorygraph.com"
OUTPUT_FILE = os.getenv("STORYGRAPH_OUTPUT_FILE", "_data/books.yml")
DEBUG_DIR = Path("tmp/storygraph-debug")
PROFILE_PATH = f"/profile/{USERNAME}"
PROFILE_URL = f"{BASE_URL}{PROFILE_PATH}"

SECTION_PATHS = {
    "currently_reading": f"/currently-reading/{USERNAME}",
    "recently_read": f"/books-read/{USERNAME}",
    "recent_five_star": f"/five_star_reads/{USERNAME}",
}

SECTION_LIMITS = {
    "currently_reading": None,
    "recently_read": 5,
    "recent_five_star": 5,
}


def ensure_debug_dir():
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def fetch_profile_html():
    """Fetch the StoryGraph profile page directly using TLS fingerprint impersonation.

    Cloudflare blocks generic HTTP clients (curl, requests, urllib) with Turnstile / cf-mitigated challenges.
    curl_cffi impersonates modern browser TLS/HTTP2 fingerprints, bypassing Cloudflare's bot challenges directly.
    """
    impersonate_targets = ["chrome124", "chrome", "chrome120"]
    last_error = None
    challenge_text = None

    for target in impersonate_targets:
        print(f"Fetching {PROFILE_URL} (impersonating {target})...")
        try:
            response = requests.get(
                PROFILE_URL,
                impersonate=target,
                timeout=30,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },
            )
            text = response.text
            lowered = text.lower()

            if response.status_code != 200:
                last_error = f"HTTP {response.status_code} via {target}"
                continue

            if "title: just a moment..." in lowered or "cf-mitigated" in lowered or "enable javascript and cookies to continue" in lowered:
                challenge_text = text
                last_error = f"Fetch via {target} hit Cloudflare challenge"
                continue

            if f"/profile/{USERNAME}" not in text and f"@{USERNAME}" not in text:
                last_error = f"Fetch via {target} returned unexpected content"
                continue

            return text
        except Exception as e:
            last_error = f"Request error via {target}: {e}"
            continue

    ensure_debug_dir()
    debug_path = DEBUG_DIR / "profile.html"
    debug_path.write_text(challenge_text or (last_error or "Unknown fetch failure"), encoding="utf-8")
    raise RuntimeError(f"{last_error}. Saved debug response to {debug_path}")


def parse_counts(soup):
    counts = {"year_count": "0", "to_read_count": "0"}

    # Year count (e.g. '143 This Year')
    for a in soup.find_all("a"):
        text = a.get_text(" ", strip=True)
        m = re.search(r"(\d+)\s+This Year", text, re.IGNORECASE)
        if m:
            counts["year_count"] = m.group(1)
            break

    # To-read count (e.g. 'To-Read Pile (1409)')
    for a in soup.find_all("a"):
        href = a.get("href") or ""
        text = a.get_text(" ", strip=True)
        if f"/to-read/{USERNAME}" in href:
            m = re.search(r"\((\d+)\)", text)
            if m:
                counts["to_read_count"] = m.group(1)
                break

    return counts


def normalise_alt(alt_text):
    if " by " in alt_text:
        title, author = alt_text.rsplit(" by ", 1)
    elif " — " in alt_text:
        title, author = alt_text.rsplit(" — ", 1)
    else:
        title, author = alt_text, ""
    return title.strip(), author.strip()


def parse_sections(soup):
    sections = {}

    for section_key, path_suffix in SECTION_PATHS.items():
        books = []
        seen = set()
        section_links = soup.find_all("a", href=re.compile(re.escape(path_suffix)))
        for sl in section_links:
            parent = sl.find_parent(["div", "section"])
            book_links = parent.find_all("a", href=re.compile(r"/books/[a-f0-9-]+")) if parent else []
            if book_links:
                for bl in book_links:
                    href = bl.get("href", "")
                    if not href.startswith("http"):
                        href = f"{BASE_URL}{href}"
                    if href in seen:
                        continue
                    seen.add(href)
                    img = bl.find("img")
                    if img:
                        alt = img.get("alt", "")
                        title, author = normalise_alt(alt)
                        src = img.get("src", "")
                        books.append(
                            {
                                "title": title,
                                "author": author,
                                "url": href,
                                "image": src,
                            }
                        )
                break

        limit = SECTION_LIMITS[section_key]
        if limit is not None:
            books = books[:limit]
        sections[section_key] = books

    return sections


def validate_data(data):
    errors = []
    if data.get("to_read_count", "0") == "0":
        errors.append("To Read count is 0 or missing")
    if data.get("year_count", "0") == "0":
        errors.append("Year count is 0 or missing")
    if not data.get("currently_reading"):
        errors.append("Currently reading list is empty")
    if not data.get("recently_read"):
        errors.append("Recently read list is empty")
    if not data.get("recent_five_star"):
        errors.append("Recent 5 Star list is empty")
    if errors:
        raise RuntimeError("Validation failed: " + "; ".join(errors))


def main():
    try:
        html = fetch_profile_html()
    except Exception as error:
        print(f"Error fetching StoryGraph data: {error}")
        sys.exit(1)

    soup = BeautifulSoup(html, "html.parser")
    data = parse_counts(soup)
    sections = parse_sections(soup)
    data.update(sections)

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
