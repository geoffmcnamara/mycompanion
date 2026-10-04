#!/usr/bin/env python3
"""
=======================
     mycompanion.py
=======================
Usage:
    mycompanion.py [--ai] [--log] [--debug] [--toggle]
    mycompanion.py (-h | --help)

Options:
    -h --help   Show help and storage paths.
    --ai        Start with AI bar open.
    -l --log    Log stdout/stderr to mycompanion.log.
    --toggle    Opt-in TSR background mode (X11 only, supports Ctrl+Space).
    -d --debug  Enable debug output and run in foreground.

Shortcuts:
    Ctrl-Space  Toggle window visibility
    Ctrl-1..4   Switch tabs (1:Notes, 2:Calc, 3:Cal, 4:Todo)
    Ctrl-a      Toggle AI bar
    Alt-c       View config file
    Ctrl-e      Edit file if using configured [Settings] editor
    Ctrl-r      Run command dialog
    Ctrl-t      Open Theme Selector
    Ctrl-h / ?  Show Shortcuts & Help
    Ctrl-s      Save selected text as file
    Ctrl-q      Quit application

Link Formatting:
    https://...                   Blue   -> Open in web browser
    [Label](file:///path/to/file) Green  -> Open in sub-window editor (creates if missing)

Setup Gemini AI (optional):
    export GEMINI_API_KEY="AIzaSy..."
"""

import os
import sys
import json
import configparser
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import subprocess
import calendar
import datetime
import threading
import traceback
from pathlib import Path
from docopt import docopt
import re
import webbrowser
import tempfile
import shlex
import math


ROOTNAME = "mycompanion"
TITLE = "MyCompanion"
VERSION = "0.6.1"
DEBUG = False
# DEBUG = True  # uncomment this to initiate debugging
if DEBUG:
    import inspect



if sys.platform == "darwin":
    DATA_DIR = Path.home() / "Library" / "Application Support" / ROOTNAME
    STATE_DIR = DATA_DIR
elif sys.platform == "win32":
    appdata = os.environ.get("APPDATA")
    DATA_DIR = (Path(appdata) / ROOTNAME) if appdata else (Path.home() / "AppData" / "Local" / ROOTNAME)
    STATE_DIR = DATA_DIR
else:
    xdg_data = os.environ.get("XDG_DATA_HOME")
    DATA_DIR = (Path(xdg_data) / ROOTNAME) if xdg_data and Path(xdg_data).is_absolute() else (Path.home() / ".config" / ROOTNAME)
    xdg_state = os.environ.get("XDG_STATE_HOME")
    STATE_DIR = (Path(xdg_state) / ROOTNAME) if xdg_state and Path(xdg_state).is_absolute() else (Path.home() / ".config" / ROOTNAME)

DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

NOTES_FILE = DATA_DIR / f"{ROOTNAME}_notes.txt"
CAL_NOTES_FILE = DATA_DIR / f"{ROOTNAME}_cal_notes.txt"
CALC_NOTES_FILE = DATA_DIR / f"{ROOTNAME}_calc_notes.txt"
TODO_FILE = DATA_DIR / f"{ROOTNAME}_todo.txt"
CONFIG_FILE = STATE_DIR / f"{ROOTNAME}.conf"
LOCK_FILE = STATE_DIR / f"{ROOTNAME}.lock"
LOG_FILE = DATA_DIR / f"{ROOTNAME}.log"

THEMES = {
    "Cyan / Black": {
        "bg": "#00ffff", "fg": "#000000", "header_bg": "#00cccc",
        "nav_bg": "#00e6e6", "panel_bg": "#00e6e6", "btn_bg": "#00b3b3",
        "btn_fg": "#000000", "insert_bg": "#000000"
    },
    "Dark / White (Default)": {
        "bg": "#1e1e1e", "fg": "#d4d4d4", "header_bg": "#1a1a1a",
        "nav_bg": "#2d2d2d", "panel_bg": "#2d2d2d", "btn_bg": "#333333",
        "btn_fg": "#ffffff", "insert_bg": "#ffffff"
    },
    "Classic Matrix": {
        "bg": "#000000", "fg": "#00ff00", "header_bg": "#051505",
        "nav_bg": "#0a220a", "panel_bg": "#0a220a", "btn_bg": "#143d14",
        "btn_fg": "#00ff00", "insert_bg": "#00ff00"
    },
    "VT220 Green Phosphor": {
        "bg": "#121812",        # Dark CRT glass tint (slight green tint in off pixels)
        "fg": "#40ff40",        # Softer phosphor bloom
        "header_bg": "#0a0f0a",
        "nav_bg": "#182218",
        "panel_bg": "#182218",
        "btn_bg": "#243524",
        "btn_fg": "#75ff75",    # Slightly brighter green for highlighted text/buttons
        "insert_bg": "#40ff40"
    },
    "IBM 3270 Amber": {
        "bg": "#100a00",        # Dark amber-tinted background
        "fg": "#ffb000",        # Classic warm monochrome amber
        "header_bg": "#0a0600",
        "nav_bg": "#1f1400",
        "panel_bg": "#1f1400",
        "btn_bg": "#382400",
        "btn_fg": "#ffd066",
        "insert_bg": "#ffb000"
    },
    "Solarized Light": {
        "bg": "#fdf6e3", "fg": "#657b83", "header_bg": "#eee8d5",
        "nav_bg": "#e0d8c3", "panel_bg": "#eee8d5", "btn_bg": "#d3c7a1",
        "btn_fg": "#073642", "insert_bg": "#073642"
    },
    "Nord Dark": {
        "bg": "#2e3440", "fg": "#eceff4", "header_bg": "#242933",
        "nav_bg": "#3b4252", "panel_bg": "#3b4252", "btn_bg": "#4c566a",
        "btn_fg": "#88c0d0", "insert_bg": "#88c0d0"
    },
    "Gruvbox Dark": {
        "bg": "#282828", "fg": "#ebdbb2", "header_bg": "#1d2021",
        "nav_bg": "#3c3836", "panel_bg": "#3c3836", "btn_bg": "#504945",
        "btn_fg": "#fabd2f", "insert_bg": "#fe8019"
    },
    "Dracula": {
        "bg": "#282a36", "fg": "#f8f8f2", "header_bg": "#21222c",
        "nav_bg": "#44475a", "panel_bg": "#44475a", "btn_bg": "#6272a4",
        "btn_fg": "#ff79c6", "insert_bg": "#50fa7b"
    },
    "Monokai": {
        "bg": "#272822", "fg": "#f8f8f2", "header_bg": "#1e1f1c",
        "nav_bg": "#3e3d32", "panel_bg": "#3e3d32", "btn_bg": "#75715e",
        "btn_fg": "#a6e22e", "insert_bg": "#f92672"
    },
    "Oceanic Next": {
        "bg": "#1b2b34", "fg": "#d8dee9", "header_bg": "#16222a",
        "nav_bg": "#343d46", "panel_bg": "#343d46", "btn_bg": "#4f5b66",
        "btn_fg": "#6699cc", "insert_bg": "#ec5f67"
    },
    "Catppuccin Mocha": {
        "bg": "#1e1e2e", "fg": "#cdd6f4", "header_bg": "#181825",
        "nav_bg": "#313244", "panel_bg": "#313244", "btn_bg": "#45475a",
        "btn_fg": "#89b4fa", "insert_bg": "#f5e0dc"
    },
    "Tokyo Night": {
        "bg": "#1a1b26", "fg": "#a9b1d6", "header_bg": "#16161e",
        "nav_bg": "#24283b", "panel_bg": "#24283b", "btn_bg": "#414868",
        "btn_fg": "#7aa2f7", "insert_bg": "#f7768e"
    },
    "One Dark Pro": {
        "bg": "#282c34", "fg": "#abb2bf", "header_bg": "#21252b",
        "nav_bg": "#3e4451", "panel_bg": "#3e4451", "btn_bg": "#4b5263",
        "btn_fg": "#61afef", "insert_bg": "#98c379"
    },
    "Rose Pine Dark": {
        "bg": "#191724", "fg": "#e0def4", "header_bg": "#110f19",
        "nav_bg": "#26233a", "panel_bg": "#26233a", "btn_bg": "#403d52",
        "btn_fg": "#c4a7e7", "insert_bg": "#ebbcba"
    },
    "Synthwave '84": {
        "bg": "#262335", "fg": "#36f9f6", "header_bg": "#1a1826",
        "nav_bg": "#34294f", "panel_bg": "#34294f", "btn_bg": "#493566",
        "btn_fg": "#fe4450", "insert_bg": "#fede5d"
    },
    "Cyberpunk Neon": {
        "bg": "#0d0f18", "fg": "#00f0ff", "header_bg": "#05060a",
        "nav_bg": "#1a1c2e", "panel_bg": "#1a1c2e", "btn_bg": "#2a2d4a",
        "btn_fg": "#ff0055", "insert_bg": "#ffe600"
    },
    "Everforest Dark": {
        "bg": "#2d353b", "fg": "#d3c6aa", "header_bg": "#232a2e",
        "nav_bg": "#3d484d", "panel_bg": "#3d484d", "btn_bg": "#475258",
        "btn_fg": "#a7c080", "insert_bg": "#e67e80"
    },
    "Gruvbox Light": {
        "bg": "#fbf1c7", "fg": "#3c3836", "header_bg": "#f2e5bc",
        "nav_bg": "#ebdbb2", "panel_bg": "#ebdbb2", "btn_bg": "#d5c4a1",
        "btn_fg": "#b57614", "insert_bg": "#9d0006"
    },
    "PaperColor Light": {
        "bg": "#eeeeee", "fg": "#444444", "header_bg": "#e4e4e4",
        "nav_bg": "#d0d0d0", "panel_bg": "#d0d0d0", "btn_bg": "#bcbcbc",
        "btn_fg": "#005f87", "insert_bg": "#d7005f"
    },
}

DEFAULT_CONFIG = {
    "Window": {"geometry": "640x500"},
    "Settings": {"ai_mode": "false", "editor": "", "md_editor": " "},
    "Theme": {"name": "Dark / White (Default)"}
}

# ==============================================================================
# Symbol Menu Configuration Data
# ==============================================================================

SYMBOL_MENU_CONFIG = {
    "Checkboxes": [
        {"label": "[✓] Completed Task", "symbol": "[✓] "},
        {"label": "[✘] Eliminated Box", "symbol": "[✘] "},
        {"label": "[ ] Open Task Box", "symbol": "[ ] "},
    ],
    "Status, Time, & Scheduling": [
        # Status
        {"label": "🟢 Green Spot (Done)", "symbol": "🟢 "},
        {"label": "🔴 Red Spot (Blocked)", "symbol": "🔴 "},
        {"label": "🟡 Yellow Spot (In Progress)", "symbol": "🟡 "},
        {"label": "🔍 Inspect / Investigate", "symbol": "🔍"},
        {"label": "🤔 Thinking / Query", "symbol": "🤔"},
        {"label": "⌛ Pending / Wait", "symbol": "⌛"},
        {"label": "⏳ In Progress", "symbol": "⏳"},
        {"label": "⌛ Hourglass (Done)", "symbol": "⌛"},
        {"label": "🔁 Repeat", "symbol": "🔁"},
        {"label": "📌 Pinned / Important", "symbol": "📌 "},
        {"label": "💡 Idea / Insight", "symbol": "💡 "},
        {"label": "⚠️ Warning", "symbol": "⚠️ "},
        {"label": "❓ Red Question Mark", "symbol": "❓ "},
        {"label": "❔ White Question Mark", "symbol": "❔ "},
        {"label": "⏰ Alarm Clock", "symbol": "⏰ "},
        {"label": "⏱️ Stopwatch / Timer", "symbol": "⏱️ "},
        {"label": "⏲️ Kitchen Timer", "symbol": "⏲️ "},
        {"label": "🕰️ Mantel / Shelf Clock", "symbol": "🕰️ "},
        {"label": "🕒 3:00 / Clock Face", "symbol": "🕒 "},
        {"label": "🕕 6:00 / Clock Face", "symbol": "🕕 "},
        {"label": "🕘 9:00 / Clock Face", "symbol": "🕘 "},
        {"label": "🕛 12:00 / Noon-Midnight", "symbol": "🕛 "},
        {"label": "🔄 Loop / Recurring", "symbol": "🔄 "},
        {"label": "📅 Calendar (Monthly)", "symbol": "📅 "},
        {"label": "📆 Tear-off Calendar", "symbol": "📆 "},
        {"label": "🗓️ Spiral Calendar", "symbol": "🗓️ "},
    ],
    "Bank & Markets": [
        {"label": "🐂 Bull Market (Wall St)", "symbol": "🐂 "},
        {"label": "🐻 Bear Market", "symbol": "🐻 "},
        {"label": "🏦 Bank Building", "symbol": "🏦 "},
        {"label": "🏛️ Treasury / Institution", "symbol": "🏛️ "},
        {"label": "📊 Market Analysis / Chart", "symbol": "📊 "},
        {"label": "💰 Dividend / Cash Flow", "symbol": "💰 "},
    ],
    "Construction & Tools": [
        {"label": "🏗️ Under Construction", "symbol": "🏗️ "},
        {"label": "🔨 Build / Carpentry", "symbol": "🔨 "},
        {"label": "🪛 Assembly / Hardware", "symbol": "🪛 "},
        {"label": "🔧 Repair / Plumbing", "symbol": "🔧 "},
        {"label": "🪚 Framing / Woodwork", "symbol": "🪚 "},
        {"label": "🧱 Masonry / Bricks", "symbol": "🧱 "},
        {"label": "📐 Layout / Measurement", "symbol": "📐 "},
        {"label": "🚧 Caution / Work Zone", "symbol": "🚧 "},
    ],
    "Coastal & Weather": [
        {"label": "☀️ Sunny / Clear", "symbol": "☀️ "},
        {"label": "🌧️ Rain / Storm", "symbol": "🌧️ "},
        {"label": "⛵ Sailboat", "symbol": "⛵ "},
        {"label": "⚓ Anchor", "symbol": "⚓ "},
        {"label": "🧭 Compass", "symbol": "🧭 "},
    ],
    "Misc Symbols" : [
        {"label": "🛂 Passport", "symbol": "🛂 "},
        {"label": "  Notes", "symbol": "  "},
        {"label": "  Quote", "symbol": "  "},
        {"label": "  Flag", "symbol": "  "},
        {"label": "  Book", "symbol": "  "},
        {"label": "📔 Notebook", "symbol": "📔 "},
        {"label": "🎇 Sparkler", "symbol": "🎇 "},
        {"label": "🎉 Party popper", "symbol": "🎉 "},
        {"label": "✨ Sparkles", "symbol": "✨ "},
        {"label": "🥳 Party Face", "symbol": "🥳 "},
        ],
    "Navigation Symbols": [
        {"label": "🧭 Compass", "symbol": "🧭 "},
        {"label": "🗺️ World Map", "symbol": "🗺️ "},
        {"label": "📍 Location Pin", "symbol": "📍 "},
        {"label": "📌 Pinned Spot", "symbol": "📌 "},
        {"label": "🚩 Destination Flag", "symbol": "🚩 "},
        {"label": "🛣️ Highway / Road", "symbol": "🛣️ "},
        {"label": "⬆️ Up Arrow", "symbol": "⬆️ "},
        {"label": "⬇️ Down Arrow", "symbol": "⬇️ "},
        {"label": "⬅️ Left Arrow", "symbol": "⬅️ "},
        {"label": "➡️ Right Arrow", "symbol": "➡️ "},
        {"label": "↗️ Northeast Arrow", "symbol": "↗️ "},
        {"label": "↘️ Southeast Arrow", "symbol": "↘️ "},
        {"label": "🔄 Return / Loop", "symbol": "🔄 "},
        {"label": "↑ Simple Up", "symbol": "↑ "},
        {"label": "↓ Simple Down", "symbol": "↓ "},
        {"label": "← Simple Left", "symbol": "← "},
        {"label": "→ Simple Right", "symbol": "→ "},
        {"label": "➔ Heavy Right", "symbol": "➔ "},
        {"label": "↔ Two-Way Arrow", "symbol": "↔ "},
        ],
    "Sports" : [
        {"label": "⚽ Soccer", "symbol": "⚽ "},
        {"label": "🏈 Football", "symbol": "🏈 "},
        {"label": "⚾ Baseball", "symbol": "⚾ "},
        {"label": "🏀 Basketball", "symbol": "🏀 "},
        {"label": "🎾 Tennis", "symbol": "🎾 "},
        {"label": "⛳ Golf", "symbol": "⛳ "},
        {"label": "⛵ Sailing", "symbol": "⛵ "},
        {"label": "🏆 Trophy", "symbol": "🏆 "},
        {"label": "  Fitness", "symbol": "  "}
        ],
    "Travel" : [
        {"label": "✈️ Airplane", "symbol": "✈️ "},
        {"label": "🚂 Train", "symbol": "🚂 "},
        {"label": "🚇 Subway", "symbol": "🚇 "},
        {"label": "🚗 Car", "symbol": "🚗 "},
        {"label": "🚙 SUV", "symbol": "🚙 "},
        {"label": "🚚 Truck", "symbol": "🚚 "},
        {"label": "🚲 Bicycle", "symbol": "🚲 "},
        {"label": "🚌 Bus", "symbol": "🚌 "},
        {"label": "🚢 Ship", "symbol": "🚢 "},
        {"label": "⚓ Anchor", "symbol": "⚓ "}
        ],
    "Devices" : [
        {"label": "🖥️ Server", "symbol": "🖥️ "},
        {"label": "🗄️ Rack / Mainframe", "symbol": "🗄️ "},
        {"label": "💾 Database / Storage", "symbol": "💾 "},
        {"label": "☁️ Cloud", "symbol": "☁️ "},
        {"label": "📱 Phone", "symbol": "📱 "},
        {"label": "📱 Tablet", "symbol": "📱 "},
        {"label": "💻 Laptop", "symbol": "💻 "},
        {"label": "🖥️ Desktop", "symbol": "🖥️ "},
        {"label": "📺 Display / Monitor", "symbol": "📺 "},
        {"label": "⌚ Smartwatch", "symbol": "⌚ "},
        {"label": "📶 Wi-Fi", "symbol": "📶 "},
        {"label": "📡 Router / Antenna", "symbol": "📡 "},
        {"label": "🔌 Ethernet / Plug", "symbol": "🔌 "},
        {"label": "📟 Modem / Pager", "symbol": "📟 "},
        {"label": "🌐 Network / Web", "symbol": "🌐 "},
        {"label": "ᛒ Bluetooth", "symbol": "ᛒ "},
        {"label": "🛰️ Satellite", "symbol": "🛰️ "},
        {"label": "🌡️ Temperature Sensor", "symbol": "🌡️ "},
        {"label": "🔋 Battery", "symbol": "🔋 "},
        {"label": "💡 Smart Light", "symbol": "💡 "},
        {"label": "🔒 Smart Lock", "symbol": "🔒 "},
        {"label": "📹 Security Camera", "symbol": "📹 "},
        {"label": "🎛️ Switch / Controller", "symbol": "🎛️ "},
        {"label": "🎧 Headphones", "symbol": "🎧 "},
        {"label": "🔊 Speaker", "symbol": "🔊 "},
        {"label": "🖨️ Printer", "symbol": "🖨️ "}
    ],
    "Medical & Laboratory": [
        {"label": "🧪 Test Tube / Sample", "symbol": "🧪 "},
        {"label": "🔬 Microscope / Lab", "symbol": "🔬 "},
        {"label": "⚗️  Alembic Distillation", "symbol": "⚗️ "},
        {"label": "🧫 Petri Dish / Culture", "symbol": "🧫 "},
        {"label": "🥼 Lab Coat", "symbol": "🥼 "},
        {"label": "💉 Syringe / Injection", "symbol": "💉 "},
        {"label": "🩹 Bandage / First Aid", "symbol": "🩹 "},
        {"label": "🩺 Stethoscope", "symbol": "🩺 "},
        {"label": "💊 Pill / Medication", "symbol": "💊 "},
        {"label": "🩸 Blood Drop", "symbol": "🩸 "},
        {"label": "🏥 Hospital / Clinic", "symbol": "🏥 "},
        {"label": "🚑 Ambulance", "symbol": "🚑 "},
        {"label": "⚕️ Medical Symbol", "symbol": "⚕️ "},
        {"label": "🧬 DNA / Genetics", "symbol": "🧬 "},
    ],
    "Figures & Clothing": [
        {"label": "👤 Person / User", "symbol": "👤 "},
        {"label": "👥 Group / Team", "symbol": "👥 "},
        {"label": "👨 Male Figure", "symbol": "👨 "},
        {"label": "👩 Female Figure", "symbol": "👩 "},
        {"label": "🚶 Walking Figure", "symbol": "🚶 "},
        {"label": "👔 Dress Shirt / Tie", "symbol": "👔 "},
        {"label": "👕 T-Shirt / Casual", "symbol": "👕 "},
        {"label": "🧥 Jacket / Outerwear", "symbol": "🧥 "},
        {"label": "👖 Pants / Jeans", "symbol": "👖 "},
        {"label": "👗 Dress / Outfit", "symbol": "👗 "},
        {"label": "🧢 Cap / Hat", "symbol": "🧢 "},
        {"label": "👞 Shoe / Footwear", "symbol": "👞 "},
        {"label": "👓 Glasses / Eyewear", "symbol": "👓 "},
    ],
    "Professions & Roles": [
        {"label": "👨‍⚕️ Male Doctor / Healthcare", "symbol": "👨‍⚕️ "},
        {"label": "👩‍⚕️ Female Doctor / Healthcare", "symbol": "👩‍⚕️ "},
        {"label": "👨‍🔬 Male Scientist / Lab Tech", "symbol": "👨‍🔬 "},
        {"label": "👩‍🔬 Female Scientist / Lab Tech", "symbol": "👩‍🔬 "},
        {"label": "👨‍💻 Male Developer / Tech", "symbol": "👨‍💻 "},
        {"label": "👩‍💻 Female Developer / Tech", "symbol": "👩‍💻 "},
        {"label": "👨‍🔧 Male Mechanic / Technician", "symbol": "👨‍🔧 "},
        {"label": "👩‍🔧 Female Mechanic / Technician", "symbol": "👩‍🔧 "},
        {"label": "👨‍🏭 Male Industrial / Factory", "symbol": "👨‍🏭 "},
        {"label": "👩‍🏭 Female Industrial / Factory", "symbol": "👩‍🏭 "},
        {"label": "👨‍💼 Male Executive / Office", "symbol": "👨‍💼 "},
        {"label": "👩‍💼 Female Executive / Office", "symbol": "👩‍💼 "},
        {"label": "👨‍🍳 Male Chef / Cook", "symbol": "👨‍🍳 "},
        {"label": "👩‍🍳 Female Chef / Cook", "symbol": "👩‍🍳 "},
        {"label": "👨‍✈️ Male Pilot / Aviation", "symbol": "👨‍✈️ "},
        {"label": "👩‍✈️ Female Pilot / Aviation", "symbol": "👩‍✈️ "},
        {"label": "👨‍🚒 Male Firefighter", "symbol": "👨‍🚒 "},
        {"label": "👩‍🚒 Female Firefighter", "symbol": "👩‍🚒 "},
        {"label": "👮 Police Officer", "symbol": "👮 "},
        {"label": "🕵️ Detective / Inspector", "symbol": "🕵️ "},
        {"label": "💂 Guard / Security", "symbol": "💂 "},
        {"label": "👷 Construction Worker", "symbol": "👷 "},
    ],
    "City & Architecture": [
        {"label": "🏙️ Cityscape / Skyline", "symbol": "🏙️ "},
        {"label": "🏢 Office Building", "symbol": "🏢 "},
        {"label": "🏘️ Houses / Neighborhood", "symbol": "🏘️ "},
        {"label": "🏠 House / Home", "symbol": "🏠 "},
        {"label": "🏡 House with Garden", "symbol": "🏡 "},
        {"label": "🏛️ Classical / Civic Building", "symbol": "🏛️ "},
        {"label": "🏬 Department Store", "symbol": "🏬 "},
        {"label": "🏭 Factory / Industrial", "symbol": "🏭 "},
        {"label": "🏗️ Construction / Crane", "symbol": "🏗️ "},
        {"label": "🏥 Hospital", "symbol": "🏥 "},
        {"label": "🏦 Bank / Financial", "symbol": "🏦 "},
        {"label": "🏫 School", "symbol": "🏫 "},
        {"label": "🏨 Hotel", "symbol": "🏨 "},
        {"label": "🗽 Statue of Liberty / Monument", "symbol": "🗽 "},
        {"label": "⛩️ Shinto Shrine / Landmark", "symbol": "⛩️ "},
        {"label": "🏰 Castle / Historic Site", "symbol": "🏰 "},
        {"label": "🌉 Bridge / Infrastructure", "symbol": "🌉 "},
    ],
    "Special Occasions": [
        # Holidays
        {"label": "🎃 Halloween", "symbol": "🎃 "},
        {"label": "🎄 Christmas tree", "symbol": "🎄 "},
        {"label": "🎅 Santa Claus", "symbol": "🎅 "},
        {"label": "🎆 New Year", "symbol": "🎆 "},
        {"label": "🍀 St. Patrick's", "symbol": "🍀 "},
        {"label": "🦃 Thanksgiving", "symbol": "🦃 "},
        # Birthdays & Weddings
        {"label": "🎂 Birthday cake", "symbol": "🎂 "},
        {"label": "🎁 Wrapped gift", "symbol": "🎁 "},
        {"label": "🎈 Balloon", "symbol": "🎈 "},
        {"label": "💍 Ring / Engagement", "symbol": "💍 "},
        {"label": "💒 Wedding chapel", "symbol": "💒 "},
        {"label": "🥂 Clinking glasses", "symbol": "🥂 "},
        {"label": "🍾 Champagne", "symbol": "🍾 "},
        # Vacation, Beach & Travel
        {"label": "🏖️ Beach umbrella", "symbol": "🏖️ "},
        {"label": "🏝️ Desert island", "symbol": "🏝️ "},
        {"label": "🌊 Ocean wave", "symbol": "🌊 "},
        {"label": "🌅 Sunrise / Sunset", "symbol": "🌅 "},
        {"label": "✈️ Airplane", "symbol": "✈️ "},
        {"label": "🧳 Luggage", "symbol": "🧳 "},
        {"label": "🗺️ Map", "symbol": "🗺️ "},
        {"label": "🚢 Cruise ship", "symbol": "🚢 "},
        ],
    "Fractions": [
        {"label": "½ One Half", "symbol": "½"},
        {"label": "⅓ One Third", "symbol": "⅓"},
        {"label": "⅔ Two Thirds", "symbol": "⅔"},
        {"label": "¼ One Quarter", "symbol": "¼"},
        {"label": "¾ Three Quarters", "symbol": "¾"},
        {"label": "⅕ One Fifth", "symbol": "⅕"},
        {"label": "⅖ Two Fifths", "symbol": "⅖"},
        {"label": "⅗ Three Fifths", "symbol": "⅗"},
        {"label": "⅘ Four Fifths", "symbol": "⅘"},
        {"label": "⅙ One Sixth", "symbol": "⅙"},
        {"label": "⅝ Five Sixths", "symbol": "⅝"},
        {"label": "⅛ One Eighth", "symbol": "⅛"},
        {"label": "⅜ Three Eighths", "symbol": "⅜"},
        {"label": "⅝ Five Eighths", "symbol": "⅝"},
        {"label": "⅞ Seven Eighths", "symbol": "⅞"},
        {"label": "⅐ One Seventh", "symbol": "⅐"},
        {"label": "⅑ One Ninth", "symbol": "⅑"},
        {"label": "⅒ One Tenth", "symbol": "⅒"},
    ],
    "Basic Operators & Arithmetic": [
        {"label": "+ Plus", "symbol": "+"},
        {"label": "− Minus", "symbol": "−"},
        {"label": "± Plus-Minus", "symbol": "±"},
        {"label": "∓ Minus-Plus", "symbol": "∓"},
        {"label": "× Multiplication Sign", "symbol": "×"},
        {"label": "÷ Division Sign", "symbol": "÷"},
        {"label": "⋅ Dot Operator / Multiplication", "symbol": "⋅"},
        {"label": "∗ Asterisk Operator", "symbol": "∗"},
        {"label": "= Equals", "symbol": "="},
        {"label": "≠ Not Equal To", "symbol": "≠"},
        {"label": "≈ Almost Equal To", "symbol": "≈"},
        {"label": "≅ Congruent / Approx Equal", "symbol": "≅"},
        {"label": "≡ Identical To / Equivalent", "symbol": "≡"},
        {"label": "∝ Proportional To", "symbol": "∝"},
    ],
    "Relations & Inequalities": [
        {"label": "< Less Than", "symbol": "<"},
        {"label": "> Greater Than", "symbol": ">"},
        {"label": "≤ Less Than or Equal To", "symbol": "≤"},
        {"label": "≥ Greater Than or Equal To", "symbol": "≥"},
        {"label": "≪ Much Less Than", "symbol": "≪"},
        {"label": "≫ Much Greater Than", "symbol": "≫"},
    ],
    "Algebra, Geometry & Calculus": [
        {"label": "° Degree", "symbol": "°"},
        {"label": "√ Square Root", "symbol": "√"},
        {"label": "∛ Cube Root", "symbol": "∛"},
        {"label": "∜ Fourth Root", "symbol": "∜"},
        {"label": "∞ Infinity", "symbol": "∞"},
        {"label": "∫ Integral", "symbol": "∫"},
        {"label": "∬ Double Integral", "symbol": "∬"},
        {"label": "∭ Triple Integral", "symbol": "∭"},
        {"label": "∮ Contour Integral", "symbol": "∮"},
        {"label": "∂ Partial Differential", "symbol": "∂"},
        {"label": "∇ Nabla / Del", "symbol": "∇"},
        {"label": "∑ N-ary Summation", "symbol": "∑"},
        {"label": "∏ N-ary Product", "symbol": "∏"},
    ],
    "Set Theory & Logic": [
        {"label": "∈ Element Of", "symbol": "∈"},
        {"label": "∉ Not an Element Of", "symbol": "∉"},
        {"label": "⊂ Subset Of", "symbol": "⊂"},
        {"label": "⊃ Superset Of", "symbol": "⊃"},
        {"label": "⊆ Subset of or Equal To", "symbol": "⊆"},
        {"label": "⊇ Superset of or Equal To", "symbol": "⊇"},
        {"label": "∪ Union", "symbol": "∪"},
        {"label": "∩ Intersection", "symbol": "∩"},
        {"label": "∅ Empty Set", "symbol": "∅"},
        {"label": "∧ Logical AND", "symbol": "∧"},
        {"label": "∨ Logical OR", "symbol": "∨"},
        {"label": "¬ Logical NOT", "symbol": "¬"},
        {"label": "∀ For All", "symbol": "∀"},
        {"label": "∃ There Exists", "symbol": "∃"},
        {"label": "∴ Therefore", "symbol": "∴"},
        {"label": "∵ Because", "symbol": "∵"},
    ],
    "Arrows & Transforms": [
        {"label": "→ Rightwards Arrow", "symbol": "→"},
        {"label": "← Leftwards Arrow", "symbol": "←"},
        {"label": "↔ Left Right Arrow", "symbol": "↔"},
        {"label": "⇒ Rightwards Double Arrow (Implies)", "symbol": "⇒"},
        {"label": "⇔ Left Right Double Arrow (Iff)", "symbol": "⇔"},
    ],
    "Greek Math Symbols": [
        {"label": "α Alpha", "symbol": "α"},
        {"label": "β Beta", "symbol": "β"},
        {"label": "γ Gamma", "symbol": "γ"},
        {"label": "δ Delta", "symbol": "δ"},
        {"label": "ε Epsilon", "symbol": "ε"},
        {"label": "θ Theta", "symbol": "θ"},
        {"label": "λ Lambda", "symbol": "λ"},
        {"label": "μ Mu / Micro", "symbol": "μ"},
        {"label": "π Pi", "symbol": "π"},
        {"label": "ρ Rho", "symbol": "ρ"},
        {"label": "σ Sigma", "symbol": "σ"},
        {"label": "φ Phi", "symbol": "φ"},
        {"label": "ω Omega", "symbol": "ω"},
        {"label": "Δ Capital Delta", "symbol": "Δ"},
        {"label": "Σ Capital Sigma", "symbol": "Σ"},
        {"label": "Ω Capital Omega", "symbol": "Ω"},
    ],
}
# EOB SYMBOL_MENU_CONFIG = {

# --- Menu Structure Definitions ---

TOP_LEVEL_CATEGORIES = [
    "Checkboxes",
    "Status, Time, & Scheduling",
]

CATEGORY_GROUPS = {
    "Math & Science": [
        "Fractions",
        "Basic Operators & Arithmetic",
        "Relations & Inequalities",
        "Algebra, Geometry & Calculus",
        "Set Theory & Logic",
        "Greek Math Symbols",
        "Arrows & Transforms",
    ],
    "Infrastructure & Tools": [
        "Devices",
        "Construction & Tools",
        "Navigation Symbols",
    ],
    "Places, Travel & Finance": [
        "Bank & Markets",
        "Coastal & Weather",
        "Travel",
        "City & Architecture",
    ],
    "People & Activities": [
        "Sports",
        "Medical & Laboratory",
        "Figures & Clothing",
        "Professions & Roles",
        "Special Occasions",
        "Misc Symbols",
    ],
}


# def check_single_instance():
#     if os.path.exists(LOCK_FILE):
#         # Attempt to bring the existing window to the front
#         try:
#             # Using wmctrl:
#             subprocess.run(["wmctrl", "-x", "-a", "mycompanion"], check=True)
# 
#             # OR using xdotool (alternative):
#             # subprocess.run(["xdotool", "search", "--onlyvisible", "--class", "mycompanion", "windowactivate"], check=True)
#         except (subprocess.CalledProcessError, FileNotFoundError):
#             pass  # Fallback if window isn't found or tool isn't installed
# 
#         print("MyCompanion is already running. Focused existing window.")
#         sys.exit(0)
# 
#     # Create lockfile
#     with open(LOCK_FILE, "w") as f:
#         f.write(str(os.getpid()))
# Did not implement this as it wasn't working the way I wanted - left the code here for more research
# check_single_instance()  

def dbug(msg: str) -> None:
    """Helper function to print debug messages only when DEBUG is enabled."""
    if DEBUG:
        frame = inspect.currentframe().f_back
        lineno = frame.f_lineno
        print(f"[DEBUG L{lineno}] {msg}")


def load_cfg_d(filepath=CONFIG_FILE):
    """
    Parses an INI file into a pure Python dictionary of dictionaries (cfg_d).
    Keeps everything native, transparent, and dependency-free.
    """
    path = Path(filepath).expanduser()
    cfg_d = {}

    if not path.exists():
        return cfg_d

    parser = configparser.ConfigParser(interpolation=None)
    # Preserve case sensitivity for keys if desired
    parser.optionxform = str
    
    try:
        parser.read(path, encoding="utf-8")
        for section in parser.sections():
            cfg_d[section] = dict(parser.items(section))
    except Exception as e:
        print(f"[ERROR] Failed to parse config file '{filepath}': {e}")

    return cfg_d

def save_cfg_d(cfg_d, filepath=CONFIG_FILE):
    """Flushes a dictionary of dictionaries directly to disk in INI format."""
    path = Path(filepath).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    for section, keys in cfg_d.items():
        if isinstance(keys, dict):
            parser[section] = {str(k): str(v) for k, v in keys.items()}
    with open(path, "w", encoding="utf-8") as f:
        parser.write(f)

def cfg_get(cfg_d, section, key, default=""):
    """Safely retrieves a string value from cfg_d."""
    if not isinstance(cfg_d, dict):
        return default
    return str(cfg_d.get(section, {}).get(key, default)).strip()

def cfg_bool(cfg_d, section, key, default=False):
    """Safely retrieves a boolean value from cfg_d."""
    if not isinstance(cfg_d, dict):
        return default
    val = cfg_d.get(section, {}).get(key, str(default))
    return str(val).lower() in ("true", "1", "yes", "on")

def cfg_set(cfg_d, section, key, value):
    """Sets a value in cfg_d in memory."""
    if not isinstance(cfg_d, dict):
        return
    if section not in cfg_d:
        cfg_d[section] = {}
    cfg_d[section][key] = str(value)

def get_custom_commands(cfg_d):
    """Parses dynamic custom command sections [cmd_*] or [command_*] from cfg_d dictionary."""
    commands = []
    if not isinstance(cfg_d, dict):
        return commands

    VALID_MODES = {
        "window": "window", "win": "window",
        "terminal": "terminal", "term": "terminal",
        "silent": "silent", "quiet": "silent",
        "raw": "raw", "exec": "raw", "direct": "raw",
    }

    for section, sec_data in cfg_d.items():
        if isinstance(sec_data, dict) and section.startswith(("cmd_", "command_")):
            # Helper for alias keys inside section dict
            shortcut = sec_data.get("shortcut") or sec_data.get("key") or sec_data.get("bind")
            cmd_str = sec_data.get("command") or sec_data.get("cmd") or sec_data.get("exec") or sec_data.get("run")

            if not shortcut or not cmd_str:
                print(f"[WARN] [{section}] missing required shortcut or command key. Skipping.")
                continue

            raw_mode = str(sec_data.get("mode") or sec_data.get("type") or "window").lower()
            mode = VALID_MODES.get(raw_mode, "window")
            title = sec_data.get("title") or sec_data.get("name") or cmd_str
            geometry = sec_data.get("geometry") or sec_data.get("geom") or sec_data.get("size") or ""

            commands.append({
                "section": section,
                "shortcut": shortcut,
                "command": cmd_str,
                "mode": mode,
                "title": title,
                "geometry": geometry,
            })

    return commands

# =====================================================================
# External Editor Helpers (Top-Level Module Scope)
# =====================================================================

def handle_external_edit(event, root, cfg_d):
  """Callback for Ctrl-e: identifies active widget and launches external editor."""
  dbug("[EVENT] <Control-e> triggered!")
  focused_widget = root.focus_get()

  if isinstance(focused_widget, (tk.Text, tk.Entry)):
    editor_cmd = cfg_d.get("Settings", {}).get("editor", "").strip()
    if editor_cmd:
      # Pass root as the 3rd argument to match open_editor_for_widget
      open_editor_for_widget(focused_widget, editor_cmd, root)
      return "break"
  return None


def open_editor_for_widget(widget, editor_cmd, root):
    """Launches external editor asynchronously without freezing Tkinter."""
    # 1. Extract content
    if isinstance(widget, tk.Text):
        content = widget.get("1.0", tk.END + "-1c")
    else:
        content = widget.get()

    # 2. Create temporary file
    try:
        tf = tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False)
        tf.write(content)
        tf.flush()
        temp_path = tf.name
        tf.close()
    except Exception as err:
        messagebox.showerror("File Error", f"Failed to create temp file: {err}")
        return

    # 3. Build command list
    try:
        cmd_args = shlex.split(editor_cmd)
        cmd_args.append(temp_path)
    except Exception as err:
        messagebox.showerror("Command Error", f"Invalid editor command line: {err}")
        os.remove(temp_path)
        return

    # 4. Spawn process non-blocking via Popen
    try:
        proc = subprocess.Popen(cmd_args)
    except FileNotFoundError:
        binary_name = cmd_args[0] if cmd_args else editor_cmd
        messagebox.showerror("Editor Not Found", f"Executable '{binary_name}' was not found in PATH.")
        os.remove(temp_path)
        return
    except Exception as err:
        messagebox.showerror("Launch Error", f"Failed to start editor:\n{err}")
        os.remove(temp_path)
        return

    # 5. Non-blocking monitor loop
    def check_editor_status():
        ret_code = proc.poll()
        if ret_code is None:
            # Still running: re-check in 200ms without blocking Tkinter events
            root.after(200, check_editor_status)
        else:
            # Process finished: read back content and clean up
            try:
                if ret_code == 0:
                    with open(temp_path, "r") as f:
                        new_content = f.read()

                    if isinstance(widget, tk.Text):
                        widget.delete("1.0", tk.END)
                        widget.insert("1.0", new_content)
                    else:
                        widget.delete(0, tk.END)
                        widget.insert(0, new_content.rstrip("\r\n"))
                else:
                    dbug(f"[EDITOR] Editor exited with non-zero code: {ret_code}")
            except Exception as read_err:
                dbug(f"[ERROR] Failed reading temp file back: {read_err}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

    # Start polling loop
    check_editor_status()



# ----------------------------------------------------------------------
# Top-level standalone helper function
# ----------------------------------------------------------------------
def sanitize_geometry(geom_str, min_w=200, min_h=200, default_w=600, default_h=400):
    """
    Validates a Tkinter geometry string (e.g. '800x600+100+100').
    If width < min_w or height < min_h, returns safe default dimensions.
    """
    if not geom_str or not isinstance(geom_str, str):
        return f"{default_w}x{default_h}"

    match = re.match(r"^(\d+)x(\d+)([\+-].*)?$", geom_str.strip())
    if not match:
        return f"{default_w}x{default_h}"

    w, h, offsets = match.groups()
    w, h = int(w), int(h)

    if w < min_w or h < min_h:
        w, h = default_w, default_h

    offsets_str = offsets if offsets else ""
    return f"{w}x{h}{offsets_str}"

def load_symbol_config(filepath="symbols.json"):
    """Loads symbol menu structure from JSON, falling back to default dict if missing."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return SYMBOL_MENU_CONFIG

def create_symbol_menu_from_config(
    parent_window, get_active_widget_func, config=SYMBOL_MENU_CONFIG
):
  """Dynamically builds a tk.Menu with prioritized top items and grouped submenus."""
  main_menu = tk.Menu(parent_window, tearoff=0)

  # Merge 'Status & Emojis' and 'Time & Scheduling' if they exist separately in config
  working_config = dict(config)
  if "Status, Time & Priority" not in working_config:
    status_items = working_config.get("Status & Emojis", [])
    time_items = working_config.get("Time & Scheduling", [])
    working_config["Status, Time & Priority"] = status_items + time_items

  def do_insert(symbol):
    widget = get_active_widget_func()
    if widget:
      widget.insert("insert", symbol)

  # 1. Top-Level Priority Items
  for cat_name in TOP_LEVEL_CATEGORIES:
    if cat_name in working_config:
      sub_menu = tk.Menu(main_menu, tearoff=0)
      for item in working_config[cat_name]:
        sym = item["symbol"]
        sub_menu.add_command(
            label=item["label"], command=lambda s=sym: do_insert(s)
        )
      main_menu.add_cascade(label=cat_name, menu=sub_menu)

  main_menu.add_separator()

  # 2. Grouped Category Folders
  for group_name, cat_list in CATEGORY_GROUPS.items():
    group_menu = tk.Menu(main_menu, tearoff=0)
    has_items = False

    for cat_name in cat_list:
      if cat_name in working_config:
        cat_menu = tk.Menu(group_menu, tearoff=0)
        for item in working_config[cat_name]:
          sym = item["symbol"]
          cat_menu.add_command(
              label=item["label"], command=lambda s=sym: do_insert(s)
          )
        group_menu.add_cascade(label=cat_name, menu=cat_menu)
        has_items = True

    if has_items:
      main_menu.add_cascade(label=f"📁 {group_name}", menu=group_menu)

  # 3. Fallback for any leftover categories
  ungrouped = [
      c
      for c in working_config
      if c not in TOP_LEVEL_CATEGORIES
      and c not in ["Status & Emojis", "Time & Scheduling"]
      and not any(c in g for g in CATEGORY_GROUPS.values())
  ]

  if ungrouped:
    other_menu = tk.Menu(main_menu, tearoff=0)
    for cat_name in ungrouped:
      cat_menu = tk.Menu(other_menu, tearoff=0)
      for item in working_config[cat_name]:
        sym = item["symbol"]
        cat_menu.add_command(
            label=item["label"], command=lambda s=sym: do_insert(s)
        )
      other_menu.add_cascade(label=cat_name, menu=cat_menu)
    main_menu.add_cascade(label="📁 Other", menu=other_menu)

  # 4. Standard Clipboard Commands
  main_menu.add_separator()
  main_menu.add_command(
      label="Copy",
      command=lambda: (
          get_active_widget_func().event_generate("<<Copy>>")
          if get_active_widget_func()
          else None
      ),
  )
  main_menu.add_command(
      label="Paste",
      command=lambda: (
          get_active_widget_func().event_generate("<<Paste>>")
          if get_active_widget_func()
          else None
      ),
  )

  return main_menu


def open_external_markdown_editor(cmd_str, file_path):
    """
    Launches an external markdown editor (e.g. 'retext') in a detached background process.
    Returns True if successfully launched, False otherwise.
    """
    if not cmd_str or not cmd_str.strip():
        return False

    file_path = os.path.abspath(os.path.expanduser(file_path))

    try:
        if sys.platform == "win32":
            cmd_list = shlex.split(cmd_str, posix=False)
            cmd_list.append(file_path)
            subprocess.Popen(cmd_list, creationflags=subprocess.DETACHED_PROCESS)
        else:
            # Linux / macOS
            cmd_list = shlex.split(cmd_str)
            cmd_list.append(file_path)
            subprocess.Popen(cmd_list, start_new_session=True)
            
        return True
    except Exception as e:
        print(f"[ERROR] Failed to launch external markdown editor '{cmd_str}': {e}")
        return False

# ----------------------------------------------------------------------
# ConfigViewerWindow (which hot shortcut buttons)
# ----------------------------------------------------------------------
class ConfigViewerWindow(tk.Toplevel):
    def __init__(self, parent, config_path, geometry="850x750", app=None):
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.config_path = config_path
        self.title("Configuration Viewer & Quick Launch")
        self.geometry(geometry)

        self.lift()
        self.focus_force()

        # Resolve palette from app or fall back to 'Dark / White (Default)'
        self.theme = self._resolve_theme_palette()

        self.bg_color = self.theme.get("bg", "#1e1e1e")
        self.fg_color = self.theme.get("fg", "#d4d4d4")
        self.panel_bg = self.theme.get("panel_bg", self.bg_color)
        self.btn_bg = self.theme.get("btn_bg", "#333333")
        self.btn_fg = self.theme.get("btn_fg", "#ffffff")

        # Set Toplevel background
        self.configure(bg=self.bg_color)

        self.bind("<Escape>", lambda e: self.destroy())
        self._build_ui()

    def _resolve_theme_palette(self):
        """Extract the active theme dict from app, module globals, or default."""
        # 1. Check if app carries the theme dict directly
        if self.app:
            if hasattr(self.app, "current_theme") and isinstance(self.app.current_theme, dict):
                return self.app.current_theme
            if hasattr(self.app, "theme") and isinstance(self.app.theme, dict):
                return self.app.theme
            if hasattr(self.app, "colors") and isinstance(self.app.colors, dict):
                return self.app.colors

            # 2. Check if app tracks current theme by string name (e.g., self.app.current_theme_name)
            theme_name = None
            for attr in ["current_theme_name", "theme_name", "active_theme"]:
                if hasattr(self.app, attr):
                    theme_name = getattr(self.app, attr)
                    break

            if theme_name and "THEMES" in globals() and theme_name in globals()["THEMES"]:
                return globals()["THEMES"][theme_name]

        # 3. Fallback check on globals directly
        if "THEMES" in globals():
            # Attempt to grab active theme name or default to 'Dark / White (Default)'
            themes = globals()["THEMES"]
            return themes.get("Dark / White (Default)", next(iter(themes.values())))

        # Fallback dictionary if all else fails
        return {
            "bg": "#1e1e1e", "fg": "#d4d4d4", "header_bg": "#1a1a1a",
            "nav_bg": "#2d2d2d", "panel_bg": "#2d2d2d", "btn_bg": "#333333",
            "btn_fg": "#ffffff", "insert_bg": "#ffffff"
        }

    def _build_ui(self):
        # Header
        top_frame = tk.Frame(self, bg=self.theme.get("header_bg", self.bg_color), padx=10, pady=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Label(
            top_frame,
            text="Configuration Shortcuts (Click Shortcut Button to Launch)",
            font=("TkDefaultFont", 11, "bold"),
            bg=self.theme.get("header_bg", self.bg_color),
            fg=self.fg_color
        ).pack(anchor=tk.W)

        # Scrollable Area Container
        container = tk.Frame(self, bg=self.bg_color, padx=10, pady=5)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(
            container,
            bg=self.bg_color,
            highlightbackground=self.bg_color,
            highlightcolor=self.bg_color,
            highlightthickness=0,
            bd=0,
            relief=tk.FLAT
        )

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=self.bg_color)

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.bind("<Configure>", _on_canvas_configure)

        def _update_scrollregion(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            scroll_frame.configure(bg=self.bg_color)

        scroll_frame.bind("<Configure>", _update_scrollregion)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Parse and Render Shortcut Cards
        cp = configparser.ConfigParser()
        cp.read(self.config_path, encoding="utf-8")

        def make_handler(c, m, t, g):
            def handler():
                if self.app and hasattr(self.app, "run_command"):
                    self.app.run_command(cmd_str=c, open_in=m, title=t, geometry=g)
            return handler

        for section in cp.sections():
            if section.startswith("cmd_"):
                cmd_name = section.replace("cmd_", "").upper()
                shortcut = cp.get(section, "shortcut", fallback="RUN")

                cmd_val = cp.get(section, "command", fallback=cp.get(section, "cmd", fallback="")).strip()
                mode_val = cp.get(section, "mode", fallback="terminal").strip()
                title_val = cp.get(section, "title", fallback=cmd_name).strip()
                geom_val = cp.get(section, "geometry", fallback="").strip()

                if not cmd_val:
                    continue

                # Shortcut Card Box matching theme panel_bg
                row = tk.LabelFrame(
                    scroll_frame,
                    text=f" [{section}] ",
                    font=("TkDefaultFont", 10, "bold"),
                    bg=self.panel_bg,
                    fg=self.fg_color,
                    highlightbackground=self.bg_color,
                    highlightthickness=1,
                    padx=10,
                    pady=8
                )
                row.pack(fill=tk.X, expand=True, pady=5, padx=5)

                # Shortcut Button matching theme btn_bg and btn_fg
                btn = tk.Button(
                    row,
                    text=f"⚡ {shortcut}",
                    font=("TkDefaultFont", 9, "bold"),
                    bg=self.btn_bg,
                    fg=self.btn_fg,
                    activebackground=self.btn_fg,
                    activeforeground=self.btn_bg,
                    highlightbackground=self.panel_bg,
                    relief=tk.RAISED,
                    bd=2,
                    command=make_handler(cmd_val, mode_val, title_val, geom_val)
                )
                btn.pack(side=tk.LEFT, padx=(0, 10), anchor=tk.N)

                # Details Frame
                details_frame = tk.Frame(row, bg=self.panel_bg)
                details_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

                lbl_info = tk.Label(
                    details_frame,
                    text=f"Mode: {mode_val}  |  Title: {title_val}  |  Geom: {geom_val or 'default'}",
                    font=("TkDefaultFont", 9, "bold"),
                    bg=self.panel_bg,
                    fg=self.fg_color
                )
                lbl_info.pack(anchor=tk.W)

                lbl_cmd = tk.Label(
                    details_frame,
                    text=f"Command: {cmd_val}",
                    wraplength=550,
                    justify=tk.LEFT,
                    bg=self.panel_bg,
                    fg=self.fg_color
                )
                lbl_cmd.pack(anchor=tk.W, pady=(2, 0))


# ----------------------------------------------------------------------
# Configuration Manager Class
# ----------------------------------------------------------------------
class ConfigManager:
    """Manages application configuration via mycompanion.conf (INI format)."""

    def __init__(self, filepath=CONFIG_FILE):
        self.filepath = Path(filepath)
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        """Loads configuration from file and populates missing default keys."""
        if not self.filepath.exists():
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            self.config.read_dict(DEFAULT_CONFIG)
            self.save_config()
            return

        # Load existing configuration directly from disk
        self.config.read(self.filepath, encoding="utf-8")

        # Ensure baseline default sections and keys exist without overwriting user settings
        for section, keys in DEFAULT_CONFIG.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for key, val in keys.items():
                if not self.config.has_option(section, key):
                    self.config.set(section, key, str(val))

        # Sanitize Window Geometry if present
        section_name = "Window" if self.config.has_section("Window") else "General"
        if self.config.has_option(section_name, "geometry"):
            raw_geom = self.config.get(section_name, "geometry")
            safe_geom = sanitize_geometry(raw_geom, min_w=200, min_h=200, default_w=600, default_h=400)
            self.config.set(section_name, "geometry", safe_geom)

    def save_config(self):
        """Flushes in-memory configuration directly to disk."""
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                self.config.write(f)
        except Exception as e:
            print(f"[ERROR] Failed to save config: {e}")

    def get_string(self, section, key, default=""):
        """Retrieves any string value from any section."""
        if self.config.has_section(section) and self.config.has_option(section, key):
            return self.config.get(section, key, fallback=default).strip()
        return default

    def get_bool(self, section, key, default=False):
        """Retrieves any boolean value from any section."""
        try:
            return self.config.getboolean(section, key)
        except Exception:
            return default

    def set_value(self, section, key, value):
        """Sets a value dynamically in memory and flushes immediately to disk."""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        self.save_config()

    def _get_flexible(self, section_proxy, keys, default=""):
        """Utility to retrieve the first matching key from a list of alias keys."""
        for k in keys:
            if k in section_proxy:
                return section_proxy.get(k, "").strip()
        return default

    def get_custom_commands(self):
        """Parses dynamic custom command sections [cmd_*] or [command_*]."""
        commands = []
        VALID_MODES = {
            "window": "window", "win": "window",
            "terminal": "terminal", "term": "terminal",
            "silent": "silent", "quiet": "silent",
            "raw": "raw", "exec": "raw", "direct": "raw",
        }
        for section in self.config.sections():
            if section.startswith(("cmd_", "command_")):
                sec = self.config[section]
                shortcut = self._get_flexible(sec, ["shortcut", "key", "bind"])
                cmd_str = self._get_flexible(sec, ["command", "cmd", "exec", "run"])

                if not shortcut or not cmd_str:
                    print(f"Warning: [{section}] missing required shortcut or command key. Skipping.")
                    continue

                raw_mode = self._get_flexible(sec, ["mode", "type"], default="window").lower()
                mode = VALID_MODES.get(raw_mode, "window")
                title = self._get_flexible(sec, ["title", "name"], default=cmd_str)
                geometry = self._get_flexible(sec, ["geometry", "geom", "size"])

                commands.append({
                    "section": section,
                    "shortcut": shortcut,
                    "command": cmd_str,
                    "mode": mode,
                    "title": title,
                    "geometry": geometry,
                })
        return commands
    # ### EOB class ConfigManager: ### #


def normalize_tk_shortcut(raw_shortcut: str) -> str:
    """
    Normalizes sloppy, alias-heavy, or unbracketed shortcut strings into standard Tkinter sequence strings.
    
    Examples:
      'Control-Shift-w'     -> '<Control-Shift-W>'
      'ctrl-shft-w'        -> '<Control-Shift-W>'
      'Ctrl-shift-w'       -> '<Control-Shift-W>'
      '<Control-Key-Shift-w>' -> '<Control-Shift-W>'
      'alt-ctrl-t'         -> '<Control-Alt-t>'
    """
    # 1. Map common human aliases to standard Tkinter modifier names
    ALIAS_MAP = {
        "ctrl": "Control",
        "cntrl": "Control",
        "control": "Control",
        "shift": "Shift",
        "shft": "Shift",
        "sft": "Shift",
        "alt": "Alt",
        "option": "Alt",
        "opt": "Alt",
        "cmd": "Command",
        "meta": "Meta",
    }

    # Clean out surrounding brackets and redundant 'Key-' prefixes
    inner = raw_shortcut.strip("<>").replace("Key-", "")
    parts = [p.strip() for p in inner.split("-") if p.strip()]
    
    if not parts:
        return raw_shortcut

    # Key is always the last token; everything prior is a modifier
    raw_key = parts[-1]
    raw_modifiers = parts[:-1]

    # 2. Normalize modifier names using the alias map
    modifiers = []
    for mod in raw_modifiers:
        mod_lower = mod.lower()
        normalized_mod = ALIAS_MAP.get(mod_lower, mod.capitalize())
        if normalized_mod not in modifiers:
            modifiers.append(normalized_mod)

    # 3. Handle key casing for Shift combinations
    key = raw_key
    if "Shift" in modifiers and len(key) == 1 and key.islower():
        key = key.upper()

    # 4. Reconstruct clean, bracketed Tkinter event sequence
    if modifiers:
        return f"<{'-'.join(modifiers)}-{key}>"
    return f"<{key}>"

def print_help_and_paths():
    print(__doc__)
    print("----------------------------------------")
    print("Storage & Runtime Locations:")
    print(f"  • Data / Store Directory : {DATA_DIR}")
    print(f"  • Notes File             : {NOTES_FILE}")
    print(f"  • Calendar Notes File    : {CAL_NOTES_FILE}")
    print(f"  • Calculator History File: {CALC_NOTES_FILE}")
    print(f"  • To-Do File             : {TODO_FILE}")
    print(f"  • Application Config File: {CONFIG_FILE}")
    print(f"  • Lock File              : {LOCK_FILE}")
    print("----------------------------------------")
    print("companionway.net © 2026")
    print("----------------------------------------")


def is_wayland() -> bool:
    """Check if the current desktop session is running on Wayland."""
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"

def ensure_daemon(doc_args: dict) -> None:
    # 1. Lockfile check
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r", encoding="utf-8") as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)
            print(f"MyCompanion is already running (PID {old_pid}).")
            print("Use Ctrl-Space to toggle the window.")
            print(f"Lock file location: {LOCK_FILE}")
            sys.exit(0)
        except (ProcessLookupError, ValueError):
            try:
                os.remove(LOCK_FILE)
            except OSError:
                pass
        except PermissionError:
            sys.exit(0)

    # Write lockfile for the current process
    with open(LOCK_FILE, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))

    # 1. Standard Window Mode (Default): Bypass daemon/subprocess spawning entirely
    if not doc_args.get("--toggle") or is_wayland():
        if doc_args.get("--toggle") and is_wayland():
            print("Warning: --toggle (TSR mode) is not supported under Wayland.")
            print("Running in standard window mode instead...")

        os.environ["SIDEKICK_DAEMON"] = "1"
        return



    # 2. Wayland Guard: If --toggle WAS requested but we're on Wayland, warn and fallback
    if is_wayland():
        print("Warning: --toggle (TSR mode) is not supported under Wayland.")
        print("Running in standard window mode instead...")
        os.environ["SIDEKICK_DAEMON"] = "1"
        return

    global DEBUG
    script_path = os.path.abspath(__file__)
    python_exec = sys.executable


    # 2. Main launch handling
    if os.environ.get("SIDEKICK_DAEMON") != "1":
        # Handle --log setup if requested
        log_handle = None
        if doc_args.get("--log"):
            log_handle = open(LOG_FILE, "a", encoding="utf-8", buffering=1)

        if DEBUG:
            # Foreground / Debug Execution
            os.environ["SIDEKICK_DAEMON"] = "1"
            if log_handle:
                # Tee/redirect standard output streams to log file while keeping terminal attached
                sys.stdout = log_handle
                sys.stderr = log_handle
            return

        # Background Daemon Spawn Execution
        new_env = os.environ.copy()
        new_env["SIDEKICK_DAEMON"] = "1"
        args_list = [python_exec, script_path] + sys.argv[1:]

        popen_kwargs = {
            "env": new_env,
            "start_new_session": True,
            "stdin": subprocess.DEVNULL,
        }

        if log_handle:
            popen_kwargs["stdout"] = log_handle
            popen_kwargs["stderr"] = log_handle
        else:
            popen_kwargs["stdout"] = subprocess.DEVNULL
            popen_kwargs["stderr"] = subprocess.DEVNULL

        subprocess.Popen(args_list, **popen_kwargs)
        sys.exit(0)
    else:
        # Child daemon initialization
        with open(LOCK_FILE, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    # ### EOB def ensure_daemon(): ### #


def solve_proportion(val, default=None):
    """Parse and solve proportion strings for any non-numeric variable name or symbol."""
    if not isinstance(val, str):
        return default if default is not None else val

    s = val.strip().lower()

    # Pattern 1: Text/Colon format: "17 is to 30 as price is to 170" or "17:30 :: ? : 170"
    pattern_text = r"^(.+?)\s+(?:is\s+to|:)\s+(.+?)\s+(?:as|::|=)\s+(.+?)\s+(?:is\s+to|:)\s+(.+?)$"

    # Pattern 2: Fraction format: "17/30 =|as price/170"
    pattern_eq = r"^(.+?)\s*/\s*(.+?)\s*(?:=|\bas\b)\s*(.+?)\s*/\s*(.+?)$"

    match = re.match(pattern_text, s) or re.match(pattern_eq, s)
    if not match:
        return default if default is not None else val

    terms = [t.strip() for t in match.groups()]

    var_index = None
    for i, term in enumerate(terms):
        try:
            terms[i] = float(term)
        except ValueError:
            if var_index is None:
                var_index = i
            else:
                # More than one variable found; unparseable
                return default if default is not None else val

    # If all 4 terms are numbers, it's not a variable proportion
    if var_index is None:
        return default if default is not None else val

    a, b, c, d = terms

    try:
        if var_index == 0:    # var / B = C / D
            return (b * c) / d
        elif var_index == 1:  # A / var = C / D
            return (a * d) / c
        elif var_index == 2:  # A / B = var / D
            return (a * d) / b
        elif var_index == 3:  # A / B = C / var
            return (b * c) / a
    except ZeroDivisionError:
        return default if default is not None else val

    return default if default is not None else val


# ----------------------------------------------------------------------
# MiniSidekick Class
# ----------------------------------------------------------------------
class MiniSidekick:
    def __init__(self, start_with_ai=False, doc_args=None, **kwargs):
        self.doc_args = doc_args or {}
        # self.cfg = ConfigManager()  # maybe rename cfg to cfg_d later?
        self.cfg = load_cfg_d()
        # dbug(f"{self.cfg=}")
        self.note_file = NOTES_FILE
        self.cal_notes_file = CAL_NOTES_FILE
        self.calc_history_file = CALC_NOTES_FILE
        self.todo_file = TODO_FILE

        ai_cfg = self.cfg.get("Settings", {}).get("ai_mode", "false")
        self.enable_ai = start_with_ai or (str(ai_cfg).lower() in ("true", "1", "yes"))

        if self.enable_ai:
            if not os.environ.get("GEMINI_API_KEY"):
                messagebox.showerror(
                    "Missing API Key",
                    "GEMINI_API_KEY environment variable is not defined.\n\n"
                    "Please set it prior to startup with --ai:\n"
                    'export GEMINI_API_KEY="my_ai_google_key"'
                )
                self.enable_ai = False  # Gracefully fall back to non-AI mode

        self.root = tk.Tk(className="mycompanion")

        # Check external editor is configured and bind Ctrl-e
        editor_setting = self.cfg.get("Settings", {}).get("editor", "").strip().lower()
        # dbug(f"[INIT] Editor setting detected: '{editor_setting}'")

        if editor_setting:
            # dbug(f"[INIT] Registering global <Control-e> binding for editor '{editor_setting}'...")
            self.root.bind_all( "<Control-e>", lambda evt: handle_external_edit(evt, self.root, self.cfg))

        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            print("--- UNCAUGHT EXCEPTION ---", file=sys.stderr)
            print(error_msg, file=sys.stderr)
            sys.stderr.flush()

        self.root.report_callback_exception = handle_exception
        sys.excepthook = handle_exception

        self.root.title(os.path.basename(__file__))

        # saved_geometry = cfg_get(self.cfg, "Window", "geometry", "640x500")
        saved_geometry = self.cfg.get("Window", {}).get("geometry", "640x500")
        self.root.geometry(saved_geometry)
        self.root.attributes("-topmost", True)
        if self.doc_args.get("--toggle") and not is_wayland():
            self.root.withdraw()
            self.is_visible = False
        else:
            self.root.deiconify()
            self.is_visible = True
        # self.root.withdraw()

        self.last_checked_date = datetime.datetime.now().date()
        self.sub_windows = []

        # --- TOP HEADER ---
        self.header_frame = tk.Frame(self.root, pady=5, padx=10)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)

        self.date_label = tk.Label(self.header_frame, text="", font=("Monospace", 9))
        self.date_label.pack(side=tk.LEFT)

        self.title_label = tk.Label(self.header_frame, text=f"{TITLE}", font=("Monospace", 10, "bold"))
        self.title_label.pack(side=tk.LEFT, expand=True)

        self.version_label = tk.Label(self.header_frame, text=f" v{VERSION}", font=("Monospace", 9))
        self.version_label.pack(side=tk.RIGHT)

        self.time_label = tk.Label(self.header_frame, text="", font=("Monospace", 9))
        self.time_label.pack(side=tk.RIGHT)

        # --- NAVIGATION BAR ---
        self.nav_frame = tk.Frame(self.root)
        self.nav_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Button(self.nav_frame, text="1. Notes", command=lambda: self.switch_view("notes"), bd=0, padx=10, pady=5).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(self.nav_frame, text="2. Calc", command=lambda: self.switch_view("calc"), bd=0, padx=10, pady=5).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(self.nav_frame, text="3. Calendar", command=lambda: self.switch_view("cal"), bd=0, padx=10, pady=5).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(self.nav_frame, text="4. Todo", command=lambda: self.switch_view("todo"), bd=0, padx=10, pady=5).pack(side=tk.LEFT, expand=True, fill=tk.X)

        # --- BOTTOM AI BAR ---
        self.ai_frame = tk.Frame(self.root, pady=8, padx=10)

        ai_label = tk.Label(self.ai_frame, text="Gemini:", font=("Monospace", 10, "bold"))
        ai_label.pack(side=tk.LEFT, padx=(0, 8))

        self.ai_input = tk.Entry(self.ai_frame, font=("Monospace", 10), bd=1, relief=tk.FLAT)
        self.ai_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=4)
        self.ai_input.bind("<Return>", self.send_to_gemini_click)

        ai_btn = tk.Button(self.ai_frame, text=" Ask ", command=self.send_to_gemini_click, bd=0, padx=12, pady=3)
        ai_btn.pack(side=tk.RIGHT)

        # --- FOOTER AREA ---
        # Fetch initial theme colors dictionary
        theme_name = self.cfg.get("Theme", {}).get("name", "Cyberpunk Neon")
        theme_colors = THEMES.get(theme_name, THEMES.get("Dark / White (Default)", {}))

        footer_bg = theme_colors.get("nav_bg", "#1e1e1e")
        text_fg = theme_colors.get("fg", "#d4d4d4")
        # btn_bg = theme_colors.get("btn_bg", theme_colors.get("panel_bg", "#333333"))
        btn_fg = theme_colors.get("btn_fg", text_fg)

        self.footer_frame = tk.Frame(
            self.root,
            bd=1,
            relief=tk.SOLID,
            bg=footer_bg,
        )
        self.footer_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=2, pady=2)

        # Save Button (Right side)
        self.save_btn = tk.Button(
            self.footer_frame,
            text="Save (Ctrl-S)",
            command=self.save_file,
            bg=footer_bg,
            fg=btn_fg,
            bd=0,
            padx=10,
            pady=2
        )
        self.save_btn.pack(side=tk.RIGHT, padx=5, pady=2)

        # --- MAIN CONTENT AREA ---
        self.content_frame = tk.Frame(self.root)
        self.content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # --- VIEW 1: NOTES ---
        self.notes_frame = tk.Frame(self.content_frame)
        self.notes_ctrl_frame = tk.Frame(self.notes_frame, pady=4, padx=10)
        self.notes_ctrl_frame.pack(side=tk.TOP, fill=tk.X)

        lbl_notes = "Notes"
        self.notes_lbl_widget = tk.Label(self.notes_ctrl_frame, text=lbl_notes, font=("Monospace", 9, "bold"))
        self.notes_lbl_widget.pack(side=tk.LEFT)

        # Insert Menu button
        tk.Button( self.notes_ctrl_frame, text="Insert Menu", command=self.show_insert_menu, bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0)) 

        tk.Button(self.notes_ctrl_frame, text="Save Selected As", command=self.save_selected_as, bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0))
        # tk.Button(self.notes_ctrl_frame, text="AI (Ctrl-a)", command=self.toggle_ai_bar, bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0))

        if self.enable_ai:
            tk.Button(self.notes_ctrl_frame, text="AI (Ctrl-a)", command=self.toggle_ai_bar, bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0))

        self.text_area = tk.Text(
            self.notes_frame, wrap=tk.WORD, font=("Monospace", 11), bd=0, padx=10, pady=10
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.text_area.bind("<KeyRelease>", lambda e: self.apply_link_parsing(self.text_area))
        self.load_notes()

        # --- VIEW 2: CALCULATOR ---
        self.calc_frame = tk.Frame(self.content_frame)

        self.calc_input_container = tk.Frame(self.calc_frame)
        self.calc_input_container.pack(fill=tk.X, padx=15, pady=15)

        self.calc_label = tk.Label(self.calc_input_container, text="Calculation: ", font=("Monospace", 14))
        self.calc_label.pack(side=tk.LEFT)

        self.calc_display = tk.Entry(self.calc_input_container, font=("Monospace", 14), bd=0)
        self.calc_display.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.calc_display.bind("<Return>", self.evaluate_calc)

        self.calc_result = tk.Label(self.calc_frame, text="Type an expression and hit Enter (e.g., 45 * 12)", font=("Monospace", 10), fg="#888")
        self.calc_result.pack(padx=15, anchor="w")

        self.calc_history_header = tk.Frame(self.calc_frame)
        self.calc_history_header.pack(fill=tk.X, padx=15, pady=(15, 5))

        self.calc_history_lbl = tk.Label(self.calc_history_header, text="Calculation History:", font=("Monospace", 10, "bold"), fg="#888", anchor="w")
        self.calc_history_lbl.pack(side=tk.LEFT)

        # Insert Menu button
        tk.Button( self.calc_history_header, text="Insert Menu", command=self.show_insert_menu, bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0)) 

        tk.Button(self.calc_history_header, text="Save Select As...", command=self.save_selected_as, bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0))

        self.calc_history_text = tk.Text(
            self.calc_frame, wrap=tk.WORD, font=("Monospace", 10), bd=0, padx=10, pady=10
        )
        self.calc_history_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        self.calc_history_text.bind("<KeyRelease>", lambda e: self.apply_link_parsing(self.calc_history_text))
        self.load_calc_history()

        # --- VIEW 3: CALENDAR ---
        self.cal_frame = tk.Frame(self.content_frame)

        self.cal_text = tk.Text(
            self.cal_frame, wrap=tk.NONE, font=("Monospace", 10), bd=0, padx=15, pady=10, height=9
        )
        self.cal_text.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.load_calendar()

        self.cal_notes_header_frame = tk.Frame(self.cal_frame)
        self.cal_notes_header_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=(5, 0))

        self.cal_notes_label = tk.Label(self.cal_notes_header_frame, text="Calendar Notes:", font=("Monospace", 10, "bold"), anchor="w")
        self.cal_notes_label.pack(side=tk.LEFT)

        # --- add Insert Menu button --- #
        tk.Button( self.cal_notes_header_frame, text="Insert Menu", command=self.show_insert_menu, bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0)) 

        tk.Button(self.cal_notes_header_frame, text="Save Select As...", command=self.save_selected_as, bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0))

        self.cal_notes_text = tk.Text(
            self.cal_frame, wrap=tk.WORD, font=("Monospace", 10), bd=0, padx=10, pady=5
        )
        self.cal_notes_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=15, pady=10)
        self.cal_notes_text.bind("<KeyRelease>", lambda e: self.apply_link_parsing(self.cal_notes_text))
        self.load_cal_notes()

        # --- VIEW 4: TODO ---
        self.todo_frame = tk.Frame(self.content_frame)
        self.todo_ctrl_frame = tk.Frame(self.todo_frame, pady=4, padx=10)
        self.todo_ctrl_frame.pack(side=tk.TOP, fill=tk.X)

        lbl_todo = "To-Do"
        self.todo_lbl_widget = tk.Label(self.todo_ctrl_frame, text=lbl_todo, font=("Monospace", 9, "bold"))
        self.todo_lbl_widget.pack(side=tk.LEFT)

        # Insert Menu button
        tk.Button( self.todo_ctrl_frame, text="Insert Menu", command=self.show_insert_menu, bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0)) 

        tk.Button(self.todo_ctrl_frame, text="Save Select As...", command=self.save_selected_as, bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0))

        self.todo_text_area = tk.Text(
            self.todo_frame, wrap=tk.WORD, font=("Monospace", 11), bd=0, padx=10, pady=10
        )
        self.todo_text_area.pack(fill=tk.BOTH, expand=True)
        self.todo_text_area.bind("<KeyRelease>", lambda e: self.apply_link_parsing(self.todo_text_area))
        self.load_todo()

        self.ai_visible = False
        if self.enable_ai:
            self.toggle_ai_bar(force_state=True)

        self.current_view = None
        self.switch_view("notes")
        self.update_header_clock()

        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        for ctrl_seq in ("<Control-1>", "<Control-Key-1>"):
            self.root.bind(ctrl_seq, lambda e: self.handle_tab_shortcut("notes"))
        for ctrl_seq in ("<Control-2>", "<Control-Key-2>"):
            self.root.bind(ctrl_seq, lambda e: self.handle_tab_shortcut("calc"))
        for ctrl_seq in ("<Control-3>", "<Control-Key-3>"):
            self.root.bind(ctrl_seq, lambda e: self.handle_tab_shortcut("cal"))
        for ctrl_seq in ("<Control-4>", "<Control-Key-4>"):
            self.root.bind(ctrl_seq, lambda e: self.handle_tab_shortcut("todo"))

        # --- KEYBINDINGS --- #
        self.root.bind("<Control-s>", self.save_selected_as)
        self.root.bind("<Control-S>", self.save_selected_as)

        self.root.bind("<Control-a>", lambda e: self.toggle_ai_bar())
        self.root.bind("<Control-A>", lambda e: self.toggle_ai_bar())
        self.root.bind("<Alt-c>",     lambda e: self.view_config_file())
        # self.root.bind("<Control-E>", lambda e: self.edit_config_file())
        self.root.bind("<Control-t>", lambda e: self.open_theme_selector())
        self.root.bind("<Control-T>", lambda e: self.open_theme_selector())
        self.root.bind("<Control-q>", lambda event: self.quit_app())
        self.root.bind("<Control-Q>", lambda event: self.quit_app())

        self.root.bind("<Control-h>", lambda e: self.show_help_legend())
        self.root.bind("<Control-H>", lambda e: self.show_help_legend())
        self.root.bind("<Control-slash>", lambda e: self.show_help_legend())

        self.root.bind("<Control-r>", lambda e: self.prompt_run_command())
        self.root.bind("<Control-R>", lambda e: self.prompt_run_command())

        # ---- custom commands setup ---- #
        self.bind_custom_commands()

        self.is_visible = False
        self.hotkey_listener = None

        self.current_theme_name = self.load_saved_theme()
        self.apply_theme(self.current_theme_name)

    def get_active_filepath(self):
        """Returns the target file path for whichever view is currently active."""
        mapping = {
            "notes": getattr(self, "note_file", None),
            "todo": getattr(self, "todo_file", None),
            "cal": getattr(self, "cal_notes_file", None),
            "calc": getattr(self, "calc_history_file", None),
        }
        return mapping.get(self.current_view)

    def save_file(self, event=None):
        """Saves the contents of the currently active pane to its corresponding file."""
        text_widget = self.get_active_text_widget()
        file_path = self.get_active_filepath()

        if text_widget and file_path:
            content = text_widget.get("1.0", tk.END)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            # Optional: Re-apply link styling after save
            if hasattr(self, "apply_link_parsing"):
                self.apply_link_parsing(text_widget)
                
            print(f"Successfully saved {self.current_view} pane to {file_path}")

    def get_active_text_widget(self):
        """Returns whichever text widget belongs to the current view."""
        if self.current_view == "notes":
            return self.text_area
        elif self.current_view == "todo":
            return self.todo_text_area
        elif self.current_view == "cal":
            return self.cal_notes_text
        elif self.current_view == "calc":
            return self.calc_history_text
        return None

    # def get_active_filepath(self):
    #     """Returns the file path belonging to the currently active view."""
    #     if self.current_view == "notes":
    #         return self.notes_file  # or self.notes_path
    #     elif self.current_view == "todo":
    #         return self.todo_file
    #     elif self.current_view == "cal":
    #         return self.cal_notes_file
    #     elif self.current_view == "calc":
    #         return self.calc_history_file
    #     return None


    def show_insert_menu(self, event=None):
        """Displays the configured symbol menu directly below the active text area."""
        widget = self.get_active_text_widget()
        if not widget:
            return "break"
        # Call your base-level builder function passing root and the active widget lookup helper
        menu = create_symbol_menu_from_config(self.root, self.get_active_text_widget)
        # Post the menu at current mouse coordinates
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()
        menu.tk_popup(x, y)
        return "break"


    def bind_custom_commands(self):
        # custom_cmds = self.cfg.get_custom_commands()
        custom_cmds = get_custom_commands(self.cfg)
        for item in custom_cmds:
            raw_shortcut = item["shortcut"]
            cmd_str = item["command"]
            mode = item["mode"]
            cmd_title = item.get("title", "MyCompanion")
            cmd_geom = item.get("geometry", "")

            # Always normalize to a single, valid Tkinter sequence
            seq = normalize_tk_shortcut(raw_shortcut)

            try:
                # dbug(f"{cmd_str=}")
                self.root.bind(
                    seq,
                    lambda e, c=cmd_str, m=mode, t=cmd_title, g=cmd_geom: (
                    self.run_command(c, open_in=m, title=t, geometry=g),  
                    "break",
                )[1],
                    # lambda e, c=cmd_str, m=mode, t=cmd_title: ( self.run_command(c, open_in=m, title=t), "break",)[1],
                )
            except tk.TclError as err:
                print(f"Warning: Failed to bind custom shortcut '{seq}': {err}")
                

    def view_config_file(self):
        self.config_viewer = ConfigViewerWindow(self.root, CONFIG_FILE, geometry="850x750", app=self)
        return "break"

    def load_saved_theme(self):
        # theme_name = cfg_get(self.cfg, "Theme", "name", "Dark / White (Default)")
        theme_name = self.cfg.get("Theme", {}).get("name", "Dark / White (Default)").strip()
        return theme_name if theme_name in THEMES else "Dark / White (Default)"

    def save_theme(self, theme_name):
        cfg_set(self.cfg, "Theme", "name", theme_name)

    def apply_theme(self, theme_name):
        self.current_theme_name = theme_name
        colors = THEMES[theme_name]
        self.save_theme(theme_name)

        # Header, Navigation, and Content Containers
        self.header_frame.config(bg=colors["header_bg"])
        self.nav_frame.config(bg=colors["nav_bg"])
        self.ai_frame.config(bg=colors["panel_bg"])
        self.notes_ctrl_frame.config(bg=colors["panel_bg"])
        self.calc_frame.config(bg=colors["bg"])
        self.calc_input_container.config(bg=colors["bg"])
        self.calc_history_header.config(bg=colors["bg"])
        self.cal_frame.config(bg=colors["bg"])
        self.cal_notes_header_frame.config(bg=colors["bg"])
        self.todo_ctrl_frame.config(bg=colors["panel_bg"])

        # Footer Button & Label Styling
        if hasattr(self, 'footer_btn'):
            self.footer_btn.config(
                bg=colors["nav_bg"],
                fg=colors["btn_fg"],
                activebackground=colors["nav_bg"],
                activeforeground=colors["btn_fg"],
                highlightbackground=colors["btn_fg"],
                highlightcolor=colors["btn_fg"]
            )
            self.status_label.config(bg=colors["nav_bg"], fg=colors["fg"])

        self.date_label.config(bg=colors["header_bg"], fg=colors["fg"])
        self.title_label.config(bg=colors["header_bg"], fg=colors["fg"])
        self.version_label.config(bg=colors["header_bg"], fg=colors["fg"])
        self.time_label.config(bg=colors["header_bg"], fg=colors["fg"])
        self.notes_lbl_widget.config(bg=colors["panel_bg"], fg=colors["fg"])
        self.todo_lbl_widget.config(bg=colors["panel_bg"], fg=colors["fg"])
        self.calc_label.config(bg=colors["bg"], fg=colors["fg"])
        self.calc_history_lbl.config(bg=colors["bg"], fg=colors["fg"])
        self.cal_notes_label.config(bg=colors["bg"], fg=colors["fg"])

        for txt in (self.text_area, self.todo_text_area, self.cal_notes_text, self.cal_text, self.calc_history_text):
            txt.config(bg=colors["bg"], fg=colors["fg"], insertbackground=colors["insert_bg"])

        self.calc_display.config(bg=colors["panel_bg"], fg=colors["fg"], insertbackground=colors["insert_bg"])
        self.ai_input.config(bg=colors["panel_bg"], fg=colors["fg"], insertbackground=colors["insert_bg"])

        def style_children(parent):
            for child in parent.winfo_children():
                if isinstance(child, tk.Button) and child != getattr(self, 'footer_btn', None):
                    child.config(
                        bg=colors["btn_bg"],
                        fg=colors["btn_fg"],
                        activebackground=colors["panel_bg"],
                        activeforeground=colors["fg"]
                    )
                elif isinstance(child, tk.Frame):
                    style_children(child)

        style_children(self.nav_frame)
        style_children(self.notes_ctrl_frame)
        style_children(self.calc_history_header)
        style_children(self.cal_notes_header_frame)
        style_children(self.todo_ctrl_frame)


    def open_theme_selector(self, event=None):
        win = tk.Toplevel(self.root)
        win.title("Select Theme")
        win.geometry("340x420")  # Made taller (420px height)
        win.attributes("-topmost", True)

        colors = THEMES[self.current_theme_name]
        win.config(bg=colors["bg"])

        lbl = tk.Label(
            win,
            text="Choose Application Theme:",
            bg=colors["bg"],
            fg=colors["fg"],
            font=("Monospace", 10, "bold"),
        )
        lbl.pack(pady=(10, 5))

        # Container frame for listbox + scrollbar
        list_frame = tk.Frame(win, bg=colors["bg"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        scrollbar = tk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            bg=colors["panel_bg"],
            activebackground=colors["btn_bg"],
            troughcolor=colors["bg"],
            bd=0,
            highlightthickness=0,
            relief=tk.FLAT,
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(
            list_frame,
            bg=colors["panel_bg"],
            fg=colors["fg"],
            selectbackground=colors["btn_bg"],
            selectforeground=colors["btn_fg"],
            font=("Monospace", 10),
            bd=0,
            highlightthickness=0,
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set,
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=listbox.yview)

        for theme in THEMES.keys():
            listbox.insert(tk.END, theme)

        # Highlight currently active theme in the listbox
        if self.current_theme_name in THEMES:
            idx = list(THEMES.keys()).index(self.current_theme_name)
            listbox.selection_set(idx)
            listbox.see(idx)

        def on_select(evt):
            sel = listbox.curselection()
            if sel:
                chosen = listbox.get(sel[0])
                self.apply_theme(chosen)
                colors_new = THEMES[chosen]

                # Update dialog components with new colors
                win.config(bg=colors_new["bg"])
                lbl.config(bg=colors_new["bg"], fg=colors_new["fg"])
                list_frame.config(bg=colors_new["bg"])
                listbox.config(
                    bg=colors_new["panel_bg"],
                    fg=colors_new["fg"],
                    selectbackground=colors_new["btn_bg"],
                    selectforeground=colors_new["btn_fg"],
                )
                scrollbar.config(
                    bg=colors_new["panel_bg"],
                    activebackground=colors_new["btn_bg"],
                    troughcolor=colors_new["bg"],
                )
                close_btn.config(
                    bg=colors_new["btn_bg"], fg=colors_new["btn_fg"]
                )

        listbox.bind("<<ListboxSelect>>", on_select)

        close_btn = tk.Button(
            win,
            text="Close",
            command=win.destroy,
            bg=colors["btn_bg"],
            fg=colors["btn_fg"],
            bd=0,
            padx=10,
            pady=4,
            relief=tk.FLAT,
        )
        close_btn.pack(pady=10)

        return "break"


    def apply_link_parsing(self, text_widget):
        for tag in text_widget.tag_names():
            if tag.startswith(("ext_", "file_", "wiki_")):
                text_widget.tag_delete(tag)

        content = text_widget.get("1.0", tk.END)

        # HTTP / HTTPS Links
        for idx, match in enumerate(re.finditer(r"https?://[^\s>\"']+", content)):
            tag_name = f"ext_{idx}"
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            url = match.group(0)

            text_widget.tag_config(tag_name, foreground="#3B82F6", underline=True)
            text_widget.tag_add(tag_name, start, end)
            text_widget.tag_bind(tag_name, "<Button-1>", lambda e, u=url: webbrowser.open(u))
            text_widget.tag_bind(tag_name, "<Enter>", lambda e: text_widget.config(cursor="hand2"))
            text_widget.tag_bind(tag_name, "<Leave>", lambda e: text_widget.config(cursor=""))

        # File Links - Route through open_or_create_file instead of open_file_subwindow
        for idx, match in enumerate(re.finditer(r"\[(.*?)\]\((file://.*?)\)", content)):
            tag_name = f"file_{idx}"
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            file_path = match.group(2).replace("file://", "")

            text_widget.tag_config(tag_name, foreground="#10B981", underline=True)
            text_widget.tag_add(tag_name, start, end)
            # Point to self.open_or_create_file here:
            text_widget.tag_bind(tag_name, "<Button-1>", lambda e, p=file_path: self.open_or_create_file(p))
            text_widget.tag_bind(tag_name, "<Enter>", lambda e: text_widget.config(cursor="hand2"))
            text_widget.tag_bind(tag_name, "<Leave>", lambda e: text_widget.config(cursor=""))


    def open_or_create_file(self, file_path):
        path = Path(file_path).expanduser().resolve()
        
        # 1. Handle missing file creation safely upfront
        try:
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
        except Exception as err:
            messagebox.showerror("File Error", f"Could not create file:\n{err}")
            return

        # 2. Route Markdown files to e ifxternal editor if configured
        if path.suffix.lower() in [".md", ".markdown"]:
            md_editor = cfg_get(self.cfg, "Settings", "md_editor")
            if md_editor:
                # Ask the user if they want to use the configured markdown editor
                msg = f"Open '{path.name}' in external editor ({md_editor})?"
                if messagebox.askyesno("Open External Editor", msg):
                    # dbug(f"{md_editor=}")
                    self.open_raw(f"{md_editor} {path}")
                    return  # Skip internal editor window completely!
                
        # 3. Default fallback for non-md files or when md_editor is blank
        self.open_file_subwindow(path)

    def open_file_subwindow(self, file_path, read_only=False):
        path = Path(file_path)
        try:
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
        except Exception as err:
            messagebox.showerror("File Error", f"Could not create file:\n{err}")
            return

        win = tk.Toplevel(self.root)
        win.title(f"{'[READ-ONLY] ' if read_only else ''}{path.name}")
        win.geometry("600x550")
        win.attributes("-topmost", True)

        colors = THEMES[self.current_theme_name]
        win.configure(bg=colors["bg"])
        self.sub_windows.append(win)
        win.protocol("WM_DELETE_WINDOW", lambda: (self.sub_windows.remove(win), win.destroy()))

        # Top Bar containing Path Header
        top_bar = tk.Frame(win, bg=colors["panel_bg"], pady=4, padx=10)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        path_label = tk.Label(top_bar, text=str(path), bg=colors["panel_bg"], fg=colors["fg"], font=("Monospace", 9, "bold"), anchor="w")
        path_label.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Main Text Editor Area
        editor = tk.Text(
            win, wrap=tk.WORD, bg=colors["bg"], fg=colors["fg"],
            insertbackground=colors["insert_bg"], font=("Monospace", 11),
            bd=0, padx=10, pady=10
        )
        editor.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        try:
            with open(path, "r", encoding="utf-8") as f:
                editor.insert("1.0", f.read())
        except Exception as err:
            messagebox.showerror("File Error", f"Could not read file:\n{err}")

        # Link Parsing / Highlighting
        if not read_only:
            editor.bind("<KeyRelease>", lambda e: self.apply_link_parsing(editor))
        self.apply_link_parsing(editor)

        # Disable editing if read_only is True
        if read_only:
            editor.config(state="disabled")

        # Bottom Control Frame (Status + Action Buttons)
        ctrl_frame = tk.Frame(win, bg=colors["panel_bg"], pady=6, padx=10)
        ctrl_frame.pack(side=tk.BOTTOM, fill=tk.X)

        status_lbl = tk.Label(
            ctrl_frame,
            text="Read-Only Mode" if read_only else "",
            bg=colors["panel_bg"],
            fg="#4ec9b0",
            font=("Monospace", 9)
        )
        status_lbl.pack(side=tk.LEFT, padx=5)

        def save_file(event=None):
            if read_only or not path.exists():
                return "break"
            try:
                content = editor.get("1.0", tk.END).strip()
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                status_lbl.config(text="Saved!")
                win.after(1500, lambda: status_lbl.config(text=""))
            except Exception as err:
                messagebox.showerror("Save Error", f"Could not save file:\n{err}")
            return "break"

        win.protocol("WM_DELETE_WINDOW", lambda: (self.sub_windows.remove(win), win.destroy()))
        editor.bind("<Control-s>", save_file)
        editor.bind("<Control-S>", save_file)

        # Bottom Right Action Buttons
        if not read_only:
            save_btn = tk.Button(
                ctrl_frame, text="Save (Ctrl-S)", command=save_file, 
                bg=colors["btn_bg"], fg=colors["btn_fg"], bd=0, padx=10, pady=3
            )
            save_btn.pack(side=tk.RIGHT, padx=5)

            def delete_file():
                confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {path.name}?", parent=win)
                if confirm:
                    try:
                        if path.exists():
                            path.unlink()
                        if win in self.sub_windows:
                            self.sub_windows.remove(win)
                        win.destroy()
                    except Exception as err:
                        messagebox.showerror("Delete Error", f"Could not delete file:\n{err}", parent=win)

            delete_btn = tk.Button(
                ctrl_frame, text="Delete Note", command=delete_file,
                bg="#8b0000", fg="#fff", activebackground="#a00000", activeforeground="#fff",
                bd=0, padx=10, pady=3, font=("Monospace", 8, "bold")
            )
            delete_btn.pack(side=tk.RIGHT, padx=5)
    # ### EOB def open_file_subwindow(self, file_path, read_only=False): ### #


    def save_selected_as(self, event=None):
        widget = None
        if self.current_view == "notes":
            widget = self.text_area
        elif self.current_view == "todo":
            widget = self.todo_text_area
        elif self.current_view == "cal":
            widget = self.cal_notes_text
        elif self.current_view == "calc":
            widget = self.calc_history_text

        if not widget:
            return "break"

        try:
            selected_text = widget.get("sel.first", "sel.last")
        except tk.TclError:
            messagebox.showinfo("Save Selected Text", "Please select text first before saving.")
            return "break"

        if not selected_text.strip():
            messagebox.showinfo("Save Selected Text", "Selected text is empty.")
            return "break"

        file_path = filedialog.asksaveasfilename(
            title="Save Selected Text As...",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(selected_text)
                messagebox.showinfo("Success", f"Saved selection to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")

        return "break"

    def open_in_vim(self, file_path, text_widget):
        text_widget.config(state=tk.NORMAL)
        content = text_widget.get("1.0", tk.END).strip()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        self.root.attributes("-topmost", False)
        self.root.update_idletasks()
        try:
            main_x = self.root.winfo_x()
            main_y = self.root.winfo_y()
        except Exception:
            main_x, main_y = 100, 100

        offset_x = main_x + 40
        offset_y = max(30, main_y - 120)

        editor = os.environ.get("EDITOR", "vim")
        terminals = [
            ["xterm", "-geometry", f"82x28+{offset_x}+{offset_y}", "-e"],
            ["x-terminal-emulator", "-e"],
            ["gnome-terminal", "--"],
            ["konsole", "-e"],
            ["xfce4-terminal", "-e"]
        ]

        def launch_and_wait(ed, terms):
            proc = None
            launched = False
            for term_cmd in terms:
                try:
                    proc = subprocess.Popen(term_cmd + [ed, str(file_path)])
                    launched = True
                    break
                except (FileNotFoundError, Exception):
                    continue

            if not launched:
                try:
                    proc = subprocess.Popen([ed, str(file_path)])
                    launched = True
                except Exception as e:
                    print(f"Error launching editor {ed}: {e}")
                    self.root.after(0, lambda: self.root.attributes("-topmost", True))
                    return

            if proc:
                proc.wait()

            def cleanup():
                self._reload_widget_content(file_path, text_widget)
                self.root.attributes("-topmost", True)
                self.root.lift()

            self.root.after(0, cleanup)

        threading.Thread(target=launch_and_wait, args=(editor, terminals), daemon=True).start()

    def _reload_widget_content(self, file_path, text_widget):
        text_widget.config(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                text_widget.insert("1.0", f.read())
        self.apply_link_parsing(text_widget)


    def handle_tab_shortcut(self, view_name):
        self.switch_view(view_name)
        return "break"

    def toggle_ai_bar(self, force_state=None):
        if force_state is not None:
            target_state = force_state
        else:
            target_state = not self.ai_visible

        current_geometry = self.root.geometry().split("+")[0]
        w, h = map(int, current_geometry.split("x"))

        if not target_state and self.ai_visible:
            self.ai_frame.pack_forget()
            self.ai_visible = False
            self.root.geometry(f"{w}x{max(400, h - 55)}")
        elif target_state and not self.ai_visible:
            self.content_frame.pack_forget()
            self.ai_frame.pack(side=tk.BOTTOM, fill=tk.X)
            self.content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            self.ai_visible = True
            self.root.geometry(f"{w}x{h + 55}")
            self.ai_input.focus_set()

        return "break"

    def send_to_gemini_click(self, event=None):
        query = self.ai_input.get().strip()
        if not query:
            return
        self.ai_input.delete(0, tk.END)
        threading.Thread(target=self._fetch_gemini_response, args=(query,), daemon=True).start()

    def _fetch_gemini_response(self, query):
        try:
            from google import genai
            client = genai.Client()
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=query
            )
            answer = response.text
        except Exception as e:
            answer = f"Error calling Gemini API:\n{str(e)}"

        self.root.after(0, lambda: self.open_response_window(query, answer))

    def open_response_window(self, query, answer):
        win = tk.Toplevel(self.root)
        win.title(f"Gemini: {query[:35]}...")
        win.geometry("550x450")
        win.attributes("-topmost", True)

        colors = THEMES[self.current_theme_name]
        win.configure(bg=colors["bg"])
        self.sub_windows.append(win)
        win.protocol("WM_DELETE_WINDOW", lambda: (self.sub_windows.remove(win), win.destroy()))

        q_label = tk.Label(win, text=f"Q: {query}", bg=colors["panel_bg"], fg=colors["fg"], font=("Monospace", 9, "bold"), anchor="w", padx=10, pady=6)
        q_label.pack(side=tk.TOP, fill=tk.X)

        text_box = tk.Text(win, wrap=tk.WORD, bg=colors["bg"], fg=colors["fg"], insertbackground=colors["insert_bg"], font=("Monospace", 10), bd=0, padx=10, pady=10)
        text_box.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        text_box.insert("1.0", answer)
        text_box.config(state=tk.DISABLED, exportselection=True)

        ctrl_frame = tk.Frame(win, bg=colors["panel_bg"], pady=6, padx=10)
        ctrl_frame.pack(side=tk.BOTTOM, fill=tk.X)

        def copy_text():
            win.clipboard_clear()
            win.clipboard_append(text_box.get("1.0", tk.END).strip())
            copy_btn.config(text="Copied!")
            win.after(1500, lambda: copy_btn.config(text="Copy"))

        copy_btn = tk.Button(ctrl_frame, text="Copy", command=copy_text, bg=colors["btn_bg"], fg=colors["btn_fg"], bd=0, padx=10, pady=4)
        copy_btn.pack(side=tk.LEFT, padx=5)

        editable = [False]
        def toggle_edit():
            if editable[0]:
                text_box.config(state=tk.DISABLED)
                edit_btn.config(text="Edit")
                editable[0] = False
            else:
                text_box.config(state=tk.NORMAL)
                edit_btn.config(text="Lock")
                editable[0] = True

        edit_btn = tk.Button(ctrl_frame, text="Edit", command=toggle_edit, bg=colors["btn_bg"], fg=colors["btn_fg"], bd=0, padx=10, pady=4)
        edit_btn.pack(side=tk.LEFT, padx=5)

        close_btn = tk.Button(ctrl_frame, text="Close", command=win.destroy, bg="#510", fg="#fff", bd=0, padx=10, pady=4)
        close_btn.pack(side=tk.RIGHT, padx=5)

    def update_header_clock(self):
        now = datetime.datetime.now()
        current_date = now.date()

        if self.last_checked_date != current_date:
            self.last_checked_date = current_date
            self.load_calendar()

        date_str = now.strftime("%Y-%m-%d (%b %d, %a)")
        time_str = now.strftime("%I:%M %p").lower().lstrip("0")

        self.date_label.config(text=date_str)
        self.time_label.config(text=time_str)

        self.root.after(60000, self.update_header_clock)

    def switch_view(self, view_name):
        self.notes_frame.pack_forget()
        self.calc_frame.pack_forget()
        self.cal_frame.pack_forget()
        self.todo_frame.pack_forget()

        if view_name == "notes":
            self.notes_frame.pack(fill=tk.BOTH, expand=True)
            self.text_area.focus_set()
            self.current_view = "notes"
        elif view_name == "calc":
            self.calc_frame.pack(fill=tk.BOTH, expand=True)
            self.calc_display.focus_set()
            self.current_view = "calc"
        elif view_name == "cal":
            self.cal_frame.pack(fill=tk.BOTH, expand=True)
            self.current_view = "cal"
        elif view_name == "todo":
            self.todo_frame.pack(fill=tk.BOTH, expand=True)
            self.todo_text_area.focus_set()
            self.current_view = "todo"

    def evaluate_calc(self, event):
        expr = self.calc_display.get().strip()
        if not expr:
            return
        
        try:
            # 1. Try solving as a proportion string first
            sentinel = object()
            result = solve_proportion(expr, default=sentinel)
            
            # 2. If it wasn't a proportion string, fall back to standard math eval
            if result is sentinel:
                math_globals = {
                    "__builtins__": None,
                    # Common built-in functions
                    "abs": abs, "round": round, "sum": sum, "min": min, "max": max,
                    # Trig functions & angle conversion
                    "sin": math.sin, "cos": math.cos, "tan": math.tan,
                    "asin": math.asin, "acos": math.acos, "atan": math.atan,
                    "radians": math.radians, "degrees": math.degrees,
                    # Common math functions & constants
                    "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
                    "factorial": math.factorial,
                    "pi": math.pi, "e": math.e
                }
                result = eval(expr, math_globals, {})
            
            # Format float results nicely (e.g., 96.33333333333333 -> 96.3333 or clean integer if whole)
            if isinstance(result, float):
                result = int(result) if result.is_integer() else round(result, 4)
            
            result_str = f"= {result}"
            self.calc_result.config(text=result_str, fg="#4ec9b0")

            history_entry = f"{expr}  -->  {result}\n"
            was_disabled = str(self.calc_history_text.cget("state")) == tk.DISABLED
            if was_disabled:
                self.calc_history_text.config(state=tk.NORMAL)

            self.calc_history_text.insert("1.0", history_entry)
            self.apply_link_parsing(self.calc_history_text)

            if was_disabled:
                self.calc_history_text.config(state=tk.DISABLED)

            self.calc_display.delete(0, tk.END)
        except Exception:
            self.calc_result.config(text="Invalid expression", fg="#f44747")


    def load_calendar(self):
        now = datetime.datetime.now()
        next_month_date = now.replace(day=28) + datetime.timedelta(days=4)

        cal = calendar.TextCalendar(calendar.SUNDAY)
        current_lines = cal.formatmonth(now.year, now.month).splitlines()
        next_lines = cal.formatmonth(next_month_date.year, next_month_date.month).splitlines()

        max_lines = max(len(current_lines), len(next_lines))
        current_lines += [""] * (max_lines - len(current_lines))
        next_lines += [""] * (max_lines - len(next_lines))

        combined_lines = []
        for cur_l, nxt_l in zip(current_lines, next_lines):
            combined_lines.append(f"{cur_l:<30}    {nxt_l}")

        final_cal_str = "\n".join(combined_lines)

        self.cal_text.config(state=tk.NORMAL)
        self.cal_text.delete("1.0", tk.END)
        self.cal_text.insert("1.0", final_cal_str)

        self.cal_text.tag_config("today", foreground="#ffe600", background="#333333", font=("Monospace", 10, "bold"))

        today_str = str(now.day)
        for line_num, line_text in enumerate(current_lines, start=1):
            match = re.search(r'\b' + re.escape(today_str) + r'\b', line_text)
            if match:
                start_pos = f"{line_num}.{match.start()}"
                end_pos = f"{line_num}.{match.end()}"
                self.cal_text.tag_add("today", start_pos, end_pos)
                break

        self.cal_text.config(state=tk.DISABLED)

    def load_notes(self):
        if os.path.exists(self.note_file):
            with open(self.note_file, "r", encoding="utf-8") as f:
                self.text_area.insert("1.0", f.read())
        self.apply_link_parsing(self.text_area)

    def load_cal_notes(self):
        if os.path.exists(self.cal_notes_file):
            with open(self.cal_notes_file, "r", encoding="utf-8") as f:
                self.cal_notes_text.insert("1.0", f.read())
        self.apply_link_parsing(self.cal_notes_text)

    def load_calc_history(self):
        if os.path.exists(self.calc_history_file):
            with open(self.calc_history_file, "r", encoding="utf-8") as f:
                self.calc_history_text.insert("1.0", f.read())
        self.apply_link_parsing(self.calc_history_text)

    def load_todo(self):
        if os.path.exists(self.todo_file) and os.path.getsize(self.todo_file) > 0:
            with open(self.todo_file, "r", encoding="utf-8") as f:
                self.todo_text_area.insert("1.0", f.read())
        else:
            default_todo = (
                "=== High Priority ===\n\n"
                "=== Medium Priority ===\n\n"
                "=== Low Priority ===\n"
            )
            self.todo_text_area.insert("1.0", default_todo)
        self.apply_link_parsing(self.todo_text_area)

    def save_notes(self):
        # if not self.use_vim:
        with open(self.note_file, "w", encoding="utf-8") as f:
            f.write(self.text_area.get("1.0", tk.END).strip())
        with open(self.cal_notes_file, "w", encoding="utf-8") as f:
            f.write(self.cal_notes_text.get("1.0", tk.END).strip())
        with open(self.todo_file, "w", encoding="utf-8") as f:
            f.write(self.todo_text_area.get("1.0", tk.END).strip())
        with open(self.calc_history_file, "w", encoding="utf-8") as f:
            f.write(self.calc_history_text.get("1.0", tk.END).strip())

    def toggle_window(self):
        self.root.after(0, self._perform_toggle)

    def _perform_toggle(self):
        if self.is_visible:
            self.hide_window()
        else:
            self.show_window()

    def show_window(self):
        self.sub_windows = [w for w in self.sub_windows if w.winfo_exists()]

        if self.current_view in ("notes", "calc"):
            self.save_notes()

        self.root.update_idletasks()
        cfg_set(self.cfg, "Window", "geometry", self.root.geometry())

        self.root.deiconify()
        for win in self.sub_windows:
            win.deiconify()

        self.root.lift()
        self.root.focus_force()

        if self.ai_visible:
            self.ai_input.focus_set()
        elif self.current_view == "notes":
            self.text_area.focus_set()
        elif self.current_view == "calc":
            self.calc_display.focus_set()
        elif self.current_view == "todo":
            self.todo_text_area.focus_set()

        self.is_visible = True

    def hide_window(self):
        # In TSR mode (--toggle), withdraw to background
        if self.doc_args.get("--toggle") and not is_wayland():
            self.root.withdraw()
            self.sub_windows = [w for w in self.sub_windows if w.winfo_exists()]
            for win in self.sub_windows:
                win.withdraw()
            self.is_visible = False
        else:
            # In standard window mode, closing/hiding quits the app cleanly
            self.quit_app()

    def quit_app(self):
        self.save_notes()
        cfg_set(self.cfg, "Window", "geometry", self.root.geometry())
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        if os.path.exists(LOCK_FILE):
            try:
                os.remove(LOCK_FILE)
            except OSError:
                pass
        self.root.quit()
        sys.exit(0)

    def run(self):
        # Only start pynput global hotkeys if --toggle was requested and not on Wayland
        if self.doc_args.get("--toggle") and not is_wayland():
            try:
                from pynput import keyboard
                self.hotkey_listener = keyboard.GlobalHotKeys({
                    '<ctrl>+<space>': self.toggle_window
                })
                self.hotkey_listener.start()
            except ImportError:
                print("Warning: pynput is required for TSR hotkey mode.")
                print("Install it with: pip install pynput")

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit_app()


    def show_help_legend(self, event=None):
        win = tk.Toplevel(self.root)
        win.title("MyCompanion Shortcuts & Help")
        win.geometry("520x400")
        win.attributes("-topmost", True)

        colors = THEMES[self.current_theme_name]
        win.configure(bg=colors["bg"])
        self.sub_windows.append(win)
        win.protocol("WM_DELETE_WINDOW", lambda: (self.sub_windows.remove(win), win.destroy()))

        # 1. Header (Top)
        hdr = tk.Label(
            win, text="Keyboard Shortcuts & Syntax",
            bg=colors["header_bg"], fg=colors["fg"],
            font=("Monospace", 10, "bold"), pady=6
        )
        hdr.pack(side=tk.TOP, fill=tk.X)

        # 2. Control Frame & Close Button (Bottom)
        ctrl_frame = tk.Frame(win, bg=colors["panel_bg"], pady=6, padx=10)
        ctrl_frame.pack(side=tk.BOTTOM, fill=tk.X)
        close_btn = tk.Button(
            ctrl_frame, text="Close", command=win.destroy,
            bg=colors["btn_bg"], fg=colors["btn_fg"], bd=0, padx=12, pady=3
        )
        close_btn.pack(side=tk.RIGHT)

        # 3. Text Widget (Middle - Packed ONCE so it fills remaining space between hdr and ctrl_frame)
        help_text = tk.Text(
            win, wrap=tk.WORD, bg=colors["bg"], fg=colors["fg"],
            insertbackground=colors["insert_bg"], font=("Monospace", 9),
            bd=0, padx=12, pady=10
        )
        help_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        content = (
            "GLOBAL SHORTCUTS:\n"
            "  Ctrl-Space   : Toggle main window visibility (If --toggle option was invoked)\n"
            "  Ctrl-1..4    : Switch tabs (1:Notes, 2:Calc, 3:Cal, 4:Todo)\n"
            "  Ctrl-a       : Toggle Gemini AI bar\n"
            "  Alt-c        : View configuration file\n"
            "  Ctrl-e       : If [Settings] editor is configured then used editor to open current file\n"
            "  Ctrl-r       : Run command dialog\n"
            "  Ctrl-t       : Open Theme Selector\n"
            "  Ctrl-h / ?   : Show this help window\n"
            "  Ctrl-s       : Save selected text to file\n"
            "  Ctrl-q       : Quit application\n\n"
            "LINK FORMATTING:\n"
            "  https://...                    : Open URL in web browser\n"
            "  [Label](file:///path/to/file)  : Open path in sub-window editor\n"
        )
        content += "\nCONFIG SHORTCUTS:\n"

        try:
            if hasattr(self, 'cfg') and self.cfg:
                if hasattr(self.cfg, 'get_custom_commands'):
                    commands = self.cfg.get_custom_commands()
                elif isinstance(self.cfg, dict):
                    commands = []
                else:
                    commands = []
            else:
                commands = []

            if commands:
                for item in commands:
                    shortcut = item.get("shortcut", "")
                    title = item.get("title") or item.get("command", "")
                    content += f"  {shortcut:<12} : {title}\n"
            else:
                content += "  (No custom commands defined in configuration)\n"
        except Exception as e:
            dbug(f"ERROR during config shortcut processing: {e}")

        content += "\n"

        try:
            help_text.config(state=tk.NORMAL)
            help_text.insert("1.0", content)
            help_text.config(state=tk.DISABLED)
        except Exception as e:
            dbug(f"ERROR during text insertion/configuration: {e}")

        return "break"
    # ### EOB def show_help_legend(...) ### #



    def open_raw(self, cmd_str):
        """Executes a command string directly in a background shell without interference."""
        # dbug(f"{cmd_str=}")
        try:
            subprocess.Popen(cmd_str, shell=True, stdout=None, stderr=None, stdin=None)
        except Exception as e:
            print(f"Failed to execute raw command '{cmd_str}': {e}")


    def open_in_terminal( self, cmd_str, title=None, geometry="180x40", font=None, hold_mode="active", **kwargs,):
        """Launches a command string inside an available terminal emulator.
        Args:
            cmd_str (str): The bash command/script to execute.
            title (str, optional): Title for the terminal window.
            geometry (str, optional): Window dimensions e.g. "180x40". Defaults to
              "180x40".
            font (str, optional): Terminal font override string (reserved for future
              use).
            hold_mode (str, optional): Strategy after process finishes:
                - "active": keeps interactive shell alive with 'exec bash --norc'.
                - "ask": prompts user to press Enter to close the window.
                - "none": exits window immediately upon completion.
        """
        win_title = title or "MyCompanion Task"
        geom = geometry or "180x40"

        # 1. Determine shell persistence strategy
        if hold_mode == "ask":
            suffix = ' ; echo ; read -r -p "Press Enter to exit..."'
        elif hold_mode == "active":
            suffix = ' ; echo "Please use Ctrl-D to exit" ; exec bash --norc'
        else:  # "none" or default
            suffix = ""

        full_shell_cmd = f"{cmd_str}{suffix}"

        # Parse geometry columns & rows for terminals needing explicit flags
        cols, rows = ( geom.split("x") if "x" in geom else ("180", "40"))

        # 2. Build explicit list of terminal options
        terminals = [
            ("kitty", ["kitty", "-o", f"initial_window_width={cols}c", "-o", f"initial_window_height={rows}c", "--title", win_title, "bash", "-c", full_shell_cmd, ],),
            ("xterm", [ "xterm", "-geometry", geom, "-T", win_title, "-e", "bash", "-c", full_shell_cmd, ],),
            ("xfce4-terminal", [ "xfce4-terminal", f"--geometry={geom}", "-T", win_title, "-x", "bash", "-c", full_shell_cmd, ],),
            ("ghostty", [ "ghostty", f"--title={win_title}", "-e", "bash", "-c", full_shell_cmd, ],),
        ]

        # Handle font overrides if specified in the future
        if font:
            # Example font hook for xterm / kitty
            pass

        # 3. Execution loop
        launched = False
        for name, term_cmd_l in terminals:
            try:
                # dbug(f"Attempting launch with {name}: {term_cmd_l=}")
                subprocess.Popen(term_cmd_l)
                launched = True
                break  # Exit loop as soon as one binary successfully launches
            except (FileNotFoundError, PermissionError):
                continue
            except Exception as err:
                # dbug(f"Failed launching {name}: {err}")
                continue

        if not launched:
            print("Warning: No compatible terminal emulator found.")

        return launched


    def run_command(self, cmd_str, open_in="window", title=None, geometry=""):
        # dbug(f"{cmd_str=} {open_in=}")
        cmd_str = cmd_str.strip()
        if not cmd_str:
            return

        if open_in == "ask":
            self.prompt_run_command(initial_cmd=cmd_str)
            return

        if open_in == "raw":
            self.open_raw(cmd_str)

        elif open_in == "terminal":
            geom = geometry or cfg_get(self.cfg, "Window", "geometry", "180x40")
            self.open_in_terminal(cmd_str, title=title, geometry=geom)

        elif open_in == "silent":
            subprocess.Popen( cmd_str, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)

        else:
            # Standard 'window' mode output capture thread
            def _exec():
                proc = subprocess.run(cmd_str, shell=True, capture_output=True, text=True)
                output = proc.stdout if proc.stdout else proc.stderr
                if not output.strip():
                    output = f"[Command completed with exit code {proc.returncode}]"
                self.root.after(0, lambda: self.show_command_output(cmd_str, output))

            threading.Thread(target=_exec, daemon=True).start()


    def prompt_run_command(self, event=None, initial_cmd=""):
        win = tk.Toplevel(self.root)
        win.title("Run Command")
        win.geometry("480x140")
        win.attributes("-topmost", True)

        colors = THEMES[self.current_theme_name]
        win.configure(bg=colors["bg"], padx=12, pady=10)
        self.sub_windows.append(win)
        win.protocol("WM_DELETE_WINDOW", lambda: (self.sub_windows.remove(win), win.destroy()))

        lbl = tk.Label(
            win, text="Enter Command:",
            bg=colors["bg"], fg=colors["fg"],
            font=("Monospace", 9, "bold")
        )
        lbl.pack(anchor=tk.W)

        entry = tk.Entry(
            win, bg=colors["panel_bg"], fg=colors["fg"],
            insertbackground=colors["insert_bg"],
            font=("Monospace", 10), bd=1
        )
        entry.pack(fill=tk.X, pady=6)
        if initial_cmd:
            entry.insert(0, initial_cmd)
        entry.focus_set()

        mode_frame = tk.Frame(win, bg=colors["bg"])
        mode_frame.pack(fill=tk.X, pady=4)

        mode_var = tk.StringVar(value="window")

        modes = [
            ("Window (Output)", "window"),
            ("Terminal (TTY)", "terminal"),
            ("Silent", "silent"),
        ]

        for text, mode_val in modes:
            rb = tk.Radiobutton(
                mode_frame, text=text, value=mode_val, variable=mode_var,
                bg=colors["bg"], fg=colors["fg"],
                selectcolor=colors["panel_bg"],
                activebackground=colors["bg"], activeforeground=colors["fg"],
                font=("Monospace", 8)
            )
            rb.pack(side=tk.LEFT, padx=6)

        def _on_submit(e=None):
            cmd = entry.get().strip()
            selected_mode = mode_var.get()
            win.destroy()
            if win in self.sub_windows:
                self.sub_windows.remove(win)
            if cmd:
                self.run_command(cmd, open_in=selected_mode)

        entry.bind("<Return>", _on_submit)
        entry.bind("<Escape>", lambda e: win.destroy())
        return "break"

    def show_command_output(self, cmd_str, output_text):

        def clean_ansi(text):
            import re
            import unicodedata

            vt100_map = str.maketrans({
                'q': '-', 'x': '|', 'l': '+', 'k': '+',
                'm': '+', 'j': '+', 't': '+', 'u': '+',
                'v': '+', 'w': '+', 'n': '+'
            })

            def replace_vt100(match):
                return match.group(1).translate(vt100_map)

            text = re.sub(r'\x1B\(0(.*?)(?:\x1B\([ABK]|$)', replace_vt100, text, flags=re.DOTALL)
            text = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', text)
            text = re.sub(r'\x1B[\(\)][0ABK]', '', text)

            box_chars = str.maketrans({
                '┌': '+', '┐': '+', '└': '+', '┘': '+',
                '├': '+', '┤': '+', '┬': '+', '┴': '+',
                '┼': '+', '─': '-', '│': '|',
                '═': '=', '║': '|', '╔': '+', '╗': '+',
                '╚': '+', '╝': '+', '╠': '+', '╣': '+',
                '╦': '+', '╩': '+', '╬': '+',
                '╴': '-', '╵': '|', '╶': '-', '╷': '|',
                '━': '-', '┃': '|', '┏': '+', '┓': '+',
                '┗': '+', '┛': '+', '┣': '+', '┫': '+'
            })
            text = text.translate(box_chars)

            clean_chars = []
            for char in text:
                code = ord(char)
                if 0xFE00 <= code <= 0xFE0F:
                    continue

                is_symbol = (
                    (0x2600 <= code <= 0x26FF) or
                    (0x2700 <= code <= 0x27BF) or
                    (0x1F300 <= code <= 0x1F5FF) or
                    (0x1F600 <= code <= 0x1F6FF) or
                    unicodedata.east_asian_width(char) in ('W', 'F')
                )

                if is_symbol:
                    clean_chars.append(' ')
                else:
                    clean_chars.append(char)

            return "".join(clean_chars)

        win = tk.Toplevel(self.root)
        win.title(f"Output: {cmd_str}")
        win.geometry("640x400")
        win.attributes("-topmost", True)

        colors = THEMES[self.current_theme_name]
        win.configure(bg=colors["bg"])
        self.sub_windows.append(win)
        win.protocol("WM_DELETE_WINDOW", lambda: (self.sub_windows.remove(win), win.destroy()))

        txt_frame = tk.Frame(win, bg=colors["bg"])
        txt_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        v_scroll = tk.Scrollbar(txt_frame, orient=tk.VERTICAL)
        h_scroll = tk.Scrollbar(txt_frame, orient=tk.HORIZONTAL)

        txt = tk.Text(
            txt_frame, wrap=tk.NONE, bg=colors["bg"], fg=colors["fg"],
            font=("Monospace", 9), bd=0,
            yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set
        )

        v_scroll.config(command=txt.yview)
        h_scroll.config(command=txt.xview)

        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        cleaned_output = clean_ansi(output_text)

        txt.insert("1.0", cleaned_output)
        txt.config(state=tk.DISABLED)
    # ### EOB class MiniSidekick ### #


if __name__ == "__main__":
    args = docopt(__doc__, version=VERSION)

    # Set the global DEBUG flag dynamically from CLI flag
    if args.get("--debug"):
        DEBUG = True
        import inspect  # Only loaded into memory when debugging

    start_ai = args.get("--ai", False)
    # use_vim = args.get("--vim", False)

    ensure_daemon(args)

    app = MiniSidekick(start_with_ai=start_ai, doc_args=args)
    app.run()
