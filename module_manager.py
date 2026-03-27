"""
SoraPlayer — Module Manager
Handles loading, installing, updating, and executing .py and .js modules.
JS modules are run via Js2Py for compatibility with Sora/Luna modules.
"""

import os
import sys
import json
import hashlib
import importlib.util
import traceback
import threading
from typing import List, Dict, Any, Optional

try:
    import requests
except ImportError:
    requests = None

try:
    import js2py
    JS2PY_AVAILABLE = True
except ImportError:
    JS2PY_AVAILABLE = False

# ─── Module Manifest Schema ───────────────────────────────────────────────────
# Each installed module has an entry in manifest.json:
# {
#   "id":      "unique_slug",
#   "name":    "Human-readable name",
#   "version": "1.0",
#   "lang":    "py" | "js",
#   "type":    "scraper" | "api",
#   "file":    "filename.py",
#   "url":     "source URL or local path",
#   "enabled": true
# }
# ──────────────────────────────────────────────────────────────────────────────


class BaseModule:
    """
    Abstract base for all SoraPlayer modules.
    Python modules should subclass this directly.
    JS modules are wrapped in this interface automatically.
    """

    # Metadata — override in subclasses
    name    = 'Unnamed Module'
    version = '1.0'
    lang    = 'py'
    module_type = 'scraper'   # 'scraper' | 'api'

    def search(self, query: str) -> List[Dict]:
        """
        Search for content matching `query`.

        Returns a list of dicts:
        [
          {
            "id":           "unique item id",
            "title":        "Movie/Show Title",
            "poster":       "https://...image.jpg",
            "year":         "2023",
            "type":         "movie" | "series",
            "description":  "...",
            "source_module": self.name,
            "extra":        {}   # anything the module wants to pass to get_links
          }
        ]
        """
        raise NotImplementedError

    def get_links(self, item: Dict) -> List[Dict]:
        """
        Resolve playable video links for `item` (from search() result).

        Returns a list of dicts:
        [
          {
            "url":     "https://.../video.m3u8",
            "quality": "1080p",
            "format":  "hls" | "mp4" | "dash",
            "label":   "Server 1"
          }
        ]
        """
        raise NotImplementedError


# ─── JS Module Wrapper ────────────────────────────────────────────────────────

class JSModuleWrapper(BaseModule):
    """
    Wraps a Sora/Luna-compatible JavaScript module loaded via Js2Py.
    Expects the JS to export (or define at top level):
        - async function search(query) -> [...] 
        - async function getLinks(item) -> [...]
    Since Js2Py runs synchronously, we resolve promises inline.
    """

    def __init__(self, js_source: str, meta: Dict):
        self.name    = meta.get('name', 'JS Module')
        self.version = meta.get('version', '1.0')
        self.lang    = 'js'
        self._meta   = meta
        self._context = None
        self._load(js_source)

    def _load(self, js_source: str):
        if not JS2PY_AVAILABLE:
            raise RuntimeError('js2py is not installed. Run: pip install js2py')

        # Polyfill minimal browser/Node globals Sora modules might expect
        polyfill = """
        var console = { log: function(){}, error: function(){}, warn: function(){} };
        var window = {};
        var module = { exports: {} };
        var exports = module.exports;
        function require(name) { return {}; }
        // Minimal fetch polyfill — modules should ideally use provided http util
        function fetch(url, opts) {
            return { then: function(cb) { return { then: function(){}, catch: function(){} }; } };
        }
        """
        try:
            self._context = js2py.EvalJs()
            self._context.execute(polyfill)
            self._context.execute(js_source)
        except Exception as e:
            raise RuntimeError(f'JS parse error: {e}')

    def _call_js_function(self, fn_name: str, *args) -> Any:
        """Call a JS function and unwrap the result (handles Promises naively)."""
        ctx = self._context
        try:
            fn = getattr(ctx, fn_name, None)
            if fn is None:
                # Try camelCase variants
                for variant in [fn_name, fn_name + 'Async', 'get' + fn_name.capitalize()]:
                    fn = getattr(ctx, variant, None)
                    if fn is not None:
                        break
            if fn is None:
                return []
            result = fn(*args)
            # js2py returns PyJs objects — convert to Python
            return self._to_python(result)
        except Exception as e:
            print(f'[JSModule] Error calling {fn_name}: {e}')
            return []

    def _to_python(self, obj) -> Any:
        """Recursively convert js2py objects to native Python types."""
        if obj is None:
            return None
        try:
            # Try direct conversion first
            if hasattr(obj, 'to_list'):
                return [self._to_python(i) for i in obj.to_list()]
            if hasattr(obj, 'to_dict'):
                return {k: self._to_python(v) for k, v in obj.to_dict().items()}
            if hasattr(obj, '__iter__') and not isinstance(obj, str):
                return [self._to_python(i) for i in obj]
            return obj
        except Exception:
            return str(obj)

    def search(self, query: str) -> List[Dict]:
        results = self._call_js_function('search', query)
        if isinstance(results, list):
            for item in results:
                item.setdefault('source_module', self.name)
            return results
        return []

    def get_links(self, item: Dict) -> List[Dict]:
        links = self._call_js_function('getLinks', item)
        if isinstance(links, list):
            return links
        return []


# ─── Module Manager ───────────────────────────────────────────────────────────

class ModuleManager:

    MANIFEST_FILE = 'manifest.json'

    def __init__(self, modules_dir: str):
        self.modules_dir = modules_dir
        self.manifest_path = os.path.join(modules_dir, self.MANIFEST_FILE)
        self._manifest: List[Dict] = []
        self._loaded: Dict[str, BaseModule] = {}   # id -> module instance
        self._lock = threading.Lock()

        os.makedirs(modules_dir, exist_ok=True)
        self._load_manifest()
        self._load_all()

    # ── Manifest I/O ──────────────────────────────────────────────────────────

    def _load_manifest(self):
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path) as f:
                    self._manifest = json.load(f)
            except Exception:
                self._manifest = []
        else:
            self._manifest = []

    def _save_manifest(self):
        with open(self.manifest_path, 'w') as f:
            json.dump(self._manifest, f, indent=2)

    # ── Loading ───────────────────────────────────────────────────────────────

    def _load_all(self):
        """Load all enabled modules from manifest."""
        for entry in self._manifest:
            if entry.get('enabled', True):
                self._load_module(entry)

    def _load_module(self, entry: Dict) -> Optional[BaseModule]:
        """Load a single module from its manifest entry."""
        mod_id   = entry['id']
        filename = entry['file']
        lang     = entry.get('lang', 'py')
        filepath = os.path.join(self.modules_dir, filename)

        if not os.path.exists(filepath):
            print(f'[ModuleManager] File not found: {filepath}')
            return None

        try:
            if lang == 'py':
                instance = self._load_py_module(filepath, entry)
            elif lang == 'js':
                instance = self._load_js_module(filepath, entry)
            else:
                print(f'[ModuleManager] Unknown lang: {lang}')
                return None

            if instance:
                with self._lock:
                    self._loaded[mod_id] = instance
                print(f'[ModuleManager] Loaded: {entry["name"]} ({lang})')
                return instance
        except Exception as e:
            print(f'[ModuleManager] Failed to load {filename}: {e}')
            traceback.print_exc()
        return None

    def _load_py_module(self, filepath: str, meta: Dict) -> Optional[BaseModule]:
        """Dynamically import a Python module file."""
        mod_id = meta['id']
        spec = importlib.util.spec_from_file_location(f'sora_module_{mod_id}', filepath)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Find a class that subclasses BaseModule
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if (isinstance(attr, type) and
                    issubclass(attr, BaseModule) and
                    attr is not BaseModule):
                instance = attr()
                instance.name    = meta.get('name', instance.name)
                instance.version = meta.get('version', instance.version)
                return instance

        # Fallback: wrap module-level functions
        if hasattr(mod, 'search') and hasattr(mod, 'get_links'):
            return _FunctionWrapperModule(mod, meta)

        raise ValueError(f'No valid module class or search/get_links functions found in {filepath}')

    def _load_js_module(self, filepath: str, meta: Dict) -> Optional[JSModuleWrapper]:
        """Load a JS module via Js2Py."""
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        return JSModuleWrapper(source, meta)

    # ── Installation ──────────────────────────────────────────────────────────

    def install_from_url(self, url: str) -> Dict:
        """
        Download a module from a URL and register it.
        Supports .py and .js files.
        Returns {'success': bool, 'name': str, 'error': str}
        """
        if not requests:
            return {'success': False, 'error': 'requests library not available'}

        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            source = resp.text
        except Exception as e:
            return {'success': False, 'error': f'Download failed: {e}'}

        # Determine language
        url_lower = url.lower()
        if url_lower.endswith('.js'):
            lang = 'js'
        elif url_lower.endswith('.py'):
            lang = 'py'
        else:
            # Sniff content
            lang = 'js' if 'function ' in source[:500] else 'py'

        # Parse metadata from file header comments
        meta = self._parse_module_meta(source, lang)

        # Generate unique ID from URL
        mod_id = hashlib.md5(url.encode()).hexdigest()[:10]
        meta.setdefault('id', mod_id)
        meta.setdefault('name', os.path.basename(url).split('.')[0])
        meta['lang']    = lang
        meta['url']     = url
        meta['enabled'] = True
        filename = f'{mod_id}.{lang}'
        meta['file'] = filename

        # Save file
        filepath = os.path.join(self.modules_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(source)

        # Add to manifest (replace if same id)
        self._manifest = [m for m in self._manifest if m['id'] != mod_id]
        self._manifest.append(meta)
        self._save_manifest()

        # Load immediately
        instance = self._load_module(meta)
        if instance is None:
            return {'success': False, 'error': 'Module loaded but no valid search/get_links found'}

        return {'success': True, 'name': meta['name']}

    def install_from_file(self, filepath: str) -> Dict:
        """Copy a local file and register as a module."""
        if not os.path.exists(filepath):
            return {'success': False, 'error': 'File not found'}

        lang = 'js' if filepath.endswith('.js') else 'py'
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()

        meta = self._parse_module_meta(source, lang)
        mod_id = hashlib.md5(filepath.encode()).hexdigest()[:10]
        meta.setdefault('id', mod_id)
        meta.setdefault('name', os.path.basename(filepath).split('.')[0])
        meta['lang'] = lang
        meta['file'] = os.path.basename(filepath)
        meta['enabled'] = True

        import shutil
        dest = os.path.join(self.modules_dir, meta['file'])
        if filepath != dest:
            shutil.copy2(filepath, dest)

        self._manifest = [m for m in self._manifest if m['id'] != mod_id]
        self._manifest.append(meta)
        self._save_manifest()
        self._load_module(meta)
        return {'success': True, 'name': meta['name']}

    def _parse_module_meta(self, source: str, lang: str) -> Dict:
        """
        Extract metadata from comment headers.
        Supports both Python and JS style:
          # @name My Module
          // @name My Module
        """
        meta = {}
        for line in source.splitlines()[:20]:
            line = line.strip().lstrip('#').lstrip('//').lstrip('*').strip()
            if line.startswith('@name '):
                meta['name'] = line[6:].strip()
            elif line.startswith('@version '):
                meta['version'] = line[9:].strip()
            elif line.startswith('@type '):
                meta['type'] = line[6:].strip()
        return meta

    # ── Removal / Toggle ──────────────────────────────────────────────────────

    def remove_module(self, mod_id: str):
        entry = self._get_entry(mod_id)
        if entry:
            filepath = os.path.join(self.modules_dir, entry['file'])
            if os.path.exists(filepath):
                os.remove(filepath)
            self._manifest = [m for m in self._manifest if m['id'] != mod_id]
            self._save_manifest()
            with self._lock:
                self._loaded.pop(mod_id, None)

    def toggle_module(self, mod_id: str, enabled: bool):
        for entry in self._manifest:
            if entry['id'] == mod_id:
                entry['enabled'] = enabled
                if enabled:
                    self._load_module(entry)
                else:
                    with self._lock:
                        self._loaded.pop(mod_id, None)
                break
        self._save_manifest()

    # ── Queries ───────────────────────────────────────────────────────────────

    def search_all(self, query: str) -> List[Dict]:
        """
        Query all loaded modules simultaneously and merge results.
        Thread-safe — spawns one thread per module.
        """
        results = []
        threads = []
        lock = threading.Lock()

        with self._lock:
            modules = dict(self._loaded)

        def _search_one(mod_id, mod):
            try:
                items = mod.search(query) or []
                for item in items:
                    item.setdefault('source_module', mod.name)
                with lock:
                    results.extend(items)
            except Exception as e:
                print(f'[ModuleManager] Search error in {mod_id}: {e}')

        for mod_id, mod in modules.items():
            t = threading.Thread(target=_search_one, args=(mod_id, mod), daemon=True)
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=10)  # 10s timeout per module

        return results

    def get_links(self, item: Dict) -> List[Dict]:
        """
        Get video links for an item. Routes to the correct module
        by source_module name or tries all if unspecified.
        """
        source_mod_name = item.get('source_module')
        with self._lock:
            modules = dict(self._loaded)

        for mod_id, mod in modules.items():
            if source_mod_name and mod.name != source_mod_name:
                continue
            try:
                links = mod.get_links(item)
                if links:
                    return links
            except Exception as e:
                print(f'[ModuleManager] get_links error in {mod_id}: {e}')

        return []

    def get_installed_modules(self) -> List[Dict]:
        return list(self._manifest)

    def _get_entry(self, mod_id: str) -> Optional[Dict]:
        for m in self._manifest:
            if m['id'] == mod_id:
                return m
        return None


# ─── Function Wrapper (for modules that don't subclass BaseModule) ────────────

class _FunctionWrapperModule(BaseModule):
    """Wraps a module that exposes search() and get_links() as top-level functions."""

    def __init__(self, mod, meta: Dict):
        self._mod = mod
        self.name    = meta.get('name', getattr(mod, 'name', 'Unknown'))
        self.version = meta.get('version', getattr(mod, 'version', '1.0'))
        self.lang    = meta.get('lang', 'py')

    def search(self, query: str) -> List[Dict]:
        return self._mod.search(query) or []

    def get_links(self, item: Dict) -> List[Dict]:
        return self._mod.get_links(item) or []
