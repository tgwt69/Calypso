"""
SoraPlayer - Modular Media Player for Android
Main Application Entry Point
"""

import os
import sys
import json
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import AsyncImage, Image
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.video import Video
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.properties import (
    StringProperty, ListProperty, DictProperty,
    BooleanProperty, NumericProperty, ObjectProperty
)
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.utils import get_color_from_hex
from kivy.animation import Animation
from kivy.lang import Builder
import threading

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))
from module_manager import ModuleManager

# ─── Color Palette ────────────────────────────────────────────────────────────
COLORS = {
    'bg_primary':    '#0A0A0F',
    'bg_secondary':  '#12121A',
    'bg_card':       '#1A1A28',
    'bg_surface':    '#1E1E2E',
    'accent':        '#6C63FF',
    'accent_soft':   '#8B85FF',
    'accent_dim':    '#2A2560',
    'text_primary':  '#EEEEFF',
    'text_secondary':'#8888AA',
    'text_muted':    '#44445A',
    'success':       '#4CAF7D',
    'warning':       '#F0A500',
    'error':         '#FF5572',
    'border':        '#2A2A40',
}

def c(key):
    return get_color_from_hex(COLORS[key])


# ─── KV Language String ───────────────────────────────────────────────────────
KV = """
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp
#:import get_color_from_hex kivy.utils.get_color_from_hex

<RoundedButton@Button>:
    background_color: 0, 0, 0, 0
    background_normal: ''
    canvas.before:
        Color:
            rgba: self.bg_color if not self.state == 'down' else (self.bg_color[0]*0.8, self.bg_color[1]*0.8, self.bg_color[2]*0.8, self.bg_color[3])
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [self.radius_val]
    bg_color: get_color_from_hex('#6C63FF')
    radius_val: dp(12)

<NavBar>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(60)
    canvas.before:
        Color:
            rgba: get_color_from_hex('#12121A')
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: get_color_from_hex('#2A2A40')
        Line:
            points: [self.x, self.top, self.right, self.top]
            width: 1

<CardWidget>:
    size_hint_y: None
    height: dp(200)
    canvas.before:
        Color:
            rgba: get_color_from_hex('#1A1A28')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]

<SearchBar>:
    size_hint_y: None
    height: dp(48)
    background_color: 0, 0, 0, 0
    background_normal: ''
    foreground_color: get_color_from_hex('#EEEEFF')
    hint_text_color: get_color_from_hex('#44445A')
    cursor_color: get_color_from_hex('#6C63FF')
    canvas.before:
        Color:
            rgba: get_color_from_hex('#1E1E2E')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(24)]
        Color:
            rgba: get_color_from_hex('#2A2A40')
        Line:
            rounded_rectangle: [self.x, self.y, self.width, self.height, dp(24)]
            width: 1.2

<ModuleCard>:
    orientation: 'vertical'
    size_hint_y: None
    height: dp(80)
    padding: [dp(16), dp(12)]
    spacing: dp(4)
    canvas.before:
        Color:
            rgba: get_color_from_hex('#1A1A28')
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]
        Color:
            rgba: get_color_from_hex('#2A2A40')
        Line:
            rounded_rectangle: [self.x, self.y, self.width, self.height, dp(12)]
            width: 0.8
"""

Builder.load_string(KV)


# ─── Custom Widgets ───────────────────────────────────────────────────────────

class NavBar(BoxLayout):
    pass

class CardWidget(BoxLayout):
    pass

class SearchBar(TextInput):
    pass

class ModuleCard(BoxLayout):
    pass


class NavButton(Button):
    """Bottom nav tab button with icon + label."""
    
    def __init__(self, icon, label, **kwargs):
        super().__init__(**kwargs)
        self.icon_char = icon
        self.label_text = label
        self.active = False
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ''
        
        layout = BoxLayout(orientation='vertical', spacing=dp(2))
        self.icon_lbl = Label(
            text=icon,
            font_size=sp(22),
            color=c('text_muted'),
            size_hint_y=0.6
        )
        self.text_lbl = Label(
            text=label,
            font_size=sp(10),
            color=c('text_muted'),
            size_hint_y=0.4
        )
        layout.add_widget(self.icon_lbl)
        layout.add_widget(self.text_lbl)
        self.add_widget(layout)

    def set_active(self, active):
        self.active = active
        color = c('accent_soft') if active else c('text_muted')
        self.icon_lbl.color = color
        self.text_lbl.color = color
        with self.canvas.before:
            Color(*c('accent_dim') if active else (0,0,0,0))
            RoundedRectangle(pos=(self.x+dp(8), self.y+dp(4)),
                             size=(self.width-dp(16), self.height-dp(8)),
                             radius=[dp(10)])


class MediaCard(BoxLayout):
    """Movie/Show card with poster + title."""

    def __init__(self, item_data, on_tap=None, **kwargs):
        super().__init__(**kwargs)
        self.item_data = item_data
        self.on_tap_cb = on_tap
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (dp(120), dp(195))
        self.spacing = dp(6)
        
        with self.canvas.before:
            Color(*c('bg_card'))
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
        self.bind(pos=self._update_rect, size=self._update_rect)

        # Poster image
        poster_url = item_data.get('poster', '')
        if poster_url:
            img = AsyncImage(source=poster_url, allow_stretch=True,
                             keep_ratio=False, size_hint_y=0.82)
        else:
            img = Widget(size_hint_y=0.82)
            with img.canvas:
                Color(*c('bg_surface'))
                RoundedRectangle(pos=img.pos, size=img.size, radius=[dp(10)])
        
        title_lbl = Label(
            text=item_data.get('title', 'Unknown'),
            font_size=sp(11),
            color=c('text_secondary'),
            size_hint_y=0.18,
            halign='center',
            valign='middle',
            text_size=(dp(112), None),
            shorten=True,
            shorten_from='right'
        )

        self.add_widget(img)
        self.add_widget(title_lbl)

        btn = Button(size_hint=(1,1), background_color=(0,0,0,0),
                     background_normal='', pos_hint={'center_x':0.5,'center_y':0.5})
        btn.bind(on_press=self._tapped)
        self.add_widget(btn)

    def _update_rect(self, *a):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def _tapped(self, *a):
        if self.on_tap_cb:
            self.on_tap_cb(self.item_data)


class SectionHeader(Label):
    def __init__(self, text, **kwargs):
        super().__init__(
            text=text,
            font_size=sp(16),
            bold=True,
            color=c('text_primary'),
            size_hint_y=None,
            height=dp(36),
            halign='left',
            valign='middle',
            **kwargs
        )
        self.bind(size=lambda *a: setattr(self, 'text_size', (self.width, None)))


# ─── Screens ──────────────────────────────────────────────────────────────────

class HomeScreen(Screen):
    """Library / Recent / Featured content."""

    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app = app_ref
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical')
        with root.canvas.before:
            Color(*c('bg_primary'))
            Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *a: setattr(root.canvas.before.get_group('')[1], 'pos', root.pos),
                  size=lambda *a: setattr(root.canvas.before.get_group('')[1], 'size', root.size))

        # Header
        header = BoxLayout(size_hint_y=None, height=dp(60), padding=[dp(20),dp(10)])
        title = Label(text='[b]SoraPlayer[/b]', markup=True,
                      font_size=sp(22), color=c('accent_soft'),
                      halign='left', valign='middle')
        title.bind(size=lambda *a: setattr(title, 'text_size', title.size))
        header.add_widget(title)

        # Scroll content
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', spacing=dp(16),
                            padding=[dp(16), dp(8), dp(16), dp(16)],
                            size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        # Featured banner
        self.featured_banner = self._make_featured_banner()
        content.add_widget(self.featured_banner)

        # Recently watched
        content.add_widget(SectionHeader(text='Continue Watching'))
        self.recent_row = self._make_card_row([])
        content.add_widget(self.recent_row)

        # Featured from modules
        content.add_widget(SectionHeader(text='Discover'))
        self.discover_row = self._make_card_row([])
        content.add_widget(self.discover_row)

        scroll.add_widget(content)
        root.add_widget(header)
        root.add_widget(scroll)
        self.add_widget(root)
        self.content_layout = content

    def _make_featured_banner(self):
        banner = BoxLayout(size_hint_y=None, height=dp(200))
        with banner.canvas.before:
            Color(*c('bg_surface'))
            RoundedRectangle(pos=banner.pos, size=banner.size, radius=[dp(16)])
        banner.bind(pos=lambda *a: None)

        overlay = BoxLayout(orientation='vertical', padding=[dp(20), dp(16)])
        lbl = Label(text='Install a module to get started',
                    font_size=sp(14), color=c('text_secondary'))
        sub = Label(text='Go to Settings → Add Module',
                    font_size=sp(12), color=c('text_muted'))
        overlay.add_widget(lbl)
        overlay.add_widget(sub)
        banner.add_widget(overlay)
        return banner

    def _make_card_row(self, items):
        row_scroll = ScrollView(size_hint_y=None, height=dp(200),
                                do_scroll_y=False)
        row = BoxLayout(orientation='horizontal', spacing=dp(10),
                        size_hint_x=None, padding=[0,0,0,0])
        row.bind(minimum_width=row.setter('width'))

        if not items:
            placeholder = Label(
                text='No content yet', font_size=sp(13),
                color=c('text_muted'), size=(dp(200), dp(200)),
                size_hint=(None, None)
            )
            row.add_widget(placeholder)
        else:
            for item in items:
                card = MediaCard(item, on_tap=self.app.open_detail)
                row.add_widget(card)

        row_scroll.add_widget(row)
        return row_scroll

    def refresh_recent(self, items):
        self.content_layout.remove_widget(self.recent_row)
        self.recent_row = self._make_card_row(items)
        # Insert at correct position
        idx = self.content_layout.children.index(self.discover_row)
        self.content_layout.add_widget(self.recent_row, index=idx + 1)

    def on_enter(self):
        Clock.schedule_once(self._load_home_content, 0.1)

    def _load_home_content(self, *a):
        history = self.app.get_watch_history()
        if history:
            self.refresh_recent(history)


class SearchScreen(Screen):
    """Global search across all installed modules."""

    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app = app_ref
        self.search_thread = None
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=[dp(16), dp(12), dp(16), dp(8)],
                         spacing=dp(12))
        with root.canvas.before:
            Color(*c('bg_primary'))
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *a: setattr(self._bg, 'pos', root.pos),
                  size=lambda *a: setattr(self._bg, 'size', root.size))

        # Title
        title_row = BoxLayout(size_hint_y=None, height=dp(40))
        title_lbl = Label(text='[b]Search[/b]', markup=True,
                          font_size=sp(20), color=c('text_primary'),
                          halign='left', valign='middle')
        title_lbl.bind(size=lambda *a: setattr(title_lbl, 'text_size', title_lbl.size))
        title_row.add_widget(title_lbl)

        # Search input row
        search_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.search_input = SearchBar(
            hint_text='  Search movies, shows...',
            multiline=False,
            font_size=sp(15),
            padding=[dp(16), dp(12)]
        )
        self.search_input.bind(on_text_validate=self._do_search)

        search_btn = Button(
            text='⌕',
            font_size=sp(20),
            size_hint_x=None,
            width=dp(48),
            background_normal='',
            background_color=(0, 0, 0, 0),
            color=c('accent')
        )
        search_btn.bind(on_press=self._do_search)
        search_row.add_widget(self.search_input)
        search_row.add_widget(search_btn)

        # Status label
        self.status_lbl = Label(
            text='Search across all your modules',
            font_size=sp(13),
            color=c('text_muted'),
            size_hint_y=None,
            height=dp(30)
        )

        # Results
        self.results_scroll = ScrollView()
        self.results_layout = GridLayout(
            cols=3, spacing=dp(10),
            padding=[0, dp(8), 0, dp(16)],
            size_hint_y=None
        )
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))
        self.results_scroll.add_widget(self.results_layout)

        root.add_widget(title_row)
        root.add_widget(search_row)
        root.add_widget(self.status_lbl)
        root.add_widget(self.results_scroll)
        self.add_widget(root)

    def _do_search(self, *a):
        query = self.search_input.text.strip()
        if not query:
            return
        self.results_layout.clear_widgets()
        self.status_lbl.text = f'Searching "{query}"...'
        self.status_lbl.color = c('accent_soft')

        def search_worker():
            results = self.app.module_manager.search_all(query)
            Clock.schedule_once(lambda dt: self._show_results(results, query))

        t = threading.Thread(target=search_worker, daemon=True)
        t.start()

    def _show_results(self, results, query):
        self.results_layout.clear_widgets()
        if not results:
            self.status_lbl.text = f'No results for "{query}"'
            self.status_lbl.color = c('text_muted')
            return

        self.status_lbl.text = f'{len(results)} results for "{query}"'
        self.status_lbl.color = c('success')

        for item in results:
            card = MediaCard(item, on_tap=self.app.open_detail)
            self.results_layout.add_widget(card)


class SettingsScreen(Screen):
    """Module management — add, remove, toggle modules."""

    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app = app_ref
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', padding=[dp(16), dp(12), dp(16), dp(8)],
                         spacing=dp(12))
        with root.canvas.before:
            Color(*c('bg_primary'))
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *a: setattr(self._bg, 'pos', root.pos),
                  size=lambda *a: setattr(self._bg, 'size', root.size))

        # Header
        title = Label(text='[b]Modules[/b]', markup=True,
                      font_size=sp(20), color=c('text_primary'),
                      size_hint_y=None, height=dp(40),
                      halign='left', valign='middle')
        title.bind(size=lambda *a: setattr(title, 'text_size', title.size))

        # Add module section
        add_box = BoxLayout(orientation='vertical', size_hint_y=None,
                            height=dp(140), spacing=dp(8))
        with add_box.canvas.before:
            Color(*c('bg_surface'))
            self._add_bg = RoundedRectangle(pos=add_box.pos, size=add_box.size, radius=[dp(14)])
        add_box.bind(pos=lambda *a: setattr(self._add_bg, 'pos', add_box.pos),
                     size=lambda *a: setattr(self._add_bg, 'size', add_box.size))
        add_box.padding = [dp(16), dp(12)]

        add_lbl = Label(text='Add Module Source', font_size=sp(14),
                        bold=True, color=c('text_primary'),
                        size_hint_y=None, height=dp(28),
                        halign='left', valign='middle')
        add_lbl.bind(size=lambda *a: setattr(add_lbl, 'text_size', add_lbl.size))

        self.url_input = TextInput(
            hint_text='Paste module URL (.py or .js)',
            multiline=False,
            font_size=sp(13),
            background_color=c('bg_card'),
            foreground_color=c('text_primary'),
            hint_text_color=c('text_muted'),
            cursor_color=c('accent'),
            size_hint_y=None, height=dp(42),
            padding=[dp(12), dp(10)]
        )

        install_btn = Button(
            text='Install Module',
            font_size=sp(14),
            size_hint_y=None, height=dp(40),
            background_normal='', background_color=(0,0,0,0),
            color=c('text_primary')
        )
        with install_btn.canvas.before:
            Color(*c('accent'))
            self._btn_bg = RoundedRectangle(pos=install_btn.pos,
                                            size=install_btn.size, radius=[dp(10)])
        install_btn.bind(
            pos=lambda *a: setattr(self._btn_bg, 'pos', install_btn.pos),
            size=lambda *a: setattr(self._btn_bg, 'size', install_btn.size),
            on_press=self._install_module
        )

        add_box.add_widget(add_lbl)
        add_box.add_widget(self.url_input)
        add_box.add_widget(install_btn)

        # Installed modules list
        installed_lbl = Label(text='Installed Modules', font_size=sp(14),
                              bold=True, color=c('text_secondary'),
                              size_hint_y=None, height=dp(32),
                              halign='left', valign='middle')
        installed_lbl.bind(size=lambda *a: setattr(installed_lbl, 'text_size', installed_lbl.size))

        self.modules_scroll = ScrollView()
        self.modules_list = BoxLayout(orientation='vertical', spacing=dp(8),
                                      size_hint_y=None, padding=[0, 0, 0, dp(16)])
        self.modules_list.bind(minimum_height=self.modules_list.setter('height'))
        self.modules_scroll.add_widget(self.modules_list)

        root.add_widget(title)
        root.add_widget(add_box)
        root.add_widget(installed_lbl)
        root.add_widget(self.modules_scroll)
        self.add_widget(root)

    def on_enter(self):
        self.refresh_module_list()

    def refresh_module_list(self):
        self.modules_list.clear_widgets()
        modules = self.app.module_manager.get_installed_modules()

        if not modules:
            empty = Label(text='No modules installed yet',
                          font_size=sp(13), color=c('text_muted'),
                          size_hint_y=None, height=dp(60))
            self.modules_list.add_widget(empty)
            return

        for mod in modules:
            self.modules_list.add_widget(self._make_module_card(mod))

    def _make_module_card(self, mod):
        card = BoxLayout(orientation='vertical', size_hint_y=None,
                         height=dp(80), spacing=dp(4), padding=[dp(14), dp(10)])
        with card.canvas.before:
            Color(*c('bg_card'))
            bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(12)])
        card.bind(pos=lambda *a, b=bg: setattr(b, 'pos', card.pos),
                  size=lambda *a, b=bg: setattr(b, 'size', card.size))

        top_row = BoxLayout(size_hint_y=0.6)
        name_lbl = Label(text=mod.get('name', 'Unknown'), font_size=sp(14),
                         bold=True, color=c('text_primary'),
                         halign='left', valign='middle')
        name_lbl.bind(size=lambda *a: setattr(name_lbl, 'text_size', name_lbl.size))

        status_color = c('success') if mod.get('enabled', True) else c('text_muted')
        status_dot = Label(text='●', font_size=sp(14), color=status_color,
                           size_hint_x=None, width=dp(24))

        del_btn = Button(text='✕', font_size=sp(13), color=c('error'),
                         size_hint_x=None, width=dp(36),
                         background_normal='', background_color=(0,0,0,0))
        del_btn.bind(on_press=lambda *a, m=mod: self._remove_module(m))

        top_row.add_widget(status_dot)
        top_row.add_widget(name_lbl)
        top_row.add_widget(del_btn)

        bot_row = BoxLayout(size_hint_y=0.4)
        version = mod.get('version', 'v1.0')
        lang = mod.get('lang', 'py').upper()
        info_lbl = Label(text=f'{lang} • {version} • {mod.get("type", "scraper")}',
                         font_size=sp(11), color=c('text_muted'),
                         halign='left', valign='middle')
        info_lbl.bind(size=lambda *a: setattr(info_lbl, 'text_size', info_lbl.size))
        bot_row.add_widget(info_lbl)

        card.add_widget(top_row)
        card.add_widget(bot_row)
        return card

    def _install_module(self, *a):
        url = self.url_input.text.strip()
        if not url:
            self._show_toast('Please enter a module URL')
            return
        self._show_toast('Installing...')

        def worker():
            result = self.app.module_manager.install_from_url(url)
            Clock.schedule_once(lambda dt: self._on_install_done(result))

        threading.Thread(target=worker, daemon=True).start()

    def _on_install_done(self, result):
        if result['success']:
            self._show_toast(f'Installed: {result["name"]}')
            self.url_input.text = ''
            self.refresh_module_list()
        else:
            self._show_toast(f'Error: {result["error"]}')

    def _remove_module(self, mod):
        self.app.module_manager.remove_module(mod['id'])
        self.refresh_module_list()

    def _show_toast(self, msg):
        popup = Popup(
            title='', content=Label(text=msg, color=c('text_primary')),
            size_hint=(0.7, None), height=dp(80),
            background='', background_color=(*c('bg_surface')[:3], 0.95),
            separator_height=0
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2.0)


class PlayerScreen(Screen):
    """Full-screen video player with controls."""

    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app = app_ref
        self.current_item = None
        self._build_ui()

    def _build_ui(self):
        self.layout = BoxLayout(orientation='vertical')
        with self.layout.canvas.before:
            Color(0, 0, 0, 1)
            self._bg = Rectangle(pos=self.layout.pos, size=self.layout.size)
        self.layout.bind(pos=lambda *a: setattr(self._bg, 'pos', self.layout.pos),
                         size=lambda *a: setattr(self._bg, 'size', self.layout.size))

        # Back button
        top_bar = BoxLayout(size_hint_y=None, height=dp(50), padding=[dp(8), dp(8)])
        back_btn = Button(text='← Back', font_size=sp(14),
                          color=c('text_primary'), size_hint_x=None, width=dp(80),
                          background_normal='', background_color=(0,0,0,0))
        back_btn.bind(on_press=lambda *a: self.app.go_back())
        self.title_lbl = Label(text='', font_size=sp(15),
                               color=c('text_primary'), bold=True)
        top_bar.add_widget(back_btn)
        top_bar.add_widget(self.title_lbl)

        # Video widget placeholder
        self.video_container = BoxLayout(size_hint_y=0.85)
        self.placeholder = Label(
            text='Loading video...',
            font_size=sp(16), color=c('text_secondary')
        )
        self.video_container.add_widget(self.placeholder)

        self.layout.add_widget(top_bar)
        self.layout.add_widget(self.video_container)
        self.add_widget(self.layout)

    def play(self, item_data, video_url):
        self.current_item = item_data
        self.title_lbl.text = item_data.get('title', '')
        self.video_container.clear_widgets()

        try:
            video = Video(
                source=video_url,
                state='play',
                allow_stretch=True,
                options={'eos': 'loop'}
            )
            self.video_container.add_widget(video)
        except Exception as e:
            err_lbl = Label(
                text=f'Player error:\n{e}\n\nURL: {video_url[:60]}...',
                font_size=sp(13), color=c('error'),
                halign='center'
            )
            self.video_container.add_widget(err_lbl)


class DetailScreen(Screen):
    """Show/Movie detail: synopsis, episode list, watch button."""

    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app = app_ref
        self.current_item = None
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation='vertical')
        with root.canvas.before:
            Color(*c('bg_primary'))
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *a: setattr(self._bg, 'pos', root.pos),
                  size=lambda *a: setattr(self._bg, 'size', root.size))

        # Top bar
        top_bar = BoxLayout(size_hint_y=None, height=dp(52), padding=[dp(8)])
        back_btn = Button(text='← Back', font_size=sp(14),
                          color=c('accent_soft'), size_hint_x=None, width=dp(80),
                          background_normal='', background_color=(0,0,0,0))
        back_btn.bind(on_press=lambda *a: self.app.go_back())
        top_bar.add_widget(back_btn)

        # Scroll content
        scroll = ScrollView()
        self.content = BoxLayout(orientation='vertical', spacing=dp(12),
                                 padding=[dp(16), dp(8), dp(16), dp(80)],
                                 size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter('height'))
        scroll.add_widget(self.content)

        root.add_widget(top_bar)
        root.add_widget(scroll)
        self.add_widget(root)

    def load_item(self, item_data):
        self.current_item = item_data
        self.content.clear_widgets()

        # Banner image
        poster_url = item_data.get('poster', '')
        if poster_url:
            banner = AsyncImage(source=poster_url, allow_stretch=True,
                                keep_ratio=True, size_hint_y=None, height=dp(240))
            self.content.add_widget(banner)

        # Title
        title = Label(text=item_data.get('title', 'Unknown'),
                      font_size=sp(22), bold=True, color=c('text_primary'),
                      size_hint_y=None, height=dp(40),
                      halign='left', valign='middle')
        title.bind(size=lambda *a: setattr(title, 'text_size', title.size))

        # Meta row
        meta_row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
        for tag in [item_data.get('year',''), item_data.get('type',''), item_data.get('source_module','')]:
            if tag:
                chip = Label(text=tag, font_size=sp(11), color=c('accent_soft'),
                             size_hint_x=None, width=dp(80))
                meta_row.add_widget(chip)

        # Description
        desc = Label(
            text=item_data.get('description', 'No description available.'),
            font_size=sp(13), color=c('text_secondary'),
            size_hint_y=None, halign='left', valign='top'
        )
        desc.bind(width=lambda *a: setattr(desc, 'text_size', (desc.width, None)))
        desc.bind(texture_size=lambda *a: setattr(desc, 'height', desc.texture_size[1] + dp(16)))

        # Watch button
        watch_btn = Button(
            text='▶  Watch Now',
            font_size=sp(15), bold=True,
            color=c('text_primary'),
            size_hint_y=None, height=dp(52),
            background_normal='', background_color=(0,0,0,0)
        )
        with watch_btn.canvas.before:
            Color(*c('accent'))
            btn_bg = RoundedRectangle(pos=watch_btn.pos, size=watch_btn.size, radius=[dp(14)])
        watch_btn.bind(
            pos=lambda *a, b=btn_bg: setattr(b, 'pos', watch_btn.pos),
            size=lambda *a, b=btn_bg: setattr(b, 'size', watch_btn.size),
            on_press=lambda *a: self._fetch_and_play()
        )

        self.content.add_widget(title)
        self.content.add_widget(meta_row)
        self.content.add_widget(desc)
        self.content.add_widget(watch_btn)

        # Episodes (if series)
        if item_data.get('episodes'):
            ep_lbl = Label(text='Episodes', font_size=sp(15), bold=True,
                           color=c('text_primary'), size_hint_y=None, height=dp(36),
                           halign='left', valign='middle')
            ep_lbl.bind(size=lambda *a: setattr(ep_lbl, 'text_size', ep_lbl.size))
            self.content.add_widget(ep_lbl)

            for ep in item_data['episodes']:
                ep_btn = Button(
                    text=f'  Ep {ep.get("number","?")} — {ep.get("title","")}',
                    font_size=sp(13), color=c('text_secondary'),
                    size_hint_y=None, height=dp(44),
                    halign='left',
                    background_normal='', background_color=(0,0,0,0)
                )
                self.content.add_widget(ep_btn)

    def _fetch_and_play(self):
        if not self.current_item:
            return
        item = self.current_item
        
        def worker():
            links = self.app.module_manager.get_links(item)
            if links:
                Clock.schedule_once(
                    lambda dt: self.app.play_video(item, links[0]['url'])
                )
            else:
                Clock.schedule_once(
                    lambda dt: self._show_no_links_error()
                )

        threading.Thread(target=worker, daemon=True).start()

    def _show_no_links_error(self):
        popup = Popup(
            title='No Links Found',
            content=Label(text='This module returned no playable links.',
                          color=c('text_secondary')),
            size_hint=(0.8, None), height=dp(140)
        )
        popup.open()


# ─── Main App ─────────────────────────────────────────────────────────────────

class SoraPlayerApp(App):
    
    def build(self):
        Window.clearcolor = c('bg_primary')
        self.title = 'SoraPlayer'
        
        # Initialize module manager
        modules_dir = os.path.join(os.path.dirname(__file__), 'Modules')
        os.makedirs(modules_dir, exist_ok=True)
        self.module_manager = ModuleManager(modules_dir)
        
        # Watch history (in-memory + persisted to JSON)
        self.watch_history = []
        self._load_history()

        # Root layout: screens + navbar
        self.root_layout = BoxLayout(orientation='vertical')

        # Screen manager
        self.sm = ScreenManager(transition=FadeTransition(duration=0.15))
        self.home_screen    = HomeScreen(app_ref=self, name='home')
        self.search_screen  = SearchScreen(app_ref=self, name='search')
        self.settings_screen = SettingsScreen(app_ref=self, name='settings')
        self.detail_screen  = DetailScreen(app_ref=self, name='detail')
        self.player_screen  = PlayerScreen(app_ref=self, name='player')

        for s in [self.home_screen, self.search_screen, self.settings_screen,
                  self.detail_screen, self.player_screen]:
            self.sm.add_widget(s)

        # Navigation bar
        self.navbar = self._build_navbar()
        self.root_layout.add_widget(self.sm)
        self.root_layout.add_widget(self.navbar)

        return self.root_layout

    def _build_navbar(self):
        bar = NavBar()
        self.nav_home_btn     = NavButton('⌂', 'Home')
        self.nav_search_btn   = NavButton('⌕', 'Search')
        self.nav_settings_btn = NavButton('⚙', 'Settings')

        self.nav_home_btn.bind(on_press=lambda *a: self.nav_to('home'))
        self.nav_search_btn.bind(on_press=lambda *a: self.nav_to('search'))
        self.nav_settings_btn.bind(on_press=lambda *a: self.nav_to('settings'))

        bar.add_widget(self.nav_home_btn)
        bar.add_widget(self.nav_search_btn)
        bar.add_widget(self.nav_settings_btn)

        self.nav_home_btn.set_active(True)
        self._nav_btns = {
            'home': self.nav_home_btn,
            'search': self.nav_search_btn,
            'settings': self.nav_settings_btn
        }
        return bar

    def nav_to(self, screen_name):
        self.navbar.opacity = 1
        self.sm.current = screen_name
        for k, btn in self._nav_btns.items():
            btn.set_active(k == screen_name)

    def open_detail(self, item_data):
        """Navigate to detail screen for an item."""
        self.navbar.opacity = 1
        self.detail_screen.load_item(item_data)
        self.sm.current = 'detail'

    def play_video(self, item_data, url):
        """Navigate to player and start playback."""
        self.navbar.opacity = 0
        self.player_screen.play(item_data, url)
        self.sm.current = 'player'
        self._add_to_history(item_data)

    def go_back(self):
        prev = self.sm.current
        if prev in ('detail', 'player'):
            self.navbar.opacity = 1
            self.sm.current = 'home'
            self.nav_to('home')

    def get_watch_history(self):
        return self.watch_history[:12]

    def _add_to_history(self, item):
        self.watch_history = [i for i in self.watch_history
                              if i.get('id') != item.get('id')]
        self.watch_history.insert(0, item)
        self._save_history()

    def _load_history(self):
        path = os.path.join(os.path.dirname(__file__), 'history.json')
        if os.path.exists(path):
            try:
                with open(path) as f:
                    self.watch_history = json.load(f)
            except Exception:
                self.watch_history = []

    def _save_history(self):
        path = os.path.join(os.path.dirname(__file__), 'history.json')
        try:
            with open(path, 'w') as f:
                json.dump(self.watch_history[:50], f)
        except Exception:
            pass


if __name__ == '__main__':
    SoraPlayerApp().run()
