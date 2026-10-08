import re
import time
from collections import Counter, deque
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from src.config import CATEGORIES, DATA_DIR, MAX_SCRAPE_PAGES, WEBSITE_URL

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TechCADD-RAG-Bot/1.0)"}

SKIP_URL_PARTS = (
    "login", "logout", "studentlogin", "dailytask", "/vertical", "javascript:",
    "mailto:", "tel:", "wa.me", ".jpg", ".jpeg", ".png", ".gif", ".svg",
    ".webp", ".pdf", ".mp4", ".zip",
)

# Order matters: first match wins. Checked against the URL path, then the title.
CATEGORY_RULES = [
    ("announcements", ("blog", "event", "seminar", "workshop", "gallery", "news")),
    ("admission", ("admission", "fee", "enquir", "contact", "demo", "certificate-verification", "franchise", "faq")),
    ("career", ("placement", "job", "career")),
    ("courses", ("course", "training", "certificate", "program", "autocad", "solid-works", "revit", "3d")),
    ("company", ("about", "review", "testimonial", "team")),
]

REMOVE_TAGS = ["script", "style", "noscript", "svg", "nav", "header", "footer", "form", "iframe", "video"]
REMOVE_HINTS = re.compile(r"(navbar|menu|popup|modal|offcanvas|cookie|breadcrumb|mobile-nav)", re.I)


def _host(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def _normalize(url: str) -> str:
    url, _ = urldefrag(url)
    p = urlparse(url)
    path = "/" if p.path in ("", "/index.php", "/index.html") else p.path
    return p._replace(path=path, query="", fragment="").geturl()


def classify(url: str, title: str = "") -> str:
    path = urlparse(url).path.lower()
    for text in (path, title.lower()):
        for category, keywords in CATEGORY_RULES:
            if any(k in text for k in keywords):
                return category
    return "company"


def _slug(url: str) -> str:
    path = urlparse(url).path.strip("/") or "home"
    path = re.sub(r"\.php$|\.html?$", "", path)
    return re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_")[:80] or "home"


def _extract(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # Collect links first: navigation menus are the best way to discover course pages
    links = [a["href"] for a in soup.find_all("a", href=True)]
    title = (soup.title.get_text(strip=True) if soup.title else "") or ""

    for tag in soup(REMOVE_TAGS):
        tag.decompose()
    for tag in list(soup.find_all(True)):
        if getattr(tag, "decomposed", False) or tag.attrs is None:
            continue
        ident = " ".join(tag.get("class", [])) + " " + (tag.get("id") or "")
        if REMOVE_HINTS.search(ident):
            tag.decompose()

    lines = [re.sub(r"\s+", " ", ln).strip() for ln in soup.get_text("\n").split("\n")]
    lines = [ln for ln in lines if len(ln) > 2]
    return title, links, lines


def _drop_boilerplate(pages: dict) -> None:
    """Remove lines repeated on most pages (menus, footers, popups)."""
    if len(pages) < 5:
        return
    counts = Counter()
    for _, _, lines in pages.values():
        counts.update(set(lines))
    limit = 0.6 * len(pages)
    for url, (title, cat, lines) in list(pages.items()):
        pages[url] = (title, cat, [ln for ln in lines if counts[ln] <= limit])


def scrape_website(start_url: str = WEBSITE_URL, max_pages: int = MAX_SCRAPE_PAGES) -> int:
    start = _normalize(start_url)
    base_host = _host(start)
    queue, seen, pages = deque([start]), {start}, {}

    while queue and len(pages) < max_pages:
        url = queue.popleft()
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code != 200 or "text/html" not in r.headers.get("content-type", ""):
                continue
            r.encoding = r.encoding or "utf-8"
            title, links, lines = _extract(r.text)
        except requests.RequestException as exc:
            print(f"[scraper] skipped {url}: {exc}")
            continue

        pages[url] = (title, classify(url, title), lines)
        for href in links:
            nxt = _normalize(urljoin(url, href))
            if (
                nxt not in seen
                and _host(nxt) == base_host
                and not any(s in nxt.lower() for s in SKIP_URL_PARTS)
            ):
                seen.add(nxt)
                queue.append(nxt)
        time.sleep(0.3)  # be polite to the server

    if not pages:
        raise RuntimeError("Scraper could not fetch any page. Check the URL / internet access.")

    _drop_boilerplate(pages)

    # Remove old scraped files only (hand-curated files stay)
    for cat in CATEGORIES:
        for old in (DATA_DIR / cat).glob("web_*.txt"):
            old.unlink()

    written = 0
    for url, (title, cat, lines) in pages.items():
        body = "\n".join(lines).strip()
        if len(body) < 200:  # nothing useful on this page
            continue
        out_dir = DATA_DIR / cat
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"web_{_slug(url)}.txt").write_text(
            f"Title: {title}\nSource: {url}\n\n{body}\n", encoding="utf-8"
        )
        written += 1

    print(f"[scraper] crawled {len(pages)} pages, saved {written} files")
    return written
