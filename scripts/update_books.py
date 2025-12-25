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

def get_soup(page, url):
    print(f"Fetching {url}...")
    try:
        # Increase timeout just in case
        page.goto(url, timeout=60000)
        # Wait for some content to ensure not just a loading spinner
        page.wait_for_load_state('domcontentloaded')
        content = page.content()
        return BeautifulSoup(content, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_book_pane(pane):
    """Extracts book info from a standard StoryGraph book pane."""
    book = {}
    
    # Title & URL
    book_links = pane.select('a[href^="/books/"]')
    for link in book_links:
        text = link.get_text(strip=True)
        if text:
            book['title'] = text
            book['url'] = BASE_URL + link['href']
            break
            
    if 'title' not in book and book_links:
        book['url'] = BASE_URL + book_links[0]['href']
        
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

def get_year_stats(page, url):
    soup = get_soup(page, url)
    if not soup:
        return None
    
    for div in soup.find_all('div'):
        if div.get_text(strip=True).upper() == "THIS YEAR":
            parent = div.find_parent('div')
            if parent:
                num_span = parent.select_one('.tabular-nums')
                if num_span:
                    return num_span.get_text(strip=True)
    return "0"

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
            
            # 4. Year Stats
            print("Scraping 'Year Stats'...")
            data['year_count'] = get_year_stats(page, f"{BASE_URL}/profile/{USERNAME}")
            
        finally:
            browser.close()
    
    # Save to _data/books.yml
    print(f"Saving to {OUTPUT_FILE}...")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        
    print("Done!")

if __name__ == "__main__":
    main()
