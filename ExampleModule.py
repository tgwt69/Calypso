"""
# @name Example Movie Module
# @version 1.0
# @type scraper

SoraPlayer Example Module
─────────────────────────
Demonstrates the full module interface:
  - search(query)    → list of media items
  - get_links(item)  → list of playable video links

In a real module you would:
  1. Use `requests` to fetch a webpage
  2. Use `BeautifulSoup` to parse the HTML
  3. Extract titles, posters, video URLs
  4. Return them in the standard format

This example uses mock data so it works without network access.
To adapt it: replace the _fetch_* methods with real scraping logic.
"""

import re
import json
from typing import List, Dict

try:
    import requests
    from bs4 import BeautifulSoup
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False

# ─── Module Metadata ──────────────────────────────────────────────────────────
name    = 'ExampleMovieDB'
version = '1.0'
lang    = 'py'
module_type = 'scraper'

# Base URL of the site you'd scrape (replace with a real one)
BASE_URL = 'https://example-movie-site.com'

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Linux; Android 12; Pixel 6) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/112.0.0.0 Mobile Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': BASE_URL,
}

# ─── Mock data (replace with real scraping) ───────────────────────────────────
MOCK_CATALOG = [
    {
        'id': 'ex_001',
        'title': 'Neon Echoes',
        'poster': 'https://picsum.photos/seed/neon/300/450',
        'year': '2023',
        'type': 'movie',
        'description': (
            'A hacker discovers a conspiracy hidden inside the city\'s '
            'neural network, and must race to expose it before she '
            'becomes the next victim.'
        ),
        'page_url': f'{BASE_URL}/movie/neon-echoes',
    },
    {
        'id': 'ex_002',
        'title': 'The Last Signal',
        'poster': 'https://picsum.photos/seed/signal/300/450',
        'year': '2022',
        'type': 'movie',
        'description': (
            'An astronaut stranded on a dying satellite must repair '
            'contact with Earth before her oxygen runs out.'
        ),
        'page_url': f'{BASE_URL}/movie/the-last-signal',
    },
    {
        'id': 'ex_003',
        'title': 'Dark Meridian',
        'poster': 'https://picsum.photos/seed/dark/300/450',
        'year': '2023',
        'type': 'series',
        'description': (
            'A detective follows a string of impossible murders '
            'across parallel timelines, each one pointing to herself.'
        ),
        'page_url': f'{BASE_URL}/series/dark-meridian',
        'episodes': [
            {'number': 1, 'title': 'Pilot', 'url': f'{BASE_URL}/watch/dark-meridian/1'},
            {'number': 2, 'title': 'The Mirror', 'url': f'{BASE_URL}/watch/dark-meridian/2'},
        ],
    },
    {
        'id': 'ex_004',
        'title': 'Velocity',
        'poster': 'https://picsum.photos/seed/velo/300/450',
        'year': '2024',
        'type': 'movie',
        'description': 'A street racer becomes unwittingly entangled in an international heist.',
        'page_url': f'{BASE_URL}/movie/velocity',
    },
]

# ─── Public Interface ─────────────────────────────────────────────────────────

def search(query: str) -> List[Dict]:
    """
    Search for titles matching `query`.

    Real implementation would do:
        url = f'{BASE_URL}/search?q={requests.utils.quote(query)}'
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        return _parse_search_results(soup)
    """
    query_lower = query.lower()
    results = []
    for item in MOCK_CATALOG:
        if query_lower in item['title'].lower() or query_lower in item['description'].lower():
            result = dict(item)
            result['source_module'] = name
            results.append(result)
    return results


def get_links(item: Dict) -> List[Dict]:
    """
    Resolve video links for `item`.

    Real implementation example:
        page_url = item.get('page_url', '')
        resp = requests.get(page_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        return _extract_video_links(soup)
    """
    # ── Mock links (replace with real extraction) ──────────────────────────
    item_id = item.get('id', '')
    mock_links = {
        'ex_001': [
            {
                'url': 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
                'quality': '1080p',
                'format': 'hls',
                'label': 'Server 1 (HLS)',
            },
            {
                'url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
                'quality': '720p',
                'format': 'mp4',
                'label': 'Server 2 (MP4)',
            },
        ],
        'ex_002': [
            {
                'url': 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
                'quality': '720p',
                'format': 'hls',
                'label': 'Server 1 (HLS)',
            },
        ],
        'ex_003': [
            {
                'url': 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8',
                'quality': '1080p',
                'format': 'hls',
                'label': 'Server 1 (HLS)',
            },
        ],
        'ex_004': [
            {
                'url': 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
                'quality': '1080p',
                'format': 'mp4',
                'label': 'Server 1 (MP4)',
            },
        ],
    }
    return mock_links.get(item_id, [])


# ─── Real Scraping Helpers (templates) ───────────────────────────────────────

def _parse_search_results(soup) -> List[Dict]:
    """
    Example parser for a search results page.
    Adjust selectors to match your target site.
    """
    items = []
    for card in soup.select('.movie-card, .item-card, article.result'):
        title_el  = card.select_one('h2, h3, .title, .name')
        poster_el = card.select_one('img')
        link_el   = card.select_one('a')
        year_el   = card.select_one('.year, .date, time')

        if not title_el:
            continue

        items.append({
            'id':           _slugify(title_el.get_text(strip=True)),
            'title':        title_el.get_text(strip=True),
            'poster':       poster_el['src'] if poster_el and poster_el.get('src') else '',
            'year':         year_el.get_text(strip=True) if year_el else '',
            'type':         'movie',
            'description':  '',
            'page_url':     _abs_url(link_el['href']) if link_el and link_el.get('href') else '',
            'source_module': name,
        })
    return items


def _extract_video_links(soup) -> List[Dict]:
    """
    Example link extractor. Looks for:
    - <source src="..."> inside <video>
    - JavaScript variables holding m3u8 / mp4 URLs
    - iframe embeds (would need further scraping)
    """
    links = []

    # Method 1: <video><source>
    for src in soup.select('video source, video[src]'):
        url = src.get('src', '')
        if url:
            fmt = 'hls' if '.m3u8' in url else 'mp4'
            links.append({'url': url, 'quality': 'auto', 'format': fmt, 'label': 'Direct'})

    # Method 2: JS variable patterns  file:"...", source:"...", etc.
    scripts = ' '.join(s.string or '' for s in soup.find_all('script'))
    patterns = [
        r'(?:file|src|source|url|stream)["\s]*:["\s]*(["\'])(https?://[^"\']+\.(?:m3u8|mp4))\1',
        r'(?:hlsUrl|videoUrl|streamUrl)\s*=\s*["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, scripts, re.IGNORECASE):
            url = match.group(match.lastindex)
            fmt = 'hls' if '.m3u8' in url else 'mp4'
            links.append({'url': url, 'quality': 'auto', 'format': fmt, 'label': 'Extracted'})

    # Deduplicate
    seen = set()
    unique = []
    for lnk in links:
        if lnk['url'] not in seen:
            seen.add(lnk['url'])
            unique.append(lnk)
    return unique


def _abs_url(href: str) -> str:
    if href.startswith('http'):
        return href
    return BASE_URL.rstrip('/') + '/' + href.lstrip('/')


def _slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
