import argparse
import errno
import json
import os
import re
import shutil
import socket
import sys
import time
from pathlib import Path

import yaml
from bs4 import BeautifulSoup
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

USERNAME = os.getenv("STORYGRAPH_USERNAME", "swediot")
BASE_URL = "https://app.thestorygraph.com"
OUTPUT_FILE = os.getenv("STORYGRAPH_OUTPUT_FILE", "_data/books.yml")
DEBUG_DIR = Path("tmp/storygraph-debug")
DEFAULT_PROFILE_DIR = Path.home() / ".cache" / "storygraph-browser-profile"
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

CHROME_CANDIDATES = (
    "/usr/bin/google-chrome-stable",
    "/usr/bin/google-chrome",
    "/opt/google/chrome/chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
)

CHROMIUM_CANDIDATES = (
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
)

CHALLENGE_MARKERS = (
    "just a moment...",
    "cf-mitigated",
    "performing security verification",
    "enable javascript and cookies to continue",
    "attention required! | cloudflare",
)


def env_flag(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def ensure_debug_dir():
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)


def resolve_browser_launch_options():
    """Prefer real Google Chrome when installed, then system Chromium, then Playwright Chromium."""
    explicit_exec = os.getenv("STORYGRAPH_BROWSER_EXECUTABLE")
    if explicit_exec:
        return {"executable_path": explicit_exec}

    explicit_channel = os.getenv("STORYGRAPH_BROWSER_CHANNEL")
    if explicit_channel:
        return {"channel": explicit_channel}

    for candidate in CHROME_CANDIDATES:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return {"executable_path": candidate}

    for name in ("google-chrome-stable", "google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return {"executable_path": found}

    for candidate in CHROMIUM_CANDIDATES:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return {"executable_path": candidate}

    return {}


def cleanup_stale_profile_locks(profile_dir: Path):
    """Remove stale Chromium Singleton* files left behind if an earlier cron run crashed."""
    lock_path = profile_dir / "SingletonLock"
    if not lock_path.is_symlink():
        return

    try:
        target = os.readlink(lock_path)
    except OSError:
        return

    host, sep, pid_str = target.rpartition("-")
    if not sep or not pid_str.isdigit():
        return

    local_hosts = {socket.gethostname(), socket.getfqdn(), socket.gethostname().split(".")[0]}
    if host not in local_hosts:
        return

    pid = int(pid_str)
    try:
        os.kill(pid, 0)
        return  # Process is still alive; leave lock intact.
    except OSError as exc:
        if exc.errno != errno.ESRCH:
            return

    print(f"Removing stale browser lock {lock_path} (dead PID {pid})...")
    for name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        stale = profile_dir / name
        try:
            if stale.is_symlink() or stale.exists():
                stale.unlink()
        except OSError:
            pass


def is_challenge_html(html: str) -> bool:
    lowered = html.lower()
    return any(marker in lowered for marker in CHALLENGE_MARKERS)


def has_profile_markers(html: str) -> bool:
    return (
        f"/books-read/{USERNAME}" in html
        or f"/to-read/{USERNAME}" in html
        or f"@{USERNAME}" in html
    )


def save_debug_artifacts(html: str, page=None):
    ensure_debug_dir()
    html_path = DEBUG_DIR / "profile.html"
    html_path.write_text(html or "", encoding="utf-8")
    screenshot_note = ""
    if page is not None:
        png_path = DEBUG_DIR / "profile.png"
        try:
            page.screenshot(path=str(png_path), full_page=True)
            screenshot_note = f" and {png_path}"
        except Exception:
            pass
    return f"{html_path}{screenshot_note}"


def fetch_profile_html(
    profile_dir: Path,
    headless: bool = True,
    challenge_timeout: int = 30,
    cookies_file: Path | None = None,
) -> str:
    """Fetch StoryGraph profile using a persistent browser context to retain cookies across runs."""
    profile_dir = profile_dir.expanduser()
    profile_dir.mkdir(parents=True, exist_ok=True)
    cleanup_stale_profile_locks(profile_dir)

    launch_opts = resolve_browser_launch_options()
    browser_desc = launch_opts.get("executable_path") or launch_opts.get("channel") or "playwright-chromium"
    mode_desc = "headless" if headless else "headed"
    print(f"Fetching {PROFILE_URL} via {browser_desc} ({mode_desc}, profile={profile_dir})...")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=headless,
            viewport={"width": 1366, "height": 900},
            locale="en-GB",
            **launch_opts,
        )
        try:
            if cookies_file:
                cookie_data = json.loads(Path(cookies_file).expanduser().read_text(encoding="utf-8"))
                if isinstance(cookie_data, list) and cookie_data:
                    context.add_cookies(cookie_data)

            page = context.pages[0] if context.pages else context.new_page()
            response = page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=45000)
            status = response.status if response else None

            deadline = time.monotonic() + max(1, challenge_timeout)
            html = page.content()

            while time.monotonic() < deadline:
                html = page.content()
                if has_profile_markers(html) and not is_challenge_html(html):
                    try:
                        page.wait_for_selector('a[href*="/books/"]', timeout=5000)
                    except PlaywrightError:
                        pass
                    return page.content()

                if not is_challenge_html(html) and status and status >= 400:
                    break

                page.wait_for_timeout(1000)

            html = page.content()
            saved = save_debug_artifacts(html, page=page)
            if is_challenge_html(html):
                raise RuntimeError(
                    f"Cloudflare challenge did not resolve within {challenge_timeout}s "
                    f"(HTTP {status}). Saved debug artifacts to {saved}"
                )
            raise RuntimeError(
                f"Unexpected profile response (HTTP {status}). Saved debug artifacts to {saved}"
            )
        finally:
            context.close()


def parse_counts(soup):
    counts = {"year_count": None, "to_read_count": None}

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
    if not data.get("to_read_count") or data["to_read_count"] == "0":
        errors.append("To Read count is 0 or missing")
    if data.get("year_count") is None:
        errors.append("Year count is missing")
    if not data.get("recently_read"):
        errors.append("Recently read list is empty")
    if not data.get("recent_five_star"):
        errors.append("Recent 5 Star list is empty")
    if errors:
        raise RuntimeError("Validation failed: " + "; ".join(errors))


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Update _data/books.yml from StoryGraph profile.")
    parser.add_argument(
        "--profile-dir",
        default=os.getenv("STORYGRAPH_PROFILE_DIR", str(DEFAULT_PROFILE_DIR)),
        help="Persistent browser user data directory (default: ~/.cache/storygraph-browser-profile).",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        default=not env_flag("STORYGRAPH_HEADLESS", default=True),
        help="Run browser in headed mode (use under xvfb-run on headless Linux or for interactive warmup).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.getenv("STORYGRAPH_CHALLENGE_TIMEOUT", "30")),
        help="Seconds to wait for Cloudflare interstitial / StoryGraph DOM before failing.",
    )
    parser.add_argument(
        "--cookies-file",
        default=os.getenv("STORYGRAPH_COOKIES_FILE"),
        help="Optional JSON file of cookies to seed into the persistent browser profile.",
    )
    parser.add_argument(
        "--soft-fail",
        action="store_true",
        default=env_flag("STORYGRAPH_SOFT_FAIL", default=False),
        help="Exit 0 without touching _data/books.yml when blocked so cron keeps the last good build.",
    )
    return parser


def main(argv=None):
    args = build_arg_parser().parse_args(argv)

    try:
        html = fetch_profile_html(
            profile_dir=Path(args.profile_dir),
            headless=not args.headed,
            challenge_timeout=args.timeout,
            cookies_file=Path(args.cookies_file) if args.cookies_file else None,
        )
    except Exception as error:
        print(f"Error fetching StoryGraph data: {error}")
        sys.exit(0 if args.soft_fail else 1)

    soup = BeautifulSoup(html, "html.parser")
    data = parse_counts(soup)
    sections = parse_sections(soup)
    data.update(sections)

    try:
        validate_data(data)
    except Exception as error:
        saved = save_debug_artifacts(html)
        print(f"{error} (saved HTML to {saved})")
        sys.exit(0 if args.soft_fail else 1)

    print(f"Saving to {OUTPUT_FILE}...")
    out_dir = os.path.dirname(OUTPUT_FILE)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as handle:
        yaml.dump(data, handle, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print("Done!")


if __name__ == "__main__":
    main()
