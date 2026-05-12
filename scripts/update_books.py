from bs4 import BeautifulSoup
import yaml
import os
import sys
import time
from pathlib import Path

# Configuration
USERNAME = "swediot"
BASE_URL = "https://app.thestorygraph.com"
OUTPUT_FILE = "_data/books.yml"
DEBUG_DIR = Path("tmp/storygraph-debug")
CHALLENGE_TITLES = {"Just a moment...", "Attention Required! | Cloudflare"}

def save_debug_artifacts(page, html, reason):
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    slug = reason.lower().replace(' ', '-').replace('/', '-')
    html_path = DEBUG_DIR / f"{slug}.html"
    shot_path = DEBUG_DIR / f"{slug}.png"
    html_path.write_text(html, encoding="utf-8")
    try:
        page.screenshot(path=str(shot_path), full_page=True)
    except Exception as screenshot_error:
        print(f"Warning: failed to save screenshot: {screenshot_error}")
    print(f"Saved debug HTML to {html_path}")
    print(f"Saved debug screenshot to {shot_path}")


def detect_challenge(page, html):
    title = (page.title() or "").strip()
    lowered = html.lower()
    indicators = [
        title in CHALLENGE_TITLES,
        "cf-mitigated" in lowered,
        "challenge-platform" in lowered,
        "enable javascript and cookies to continue" in lowered,
        "just a moment" in lowered,
    ]
    return any(indicators), title


def get_soup(page, url, wait_for_selector=None):
    print(f"Fetching {url}...")
    try:
        response = page.goto(url, wait_until='domcontentloaded', timeout=60000)

        if wait_for_selector:
            try:
                page.wait_for_selector(wait_for_selector, timeout=5000)
            except Exception:
                pass

        page.wait_for_timeout(2000)
        content = page.content()
        challenged, title = detect_challenge(page, content)
        status = response.status if response else "unknown"

        if challenged:
            reason = f"cloudflare-challenge-{status}"
            print(f"Blocked by Cloudflare challenge while fetching {url} (status {status}, title '{title}').")
            save_debug_artifacts(page, content, reason)
            return None

        return BeautifulSoup(content, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_profile_stats_from_soup(soup):
    """Extracts stats from already fetched profile soup."""
    stats = {'year_count': '0', 'to_read_count': '0'}
    if not soup:
        return stats
    
    # 1. Year Count ("THIS YEAR")
    for div in soup.find_all('div'):
        text = div.get_text(strip=True).upper()
        
        if text == "THIS YEAR":
            parent = div.find_parent('div')
            if parent:
                num_span = parent.select_one('.tabular-nums')
                if num_span:
                    stats['year_count'] = num_span.get_text(strip=True)
                    
    # 2. To Read Count
    # Look for: <a href="/to-read/swediot">To-Read Pile (1309)</a>
    to_read_link = soup.select_one(f'a[href*="/to-read/{USERNAME.lower()}"]')
    if to_read_link:
        text = to_read_link.get_text(strip=True)
        if '(' in text and ')' in text:
            try:
                count = text.split('(')[1].split(')')[0]
                stats['to_read_count'] = count
            except IndexError:
                pass

    return stats

def get_books_from_profile_section(soup, section_path, limit=None):
    books = []
    seen = set()
    
    links = soup.select(f'a[href*="{section_path}"]')
    
    for link in links:
        container = link.find_parent(lambda tag: tag.name == 'div' and tag.get('class') and any(c in tag.get('class') for c in ['col-span-2', 'mt-7', 'mt-1']))
        if not container:
            parent = link.find_parent('div')
            if parent:
                parent = parent.find_parent('div')
            container = parent
            
        if not container: continue
            
        book_links = container.select('.book-page-link')
        for bl in book_links:
            url = bl.get('href')
            if url and url.startswith('/'):
                url = "https://app.thestorygraph.com" + url
                
            if url in seen: continue
            seen.add(url)
            
            img = bl.select_one('img')
            if not img: continue
            
            alt = img.get('alt', '')
            parts = alt.split(' by ')
            title = parts[0].strip()
            author = parts[1].strip() if len(parts) > 1 else ''
            
            books.append({
                'title': title,
                'author': author,
                'url': url,
                'image': img.get('src')
            })
            
    if limit:
        books = books[:limit]
    return books

def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not found. Please install: pip install playwright && playwright install chromium")
        return

    data = {}
    
    print("Launching headless browser...")
    with sync_playwright() as p:
        # Launch browser with stealth args
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
        )
        
        # Apply stealth
        try:
            import playwright_stealth
            if hasattr(playwright_stealth, 'Stealth'):
                # Handle v2.x breaking changes
                stealth = playwright_stealth.Stealth()
                if hasattr(stealth, 'apply_stealth_sync'):
                    stealth.apply_stealth_sync(context)
                else:
                    stealth_sync = getattr(playwright_stealth, 'stealth_sync', None)
                    if stealth_sync:
                        stealth_sync(context)
            else:
                # Fallback to v1.x
                playwright_stealth.stealth_sync(context)
        except ImportError:
            print("Warning: playwright-stealth not found. Skipping stealth mode.")

        page = context.new_page()
        page.set_extra_http_headers({
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8'
        })

        try:
            print("Scraping Profile Page...")
            soup = get_soup(page, f"{BASE_URL}/profile/{USERNAME}")
            if not soup:
                print("Failed to get profile page.")
                sys.exit(1)
                
            # 1. Profile Stats
            print("Extracting 'Profile Stats'...")
            stats = get_profile_stats_from_soup(soup)
            data['year_count'] = stats['year_count']
            data['to_read_count'] = stats['to_read_count']

            # 2. Currently Reading
            print("Extracting 'Currently Reading'...")
            data['currently_reading'] = get_books_from_profile_section(soup, f"/currently-reading/")
            
            # 3. Recent 5 Star Reads (Last 5)
            print("Extracting 'Recent 5 Star Reads'...")
            data['recent_five_star'] = get_books_from_profile_section(soup, f"/five_star_reads/", limit=5)

            # 4. Recently Read (Last 5)
            print("Extracting 'Recently Read'...")
            data['recently_read'] = get_books_from_profile_section(soup, f"/books-read/", limit=5)
            
        finally:
            browser.close()
            
    # Validate data before saving
    errors = []
    
    # 1. To Read Count
    if data.get('to_read_count', '0') == '0' or not data.get('to_read_count'):
        errors.append("Error: To Read count is 0 or missing")
        
    # 2. Year Count
    if data.get('year_count', '0') == '0' or not data.get('year_count'):
        errors.append("Error: Year count is 0 or missing")
        
    # 3. Recently Read
    if not data.get('recently_read'):
        errors.append("Error: Recently read list is empty")
        
    # 4. Recent 5 Star
    if not data.get('recent_five_star'):
        errors.append("Error: Recent 5 Star list is empty")

    if errors:
        print("\nValidation Failed:")
        for error in errors:
            print(f"  - {error}")
        print("\nExiting without saving.")
        sys.exit(1)
    
    # Save to _data/books.yml
    print(f"Saving to {OUTPUT_FILE}...")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        
    print("Done!")

if __name__ == "__main__":
    main()
