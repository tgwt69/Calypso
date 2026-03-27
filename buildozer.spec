[app]
# ── Identity ──────────────────────────────────────────────────
title = Calypso
package.name = calypso
package.domain = org.tgwt69
version = 1.0.0
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,js
source.include_patterns = modules/*.py,modules/*.js,modules/*.json

# ── Requirements ──────────────────────────────────────────────
# All in one clean line to avoid duplicate errors
requirements = python3,kivy==2.3.0,kivymd,requests,certifi,urllib3,charset-normalizer,idna,beautifulsoup4,soupsieve,pyjnius,pillow,zope.event,zope.interface,js2py,six

# ── Android Configuration ─────────────────────────────────────
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE
android.api = 33
android.minapi = 24
android.ndk = 25c
android.hwaccel = True
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = False
orientation = portrait
android.uses_cleartext_traffic = True

[buildozer]
log_level = 2
warn_on_root = 1
