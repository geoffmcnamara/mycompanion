#!/usr/bin/env python3
"""
=======================
     mycompanion.py
=======================
Usage:
    mycompanion.py [--ai] [--vim] [--log] [--debug]
    mycompanion.py (-h | --help)

Options:
    -h --help   Show help and storage paths.
    --ai        Start with AI bar open.
    --vim       Enable external Vim editing.
    -l --log    Log stdout/stderr to mycompanion.log.
    -d --debug  Enable debug output and run in foreground.

Shortcuts:
    Ctrl-Space  Toggle window visibility
    Ctrl-1..4   Switch tabs (1:Notes, 2:Calc, 3:Cal, 4:Todo)
    Ctrl-a      Toggle AI bar
    Alt-c      View config file
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
from pynput import keyboard
import subprocess
import calendar
import datetime
import threading
import traceback
from pathlib import Path
from docopt import docopt
import re
import webbrowser

ROOTNAME = "mycompanion"
TITLE = "MyCompanion"
VERSION = "0.5.0a0"
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
    "Amber Phosphor": {
        "bg": "#120a00", "fg": "#ffb000", "header_bg": "#0a0500",
        "nav_bg": "#1f1200", "panel_bg": "#1f1200", "btn_bg": "#3d2400",
        "btn_fg": "#ffc107", "insert_bg": "#ffb000"
    }
}

DEFAULT_CONFIG = {
    "Window": {"geometry": "640x500"},
    "Settings": {"ai_mode": "false", "vim_mode": "false"},
    "Theme": {"name": "Dark / White (Default)"}
}


def dbug(msg: str) -> None:
    """Helper function to print debug messages only when DEBUG is enabled."""
    if DEBUG:
        frame = inspect.currentframe().f_back
        lineno = frame.f_lineno
        print(f"[DEBUG L{lineno}] {msg}")


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
        # if DEBUG:
            # for section in self.config.sections():
                # dbug(f"[{section}]")
                # for key, value in self.config.items(section):
                    # dbug(f"  {key} = {value}")
                # print()
            # pass
        self.load_config()
        # """--== SEP_LINE ==--""" #

    def load_config(self):
        if not self.filepath.exists():
            self.config.read_dict(DEFAULT_CONFIG)
            self.save_config()
        else:
            self.config.read(self.filepath, encoding="utf-8")
            # if DEBUG:
            #     # --- DEBUG REPR INSPECTION ---
            #     for sec in self.config.sections():
            #         for k, v in self.config.items(sec):
            #             dbug(f"READ -> [{sec}] {k} = {repr(v)}")
            #             print("v: " + v)
            #     # -----------------------------
            # dbug(f"{self.config.read(self.filepath, encoding='utf-8')=}")
            for section, keys in DEFAULT_CONFIG.items():
                # dbug(f"{section=} {keys=}")
                if not self.config.has_section(section):
                    self.config.add_section(section)
                for key, val in keys.items():
                    if not self.config.has_option(section, key):
                        self.config.set(section, key, val)
                        # dbug(f"{section=} {key=} {val=}")
        # --- SANITIZE GEOMETRY HERE ---
        # Adjust 'Window' or 'geometry' to match your actual config section/key names
        section_name = "Window" if self.config.has_section("Window") else "General"
        if self.config.has_option(section_name, "geometry"):
            raw_geom = self.config.get(section_name, "geometry")
            safe_geom = sanitize_geometry(raw_geom, min_w=200, min_h=200, default_w=600, default_h=400)
            self.config.set(section_name, "geometry", safe_geom)
        # """--== SEP_LINE ==--""" #

    def save_config(self):
        try:
            if self.filepath.exists():
                try:
                    disk_config = configparser.ConfigParser()
                    disk_config.read(self.filepath, encoding="utf-8")
                    for section in self.config.sections():
                        if not disk_config.has_section(section):
                            disk_config.add_section(section)
                        for key, val in self.config.items(section):
                            # dbug(f"{key=} {val=}")
                            disk_config.set(section, key, val)
                    self.config = disk_config
                except Exception as e:
                    print(f"Config load error: {e}")
            with open(self.filepath, "w", encoding="utf-8") as f:
                self.config.write(f)
        except Exception as e:
            print(f"Failed to save config: {e}")
        # """--== SEP_LINE ==--""" #
    def get_bool(self, section, key, default=False):
        # dbug(f"{section=} {key=}")
        try:
            return self.config.getboolean(section, key)
        except Exception:
            return default
        # """--== SEP_LINE ==--""" #
    def get_string(self, section, key, default=""):
        return self.config.get(section, key, fallback=default)
        # dbug(f"{section=} {key=}")
        # """--== SEP_LINE ==--""" #
    def set_value(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        # dbug(f"{section=} {key=} {str(value)=}")
        self.save_config()
        # """--== SEP_LINE ==--""" #
    def _get_flexible(self, section_proxy, keys, default=""):
        """ 
        Utility to retrieve the first matching key from a list of alias keys. 
        """
        for k in keys:
            if k in section_proxy:
                # dbug(f"{k=}")
                return section_proxy.get(k, "").strip()
        return default
        # """--== SEP_LINE ==--""" #
    def get_custom_commands(self):
        commands = []
        # Alias map for normalized execution modes
        VALID_MODES = {
            "window": "window",
            "win": "window",
            "terminal": "terminal",
            "term": "terminal",
            "silent": "silent",
            "quiet": "silent",
            "raw": "raw",
            "exec": "raw",
            "direct": "raw",
        }
        for section in self.config.sections():
            if section.startswith("cmd_") or section.startswith("command_"):
                sec = self.config[section]
                # """--== SEP_LINE ==--""" #
                # Key Aliases
                shortcut = self._get_flexible(sec, ["shortcut", "key", "bind"])
                cmd_str = self._get_flexible(sec, ["command", "cmd", "exec", "run"])
                # dbug(f"{cmd_str=} {sec=}")
                # """--== SEP_LINE ==--""" #
                if not shortcut or not cmd_str:
                    print(f"Warning: [{section}] missing required shortcut or command key. Skipping.")
                    continue
                    # """--== SEP_LINE ==--""" #
                # Mode resolution and validation
                raw_mode = self._get_flexible(sec, ["mode", "type"], default="window").lower()
                if raw_mode in VALID_MODES:
                    mode = VALID_MODES[raw_mode]
                else:
                    print(f"Warning: [{section}] unrecognized mode '{raw_mode}'. Defaulting to 'window'.")
                    mode = "window"
                    # """--== SEP_LINE ==--""" #
                title = self._get_flexible(sec, ["title", "name"], default=cmd_str)
                geometry = self._get_flexible(sec, ["geometry", "geom", "size"])
                # """--== SEP_LINE ==--""" #
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


def ensure_daemon(doc_args):
    global DEBUG
    script_path = os.path.abspath(__file__)
    python_exec = sys.executable

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

    # 2. Main launch handling
    if os.environ.get("SIDEKICK_DAEMON") != "1":
        # if DEBUG:
        #     print("[DEBUG] Running in foreground debug mode...", flush=True)
        #     os.environ["SIDEKICK_DAEMON"] = "1"
        #     return  # <-- Stops backgrounding and keeps terminal attached

        # Always print startup help and storage paths on launch
        print_help_and_paths()

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


# def ensure_daemon(doc_args):
#     script_path = os.path.abspath(__file__)
#     python_exec = sys.executable
# 
#     # Check lockfile
#     if os.path.exists(LOCK_FILE):
#         try:
#             with open(LOCK_FILE, "r", encoding="utf-8") as f:
#                 old_pid = int(f.read().strip())
#             os.kill(old_pid, 0)
#             print(f"MyCompanion is already running (PID {old_pid}).")
#             print("Use Ctrl-space to toggle the window.")
#             print(f"Lock file location: {LOCK_FILE}")
#             sys.exit(0)
#         except (ProcessLookupError, ValueError):
#             try:
#                 os.remove(LOCK_FILE)
#             except OSError:
#                 pass
#         except PermissionError:
#             sys.exit(0)
# 
#     # Parent CLI launcher process
#     if os.environ.get("SIDEKICK_DAEMON") != "1":
#         if DEBUG:
#             os.environ["SIDEKICK_DAEMON"] = "1"
#             return
# 
#         print_help_and_paths()
# 
#         new_env = os.environ.copy()
#         new_env["SIDEKICK_DAEMON"] = "1"
# 
#         args_list = [python_exec, script_path] + sys.argv[1:]
# 
#         popen_kwargs = {
#             "env": new_env,
#             "start_new_session": True,
#             "stdin": subprocess.DEVNULL,
#         }
# 
#         # Check docopt parsed arguments for --log
#         if doc_args.get("--log"):
#             log_fp = open(LOG_FILE, "a", encoding="utf-8")
#             popen_kwargs["stdout"] = log_fp
#             popen_kwargs["stderr"] = log_fp
#         elif DEBUG:
#             pass  # Leave terminal streams open for debugging
#         else:
#             popen_kwargs["stdout"] = subprocess.DEVNULL
#             popen_kwargs["stderr"] = subprocess.DEVNULL
# 
#         subprocess.Popen(args_list, **popen_kwargs)
#         sys.exit(0)
#     else:
#         # Child daemon process
#         with open(LOCK_FILE, "w", encoding="utf-8") as f:
#             f.write(str(os.getpid()))
#     # ### EOB def ensure_daemon(): ### #


# ----------------------------------------------------------------------
# MiniSidekick Class
# ----------------------------------------------------------------------
class MiniSidekick:
    def __init__(self, start_with_ai=False, use_vim=False, doc_args=None, **kwargs):
        self.cfg = ConfigManager()
        self.note_file = NOTES_FILE
        self.cal_notes_file = CAL_NOTES_FILE
        self.calc_history_file = CALC_NOTES_FILE
        self.todo_file = TODO_FILE

        self.use_vim = use_vim or self.cfg.get_bool("Settings", "vim_mode", False)
        # self.enable_ai = start_with_ai
        self.enable_ai = start_with_ai or self.cfg.get_bool("Settings", "ai_mode", False)

        if self.enable_ai:
            if not os.environ.get("GEMINI_API_KEY"):
                messagebox.showerror(
                    "Missing API Key",
                    "GEMINI_API_KEY environment variable is not defined.\n\n"
                    "Please set it prior to startup with --ai:\n"
                    'export GEMINI_API_KEY="my_ai_google_key"'
                )
                self.enable_ai = False  # Gracefully fall back to non-AI mode

        self.root = tk.Tk()
        
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

        saved_geometry = self.cfg.get_string("Window", "geometry", "640x500")
        self.root.geometry(saved_geometry)
        self.root.attributes("-topmost", True)
        self.root.withdraw()

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
        # Using a Button with bd=1 and relief=tk.SOLID gives a crisp, thin 1px outline across X11/Tkinter.
        # Binding it to command=self.toggle_window allows clicking anywhere on the footer to hide/show.
        self.footer_btn = tk.Button(
            self.root,
            bd=1,
            relief=tk.SOLID,
            highlightthickness=0,
            command=self.toggle_window,
            cursor="hand2"  # Visual cue that the footer is interactive
        )
        self.footer_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=2, pady=2)

        self.status_label = tk.Label(
            self.footer_btn,
            text="Note: mycompanion always holds topmost window. Click here or press Ctrl+Space to hide",
            font=("Helvetica", 9, "italic")
        )
        self.status_label.pack(pady=2)

        # Ensure clicking directly on the label text also triggers the toggle action
        self.status_label.bind("<Button-1>", lambda e: self.toggle_window())

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

        tk.Button(self.notes_ctrl_frame, text="Save Selected As", command=self.save_selected_as, bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0))
        # tk.Button(self.notes_ctrl_frame, text="AI (Ctrl-a)", command=self.toggle_ai_bar, bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0))

        if self.enable_ai:
            tk.Button(self.notes_ctrl_frame, text="AI (Ctrl-a)", command=self.toggle_ai_bar, bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0))

        if self.use_vim:
            tk.Button(self.notes_ctrl_frame, text="Edit in Vim", command=lambda: self.open_in_vim(self.note_file, self.text_area), bd=0, padx=8, pady=2).pack(side=tk.RIGHT)

        self.text_area = tk.Text(
            self.notes_frame, wrap=tk.WORD, font=("Monospace", 11), bd=0, padx=10, pady=10
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.text_area.bind("<KeyRelease>", lambda e: self.apply_link_parsing(self.text_area))
        self.load_notes()

        if self.use_vim:
            self.text_area.config(state=tk.DISABLED)

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

        tk.Button(self.calc_history_header, text="Save Select As...", command=self.save_selected_as, bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0))

        if self.use_vim:
            tk.Button(self.calc_history_header, text="Edit in Vim", command=lambda: self.open_in_vim(self.calc_history_file, self.calc_history_text), bd=0, padx=8, pady=2).pack(side=tk.RIGHT)

        self.calc_history_text = tk.Text(
            self.calc_frame, wrap=tk.WORD, font=("Monospace", 10), bd=0, padx=10, pady=10
        )
        self.calc_history_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        self.calc_history_text.bind("<KeyRelease>", lambda e: self.apply_link_parsing(self.calc_history_text))
        self.load_calc_history()

        if self.use_vim:
            self.calc_history_text.config(state=tk.DISABLED)

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

        tk.Button(self.cal_notes_header_frame, text="Save Select As...", command=self.save_selected_as, bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0))

        if self.use_vim:
            tk.Button(self.cal_notes_header_frame, text="Edit in Vim", command=lambda: self.open_in_vim(self.cal_notes_file, self.cal_notes_text), bd=0, padx=8, pady=2).pack(side=tk.RIGHT)

        self.cal_notes_text = tk.Text(
            self.cal_frame, wrap=tk.WORD, font=("Monospace", 10), bd=0, padx=10, pady=5
        )
        self.cal_notes_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=15, pady=10)
        self.cal_notes_text.bind("<KeyRelease>", lambda e: self.apply_link_parsing(self.cal_notes_text))
        self.load_cal_notes()

        if self.use_vim:
            self.cal_notes_text.config(state=tk.DISABLED)

        # --- VIEW 4: TODO ---
        self.todo_frame = tk.Frame(self.content_frame)
        self.todo_ctrl_frame = tk.Frame(self.todo_frame, pady=4, padx=10)
        self.todo_ctrl_frame.pack(side=tk.TOP, fill=tk.X)

        lbl_todo = "To-Do"
        self.todo_lbl_widget = tk.Label(self.todo_ctrl_frame, text=lbl_todo, font=("Monospace", 9, "bold"))
        self.todo_lbl_widget.pack(side=tk.LEFT)

        tk.Button(self.todo_ctrl_frame, text="Save Select As...", command=self.save_selected_as, bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0))

        if self.use_vim:
            tk.Button(self.todo_ctrl_frame, text="Edit in Vim", command=lambda: self.open_in_vim(self.todo_file, self.todo_text_area), bd=0, padx=8, pady=2).pack(side=tk.RIGHT)

        self.todo_text_area = tk.Text(
            self.todo_frame, wrap=tk.WORD, font=("Monospace", 11), bd=0, padx=10, pady=10
        )
        self.todo_text_area.pack(fill=tk.BOTH, expand=True)
        self.todo_text_area.bind("<KeyRelease>", lambda e: self.apply_link_parsing(self.todo_text_area))
        self.load_todo()

        if self.use_vim:
            self.todo_text_area.config(state=tk.DISABLED)

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
        self.root.bind("<Control-E>", lambda e: self.edit_config_file())
        self.root.bind("<Control-t>", lambda e: self.open_theme_selector())
        self.root.bind("<Control-T>", lambda e: self.open_theme_selector())
        self.root.bind("<Control-q>", lambda event: self.quit_app())
        self.root.bind("<Control-Q>", lambda event: self.quit_app())

        self.root.bind("<Control-h>", lambda e: self.show_help_legend())
        self.root.bind("<Control-H>", lambda e: self.show_help_legend())
        self.root.bind("<Control-slash>", lambda e: self.show_help_legend())

        self.root.bind("<Control-r>", lambda e: self.prompt_run_command())
        self.root.bind("<Control-R>", lambda e: self.prompt_run_command())

        self.bind_custom_commands()

        self.is_visible = False
        self.hotkey_listener = None

        self.current_theme_name = self.load_saved_theme()
        self.apply_theme(self.current_theme_name)


    def bind_custom_commands(self):
        custom_cmds = self.cfg.get_custom_commands()
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
        theme_name = self.cfg.get_string("Theme", "name", "Dark / White (Default)")
        return theme_name if theme_name in THEMES else "Dark / White (Default)"

    def save_theme(self, theme_name):
        self.cfg.set_value("Theme", "name", theme_name)

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
        win.geometry("320x250")
        win.attributes("-topmost", True)

        colors = THEMES[self.current_theme_name]
        win.config(bg=colors["bg"])

        lbl = tk.Label(win, text="Choose Application Theme:", bg=colors["bg"], fg=colors["fg"], font=("Monospace", 10, "bold"))
        lbl.pack(pady=(10, 5))

        listbox = tk.Listbox(
            win, bg=colors["panel_bg"], fg=colors["fg"],
            selectbackground=colors["btn_bg"], font=("Monospace", 10), bd=0, relief=tk.FLAT
        )
        listbox.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        for theme in THEMES.keys():
            listbox.insert(tk.END, theme)

        def on_select(evt):
            sel = listbox.curselection()
            if sel:
                chosen = listbox.get(sel[0])
                self.apply_theme(chosen)
                colors_new = THEMES[chosen]
                win.config(bg=colors_new["bg"])
                lbl.config(bg=colors_new["bg"], fg=colors_new["fg"])
                listbox.config(bg=colors_new["panel_bg"], fg=colors_new["fg"], selectbackground=colors_new["btn_bg"])
                close_btn.config(bg=colors_new["btn_bg"], fg=colors_new["btn_fg"])

        listbox.bind("<<ListboxSelect>>", on_select)

        close_btn = tk.Button(win, text="Close", command=win.destroy, bg=colors["btn_bg"], fg=colors["btn_fg"], bd=0, padx=10, pady=4)
        close_btn.pack(pady=10)

        return "break"

    def apply_link_parsing(self, text_widget):
        for tag in text_widget.tag_names():
            if tag.startswith(("ext_", "file_", "wiki_")):
                text_widget.tag_delete(tag)

        content = text_widget.get("1.0", tk.END)

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

        for idx, match in enumerate(re.finditer(r"\[(.*?)\]\((file://.*?)\)", content)):
            tag_name = f"file_{idx}"
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            file_path = match.group(2).replace("file://", "")

            text_widget.tag_config(tag_name, foreground="#10B981", underline=True)
            text_widget.tag_add(tag_name, start, end)
            text_widget.tag_bind(tag_name, "<Button-1>", lambda e, p=file_path: self.open_file_subwindow(p))
            text_widget.tag_bind(tag_name, "<Enter>", lambda e: text_widget.config(cursor="hand2"))
            text_widget.tag_bind(tag_name, "<Leave>", lambda e: text_widget.config(cursor=""))

    def open_or_create_file(self, file_path):
        path = Path(file_path)
        try:
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            subprocess.run(["xdg-open", str(path)])
        except Exception as err:
            messagebox.showerror("File Error", f"Could not open/create file:\n{err}")


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
        win.geometry("600x450")
        win.attributes("-topmost", True)

        colors = THEMES[self.current_theme_name]
        win.configure(bg=colors["bg"])
        self.sub_windows.append(win)
        win.protocol("WM_DELETE_WINDOW", lambda: (self.sub_windows.remove(win), win.destroy()))

        top_bar = tk.Frame(win, bg=colors["panel_bg"], pady=4, padx=10)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        path_label = tk.Label(top_bar, text=str(path), bg=colors["panel_bg"], fg=colors["fg"], font=("Monospace", 9, "bold"), anchor="w")
        path_label.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Only show the Delete button if the file is opened for editing
        if not read_only:
            def delete_file():
                confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {path.name}?", parent=win)
                if confirm:
                    try:
                        if path.exists():
                            path.unlink()
                        win.destroy()
                    except Exception as err:
                        messagebox.showerror("Delete Error", f"Could not delete file:\n{err}", parent=win)

            delete_btn = tk.Button(
                top_bar, text="Delete Note", command=delete_file,
                bg="#8b0000", fg="#fff", activebackground="#a00000", activeforeground="#fff",
                bd=0, padx=8, pady=2, font=("Monospace", 8, "bold")
            )
            delete_btn.pack(side=tk.RIGHT)

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

        # Parse clickable links / syntax highlighting if applicable
        if not read_only:
            editor.bind("<KeyRelease>", lambda e: self.apply_link_parsing(editor))
        self.apply_link_parsing(editor)

        # Disable editing if read_only is True (placed after content insertion and parsing)
        if read_only:
            editor.config(state="disabled")

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
            if not path.exists():
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

        win.protocol("WM_DELETE_WINDOW", lambda: (save_file(), win.destroy()))
        editor.bind("<Control-s>", save_file)
        editor.bind("<Control-S>", save_file)

        save_btn = tk.Button(ctrl_frame, text="Save (Ctrl-S)", command=save_file, bg=colors["btn_bg"], fg=colors["btn_fg"], bd=0, padx=10, pady=3)
        save_btn.pack(side=tk.RIGHT, padx=5)

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

        if self.use_vim:
            text_widget.config(state=tk.DISABLED)

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
            result = eval(expr, {"__builtins__": None}, {})
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
        if not self.use_vim:
            with open(self.note_file, "w", encoding="utf-8") as f:
                f.write(self.text_area.get("1.0", tk.END).strip())
            with open(self.cal_notes_file, "w", encoding="utf-8") as f:
                f.write(self.cal_notes_text.get("1.0", tk.END).strip())
            with open(self.todo_file, "w", encoding="utf-8") as f:
                f.write(self.todo_text_area.get("1.0", tk.END).strip())
            with open(self.calc_history_file, "w", encoding="utf-8") as f:
                f.write(self.calc_history_text.get("1.0", tk.END).strip())
        else:
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
        self.cfg.set_value("Window", "geometry", self.root.geometry())

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
        self.save_notes()
        self.cfg.set_value("Window", "geometry", self.root.geometry())
        self.root.withdraw()
        self.sub_windows = [w for w in self.sub_windows if w.winfo_exists()]
        for win in self.sub_windows:
            win.withdraw()
        self.is_visible = False

    def quit_app(self):
        self.save_notes()
        self.cfg.set_value("Window", "geometry", self.root.geometry())
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
        self.hotkey_listener = keyboard.GlobalHotKeys({
            '<ctrl>+<space>': self.toggle_window
        })
        self.hotkey_listener.start()
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

        hdr = tk.Label(
            win, text="Keyboard Shortcuts & Syntax",
            bg=colors["header_bg"], fg=colors["fg"],
            font=("Monospace", 10, "bold"), pady=6
        )
        hdr.pack(side=tk.TOP, fill=tk.X)

        help_text = tk.Text(
            win, wrap=tk.WORD, bg=colors["bg"], fg=colors["fg"],
            insertbackground=colors["insert_bg"], font=("Monospace", 9),
            bd=0, padx=12, pady=10
        )
        help_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        content = (
            "GLOBAL SHORTCUTS:\n"
            "  Ctrl-Space   : Toggle main window visibility\n"
            "  Ctrl-1..4    : Switch tabs (1:Notes, 2:Calc, 3:Cal, 4:Todo)\n"
            "  Ctrl-a       : Toggle Gemini AI bar\n"
            "  Alt-c        : View configuration file\n"
            "  Ctrl-r       : Run command dialog\n"
            "  Ctrl-t       : Open Theme Selector\n"
            "  Ctrl-h / ?   : Show this help window\n"
            "  Ctrl-s       : Save selected text to file\n"
            "  Ctrl-q       : Quit application\n\n"
            "LINK FORMATTING:\n"
            "  https://...                    : Open URL in web browser\n"
            "  [Label](file:///path/to/file)  : Open path in sub-window editor\n"
        )

        # 2. Extract and format CONFIG SHORTCUTS using ConfigManager helper
        content += "\nCONFIG SHORTCUTS:\n"
        
        commands = self.cfg.get_custom_commands() if hasattr(self, 'cfg') and self.cfg else []

        if commands:
            for item in commands:
                shortcut = item.get("shortcut", "")
                title = item.get("title") or item.get("command", "")
                content += f"  {shortcut:<12} : {title}\n"
        else:
            content += "  (No custom commands defined in configuration)\n"

        content += "\n"

        help_text.insert("1.0", content)
        help_text.config(state=tk.DISABLED)

        ctrl_frame = tk.Frame(win, bg=colors["panel_bg"], pady=6, padx=10)
        ctrl_frame.pack(side=tk.BOTTOM, fill=tk.X)

        close_btn = tk.Button(
            ctrl_frame, text="Close", command=win.destroy,
            bg=colors["btn_bg"], fg=colors["btn_fg"], bd=0, padx=12, pady=3
        )
        close_btn.pack(side=tk.RIGHT)

        return "break"
        # ### EOB def show_help_legend(self, event=None): ### #


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
        #  mycompanion.conf [cmd_*] (geometry) 
        # → ConfigManager.get_custom_commands() 
        # → MiniSidekick.bind_custom_commands() 
        # → MiniSidekick.run_command(..., geometry=...) 
        # → MiniSidekick.open_in_terminal(..., geometry=...)
        # import subprocess

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
            geom = geometry or self.cfg.get_string("Window", "geometry", "180x40")
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

if __name__ == "__main__":
    args = docopt(__doc__, version=VERSION)

    # Set the global DEBUG flag dynamically from CLI flag
    if args.get("--debug"):
        DEBUG = True
        import inspect  # Only loaded into memory when debugging

    start_ai = args.get("--ai", False)
    use_vim = args.get("--vim", False)

    ensure_daemon(args)

    app = MiniSidekick(start_with_ai=start_ai, use_vim=use_vim, doc_args=args)
    app.run()
