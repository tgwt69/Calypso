[app]

# ── Identity ──────────────────────────────────────────────────────────────────
title = SoraPlayer
package.name = soraplayer
package.domain = org.soraplayer
version = 1.0.0
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,js
source.include_patterns = Modules/*.py,Modules/*.js,Modules/manifest.json

# ── Requirements ──────────────────────────────────────────────────────────────
# Core
requirements = python3==3.11.6,kivy==2.3.0,kivymd

# Networking & scraping
requirements += ,requests,certifi,urllib3,charset-normalizer,idna
requirements += ,beautifulsoup4,soupsieve,lxml

# JS interpreter (Sora/Luna module compatibility)
requirements += ,js2py

# Android integration
requirements += ,pyjnius

# Utilities
requirements += ,pillow,zope.event,zope.interface

# ── Android Platform ──────────────────────────────────────────────────────────
[buildozer]
log_level = 2
warn_on_root = 1

[app:android]
android.minapi     = 24
android.ndk        = 25b
android.sdk        = 33
android.archs      = arm64-v8a, armeabi-v7a

# Permissions
android.permissions = \
    INTERNET, \
    READ_EXTERNAL_STORAGE, \
    WRITE_EXTERNAL_STORAGE, \
    ACCESS_NETWORK_STATE, \
    FOREGROUND_SERVICE, \
    WAKE_LOCK, \
    RECEIVE_BOOT_COMPLETED

# Allow cleartext traffic (needed for some HTTP module sources)
android.usesCleartextTraffic = true

# Hardware acceleration for video playback
android.manifest.xmlns_tools = true
android.manifest.uses_feature = android.hardware.type.watch;required=false

# Activity flags
android.activity_class_name = org.kivy.android.PythonActivity
android.extra_manifest_xml = \
    <uses-feature android:name="android.software.leanback" android:required="false" /> \
    <uses-feature android:name="android.hardware.touchscreen" android:required="false" />

# PiP support (Picture-in-Picture)
# Add android:supportsPictureInPicture="true" to activity in manifest
android.extra_manifest_application_arguments = \
    android:supportsPictureInPicture="true" \
    android:configChanges="screenSize|smallestScreenSize|screenLayout|orientation"

# ── App Metadata ──────────────────────────────────────────────────────────────
android.wakelock      = false
android.allow_backup  = false

# Orientation
orientation = portrait

# Splash screen
presplash.filename  = %(source.dir)s/assets/presplash.png
icon.filename       = %(source.dir)s/assets/icon.png

# Services (for background module updates)
# android.services = ModuleUpdater:service_module_updater.py

# ── iOS (stub) ────────────────────────────────────────────────────────────────
[app:ios]
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.10.0
