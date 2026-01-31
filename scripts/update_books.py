import requests
from bs4 import BeautifulSoup
import yaml
import os
import datetime
import sys

# Configuration
USERNAME = "swediot"
BASE_URL = "https://app.thestorygraph.com"
OUTPUT_FILE = "_data/books.yml"

def get_soup(page, url, wait_for_selector=None):
    print(f"Fetching {url}...")
    try:
        # Increase timeout just in case
        page.goto(url, timeout=60000)
        # Wait for some content to ensure not just a loading spinner
        page.wait_for_load_state('domcontentloaded')
        
        if wait_for_selector:
             try:
                page.wait_for_selector(wait_for_selector, timeout=5000)
             except Exception:
                # Optional: log warning if verbose
                # print(f"  Warning: Timeout waiting for selector '{wait_for_selector}'")
                pass

        content = page.content()
        return BeautifulSoup(content, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_book_pane(pane):
    """Extracts book info from a standard StoryGraph book pane."""
    book = {}
    
    # Title & URL
    # Valid title links start with /books/ and are NOT editions links
    # Selector: .book-pane a[href^='/books/']:not([href*='/editions'])
    book_link = pane.select_one("a[href^='/books/']:not([href*='/editions'])")
    
    if book_link:
        text = book_link.get_text(strip=True)
        if text:
            book['title'] = text
            book['url'] = BASE_URL + book_link['href']

    # Fallback to any book link if specific one not found (robustness)
    if 'title' not in book:
         book_links = pane.select('a[href^="/books/"]')
         for link in book_links:
            text = link.get_text(strip=True)
            if text:
                book['title'] = text
                book['url'] = BASE_URL + link['href']
                break
            
    if 'title' not in book and book_link:
         book['url'] = BASE_URL + book_link['href']
        
    # Author
    author_node = pane.select_one('a[href^="/authors/"]')
    if author_node:
        book['author'] = author_node.get_text(strip=True)
        
    # Image
    img_node = pane.select_one('.book-cover img')
    if not img_node:
        img_node = pane.select_one('img')
        
    if img_node:
        book['image'] = img_node.get('src')
        if not book.get('title') and img_node.get('alt'):
             parts = img_node['alt'].split(" by ")
             if len(parts) >= 1:
                 book['title'] = parts[0]

    return book if book.get('title') else None

def get_profile_stats(page, url):
    """Scrapes profile page for various stats."""
    soup = get_soup(page, url)
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

def get_books_from_url(page, url, limit=None):
    soup = get_soup(page, url)
    books = []
    if not soup:
        return books
        
    panes = soup.select('.book-pane')
    if not panes:
        panes = soup.select('.read-books-row')

    seen_urls = set()
    for pane in panes:
        book = parse_book_pane(pane)
        if book and book.get('url') not in seen_urls:
            books.append(book)
            seen_urls.add(book['url'])
            if limit and len(books) >= limit:
                break
    return books

def get_rolling_year_books_count(page):
    """Calculates books read in the current month + last 12 months."""
    print("Calculating rolling year book count...")
    total_count = 0
    today = datetime.date.today()
    
    # Current month (0) + 12 previous months = 13 months total
    for i in range(13):
        year = today.year
        month = today.month - i
        
        while month <= 0:
            month += 12
            year -= 1
            
        url = f"{BASE_URL}/books-read/{USERNAME}?year={year}&month={month}"
        
        # Wait for the count element to ensure dynamic content is loaded
        soup = get_soup(page, url, wait_for_selector='.search-results-count')
        
        if soup:
            count_node = soup.select_one('.search-results-count')
            if count_node:
                text = count_node.get_text(strip=True)
                # Text example: "3 books" or "1 book"
                try:
                    count = int(text.split()[0])
                    total_count += count
                    print(f"  {year}-{month}: {count} books")
                except (ValueError, IndexError):
                    print(f"  {year}-{month}: Could not parse count from '{text}'")
            else:
                print(f"  {year}-{month}: No count element found. Assuming 0.")

    return str(total_count)

    return str(total_count)

def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright not found. Please install: pip install playwright && playwright install chromium")
        return

    data = {}
    
    print("Launching headless browser...")
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        try:
            # 1. Currently Reading
            print("Scraping 'Currently Reading'...")
            data['currently_reading'] = get_books_from_url(page, f"{BASE_URL}/currently-reading/{USERNAME}")
            
            # 2. Recently Read (Last 5)
            print("Scraping 'Recently Read'...")
            data['recently_read'] = get_books_from_url(page, f"{BASE_URL}/books-read/{USERNAME}", limit=5)
            
            # 3. Recent 5 Star Reads (Last 5)
            print("Scraping 'Recent 5 Star Reads'...")
            data['recent_five_star'] = get_books_from_url(page, f"{BASE_URL}/five_star_reads/{USERNAME}", limit=5)
            
            # 4. Profile Stats
            print("Scraping 'Profile Stats'...")
            stats = get_profile_stats(page, f"{BASE_URL}/profile/{USERNAME}")
            
            # 5. Rolling Year Count (Current month + last 12 months)
            data['year_count'] = get_rolling_year_books_count(page)
            data['to_read_count'] = stats['to_read_count']
            
        finally:
            browser.close()
            
    # Validate data before saving
    errors = []
    
    # 1. To Read Count
    if data.get('to_read_count', '0') == '0':
        errors.append("Error: To Read count is 0")
        
    # 2. Year Count
    if data.get('year_count', '0') == '0':
        errors.append("Error: Year count is 0")
        
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
