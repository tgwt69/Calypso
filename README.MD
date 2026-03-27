# Calypso

A modular, Sora-inspired media player for Android built with Python + Kivy.  
Install modules to unlock content sources — the app itself is an empty shell.

-----

## Project Structure

```
SoraPlayer/
├── main.py              # App entry point, UI, screen management
├── module_manager.py    # Module loader, installer, JS runner
├── buildozer.spec       # Android build config
├── history.json         # Auto-generated watch history
├── Modules/
│   ├── manifest.json    # Auto-generated module registry
│   ├── ExampleModule.py # Sample Python scraper module
│   └── ExampleModule.js # Sample JavaScript module (Sora/Luna compatible)
└── assets/
    ├── icon.png
    └── presplash.png
```

-----

## Running on Desktop (Development)

```bash
pip install kivy requests beautifulsoup4 js2py pillow
python main.py
```

-----

## Building for Android

```bash
pip install buildozer
buildozer android debug deploy run
```

First build takes 20–40 minutes (downloads NDK, SDK, Python for Android).

-----

## Writing a Python Module

Create a file in `Modules/` with a header and `search` + `get_links` functions:

```python
# @name My Source
# @version 1.0
# @type scraper

import requests
from bs4 import BeautifulSoup

name = "My Source"
BASE_URL = "https://your-site.com"
HEADERS = {"User-Agent": "Mozilla/5.0 ..."}

def search(query):
    resp = requests.get(f"{BASE_URL}/search?q={query}", headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for card in soup.select(".movie-card"):
        results.append({
            "id":           card["data-id"],
            "title":        card.select_one("h2").text,
            "poster":       card.select_one("img")["src"],
            "year":         card.select_one(".year").text,
            "type":         "movie",
            "description":  "",
            "page_url":     BASE_URL + card.select_one("a")["href"],
            "source_module": name,
        })
    return results

def get_links(item):
    resp = requests.get(item["page_url"], headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")
    # Extract .m3u8 or .mp4 URLs from the page
    return [{"url": "...", "quality": "1080p", "format": "hls", "label": "Server 1"}]
```

-----

## Writing a JavaScript Module (Sora/Luna Compatible)

Existing Sora/Luna `.js` modules work if they expose:

- `search(query)` → array of items
- `getLinks(item)` → array of link objects

```javascript
// @name My JS Source
// @version 1.0

var BASE_URL = "https://your-site.com";

function search(query) {
    // ... scraping logic
    return [{ id: "1", title: "...", poster: "...", source_module: "My JS Source" }];
}

function getLinks(item) {
    return [{ url: "https://...video.m3u8", quality: "1080p", format: "hls" }];
}
```

> **Note:** Js2Py runs JavaScript synchronously. Modules that rely heavily on  
> `async/await` or real `fetch()` calls will need adaptation. For best results,  
> use the Python module format for new sources.

-----

## Installing a Module

**In the app:** Settings tab → paste the module URL → Install Module  
**Manually:** Drop the `.py` or `.js` file into the `Modules/` folder and restart.

-----

## Item Object Schema

```json
{
  "id":            "unique-string",
  "title":         "Movie Title",
  "poster":        "https://image.url/poster.jpg",
  "year":          "2024",
  "type":          "movie | series",
  "description":   "Synopsis...",
  "page_url":      "https://source-site.com/movie/slug",
  "source_module": "Module Name",
  "episodes": [
    { "number": 1, "title": "Pilot", "url": "..." }
  ]
}
```

## Link Object Schema

```json
{
  "url":     "https://cdn.example.com/stream.m3u8",
  "quality": "1080p",
  "format":  "hls | mp4 | dash",
  "label":   "Server 1"
}
```

-----

## Supported Formats

|Format|Extension|Notes                                      |
|------|---------|-------------------------------------------|
|HLS   |`.m3u8`  |Adaptive bitrate, works on Android natively|
|MP4   |`.mp4`   |Direct play                                |
|DASH  |`.mpd`   |Requires ExoPlayer (pyjnius bridge)        |

-----

## Picture-in-Picture

PiP is configured in `buildozer.spec` via `android:supportsPictureInPicture="true"`.  
To trigger it in code:

```python
from jnius import autoclass
PythonActivity = autoclass('org.kivy.android.PythonActivity')
activity = PythonActivity.mActivity
activity.enterPictureInPictureMode()
```

Add this to the player screen’s back button or home button handler.
