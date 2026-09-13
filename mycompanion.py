#!/usr/bin/env python3
"""
=======================
     mycompanion.py
=======================

Run this app from the command line.

Usage:
    mycompanion.py [--ai] [--vim]
    mycompanion.py (-h | --help)

Options:
    -h --help    Show this help and storage locations.
    --ai         Start with Gemini AI input bar visible.
    --vim        Enable external Vim editor buttons and shortcuts for notes/todos.

The program becomes resident in memory and can be called up with Ctrl-space
Toggle open or closed with the Ctrl-space
While it is up - hit Ctrl-q to quit out of the program completely
Hit Ctrl-a to toggle the Gemini AI input bar on/off.

    Ctrl-space     toggle main window
    Ctrl-1      notes tab
    Ctrl-2      calculator tab
    Ctrl-3      calendar tab
    Ctrl-4      todo tab
    Ctrl-a      toggle AI query input 
    Ctrl-s      save selected text as file
    Ctrl-q      quit (removes program from memory - but data is preserved in files)

SETUP GEMINI AI (optional): 
  1. Generate an API key at: https://aistudio.google.com/app/apikey (create project name, import projects, create project api_key)
  2. Export the key in your terminal session before launching:
     export GEMINI_API_KEY="AIzaSyYourKeyHere"

    Enjoy!

companionway.net © 2026
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from pynput import keyboard
import subprocess
import calendar
import datetime
import threading
from pathlib import Path
import tempfile
from docopt import docopt


ROOTNAME = "mycompanion"
TITLE = "MyCompanion"
VERSION = "0.3.0"

# Determine base directories based on the operating system
if sys.platform == "darwin":
    DATA_DIR = Path.home() / "Library" / "Application Support" / ROOTNAME
    STATE_DIR = DATA_DIR
elif sys.platform == "win32":
    appdata = os.environ.get("APPDATA")
    DATA_DIR = (Path(appdata) / ROOTNAME) if appdata else (Path.home() / "AppData" / "Local" / ROOTNAME)
    STATE_DIR = DATA_DIR
else:
    xdg_data = os.environ.get("XDG_DATA_HOME")
    DATA_DIR = (Path(xdg_data) / ROOTNAME) if xdg_data and Path(xdg_data).is_absolute() else (Path.home() / ".local" / "share" / ROOTNAME)
    xdg_state = os.environ.get("XDG_STATE_HOME")
    STATE_DIR = (Path(xdg_state) / ROOTNAME) if xdg_state and Path(xdg_state).is_absolute() else (Path.home() / ".local" / "state" / ROOTNAME)

DATA_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

NOTES_FILE = DATA_DIR / f"{ROOTNAME}_notes.txt"
CAL_NOTES_FILE = DATA_DIR / f"{ROOTNAME}_cal_notes.txt"
CALC_NOTES_FILE = DATA_DIR / f"{ROOTNAME}_calc_notes.txt"
TODO_FILE = DATA_DIR / f"{ROOTNAME}_todo.txt"
LOCK_FILE = STATE_DIR / f"{ROOTNAME}.lock"


def print_help_and_paths():
    print(__doc__)
    print("----------------------------------------")
    print("Storage & Runtime Locations:")
    print(f"  • Data / Store Directory : {DATA_DIR}")
    print(f"  • Notes File             : {NOTES_FILE}")
    print(f"  • Calendar Notes File    : {CAL_NOTES_FILE}")
    print(f"  • Calculator History File: {CALC_NOTES_FILE}")
    print(f"  • To-Do File             : {TODO_FILE}")
    print(f"  • Lock File              : {LOCK_FILE}")
    print("----------------------------------------\n")


def ensure_daemon():
    script_path = os.path.abspath(__file__)
    python_exec = sys.executable

    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)
            print(f"MyCompanion is already running (PID {old_pid}).")
            print(f"Use Ctrl-space to toggle the window.")
            print(f"Lock file location: {LOCK_FILE}")
            sys.exit(0)
        except (ProcessLookupError, ValueError):
            os.remove(LOCK_FILE)
        except PermissionError:
            sys.exit(0)

    if os.environ.get("SIDEKICK_DAEMON") != "1":
        print_help_and_paths()

        new_env = os.environ.copy()
        new_env["SIDEKICK_DAEMON"] = "1"
        
        args = [python_exec, script_path] + sys.argv[1:]
        subprocess.Popen(
            args,
            env=new_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True
        )
        sys.exit(0)
    else:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))

class MiniSidekick:
    def __init__(self, start_with_ai=False, use_vim=False):
        self.note_file = NOTES_FILE
        self.cal_notes_file = CAL_NOTES_FILE
        self.calc_history_file = CALC_NOTES_FILE
        self.todo_file = TODO_FILE
        self.use_vim = use_vim
        
        self.root = tk.Tk()
        self.root.title(os.path.basename(__file__))
        self.root.geometry("640x500") 
        self.root.attributes("-topmost", True)
        self.root.withdraw()
        
        self.last_checked_date = datetime.datetime.now().date()
        
        self.header_frame = tk.Frame(self.root, bg="#1a1a1a", pady=5, padx=10)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)

        self.date_label = tk.Label(self.header_frame, text="", bg="#1a1a1a", fg="#9cdcfe", font=("Monospace", 9))
        self.date_label.pack(side=tk.LEFT)

        self.title_label = tk.Label(self.header_frame, text=f"{TITLE}", bg="#1a1a1a", fg="#fff", font=("Monospace", 10, "bold"))
        self.title_label.pack(side=tk.LEFT, expand=True)

        self.version_label = tk.Label(self.header_frame, text=f" v{VERSION}", bg="#1a1a1a", fg="#888888", font=("Monospace", 9))
        self.version_label.pack(side=tk.RIGHT)

        self.time_label = tk.Label(self.header_frame, text="", bg="#1a1a1a", fg="#4ec9b0", font=("Monospace", 9))
        self.time_label.pack(side=tk.RIGHT)

        self.nav_frame = tk.Frame(self.root, bg="#2d2d2d")
        self.nav_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(self.nav_frame, text="1. Notes", command=lambda: self.switch_view("notes"), bg="#333", fg="#fff", bd=0, padx=10, pady=5).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(self.nav_frame, text="2. Calc", command=lambda: self.switch_view("calc"), bg="#333", fg="#fff", bd=0, padx=10, pady=5).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(self.nav_frame, text="3. Calendar", command=lambda: self.switch_view("cal"), bg="#333", fg="#fff", bd=0, padx=10, pady=5).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(self.nav_frame, text="4. Todo", command=lambda: self.switch_view("todo"), bg="#333", fg="#fff", bd=0, padx=10, pady=5).pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.ai_frame = tk.Frame(self.root, bg="#252526", pady=6, padx=10)

        ai_label = tk.Label(self.ai_frame, text="Gemini:", bg="#252526", fg="#4ec9b0", font=("Monospace", 9, "bold"))
        ai_label.pack(side=tk.LEFT, padx=(0, 5))

        self.ai_input = tk.Entry(self.ai_frame, font=("Monospace", 10), bg="#333333", fg="#d4d4d4", insertbackground="white", bd=0)
        self.ai_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=3)
        self.ai_input.bind("<Return>", self.send_to_gemini_click)

        ai_btn = tk.Button(self.ai_frame, text="Ask", command=self.send_to_gemini_click, bg="#333", fg="#fff", bd=0, padx=10, pady=2)
        ai_btn.pack(side=tk.RIGHT)

        self.content_frame = tk.Frame(self.root)
        self.content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # --- VIEW 1: NOTES ---
        self.notes_frame = tk.Frame(self.content_frame)
        notes_ctrl_frame = tk.Frame(self.notes_frame, bg="#2d2d2d", pady=4, padx=10)
        notes_ctrl_frame.pack(side=tk.TOP, fill=tk.X)
        
        lbl_notes = "Notes (Vim Editor Mode - Press Ctrl-E)" if self.use_vim else "Notes"
        tk.Label(notes_ctrl_frame, text=lbl_notes, bg="#2d2d2d", fg="#9cdcfe", font=("Monospace", 9, "bold")).pack(side=tk.LEFT)
        
        tk.Button(notes_ctrl_frame, text="Save selected-text as: <filename>", command=self.save_selected_as, bg="#333", fg="#fff", bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0))
        
        if self.use_vim:
            tk.Button(notes_ctrl_frame, text="Edit in Vim", command=lambda: self.open_in_vim(self.note_file, self.text_area), bg="#333", fg="#fff", bd=0, padx=8, pady=2).pack(side=tk.RIGHT)

        self.text_area = tk.Text(
            self.notes_frame, wrap=tk.WORD, bg="#1e1e1e", fg="#d4d4d4", 
            insertbackground="white", font=("Monospace", 11), bd=0, padx=10, pady=10
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.load_notes()

        if self.use_vim:
            self.text_area.config(state=tk.DISABLED)
            self.text_area.bind("<Control-e>", lambda e: self.open_in_vim(self.note_file, self.text_area))
            self.text_area.bind("<Control-E>", lambda e: self.open_in_vim(self.note_file, self.text_area))

        # --- VIEW 2: CALCULATOR ---
        self.calc_frame = tk.Frame(self.content_frame, bg="#1e1e1e")
        
        input_container = tk.Frame(self.calc_frame, bg="#1e1e1e")
        input_container.pack(fill=tk.X, padx=15, pady=15)

        calc_label = tk.Label(input_container, text="Calculation: ", font=("Monospace", 14), bg="#1e1e1e", fg="#d4d4d4")
        calc_label.pack(side=tk.LEFT)

        self.calc_display = tk.Entry(input_container, font=("Monospace", 14), bg="#2d2d2d", fg="#d4d4d4", insertbackground="white", bd=0)
        self.calc_display.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.calc_display.bind("<Return>", self.evaluate_calc)

        self.calc_result = tk.Label(self.calc_frame, text="Type an expression and hit Enter (e.g., 45 * 12)", font=("Monospace", 10), bg="#1e1e1e", fg="#888")
        self.calc_result.pack(padx=15, anchor="w")

        history_label = tk.Label(self.calc_frame, text="Calculation History:", font=("Monospace", 10, "bold"), bg="#1e1e1e", fg="#888", anchor="w")
        history_label.pack(padx=15, pady=(15, 5), anchor="w")

        self.calc_history_text = tk.Text(
            self.calc_frame, wrap=tk.WORD, bg="#2d2d2d", fg="#d4d4d4", 
            font=("Monospace", 10), bd=0, padx=10, pady=10
        )
        self.calc_history_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        self.calc_history_text.config(state=tk.DISABLED)
        self.load_calc_history()

        # --- VIEW 3: CALENDAR ---
        self.cal_frame = tk.Frame(self.content_frame, bg="#1e1e1e")
        
        self.cal_text = tk.Text(
            self.cal_frame, wrap=tk.NONE, bg="#1e1e1e", fg="#d4d4d4", 
            font=("Monospace", 10), bd=0, padx=15, pady=10, height=9
        )
        self.cal_text.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.load_calendar()

        cal_notes_header_frame = tk.Frame(self.cal_frame, bg="#1e1e1e")
        cal_notes_header_frame.pack(side=tk.TOP, fill=tk.X, padx=15, pady=(5, 0))

        cal_notes_label = tk.Label(cal_notes_header_frame, text="Calendar Notes:", font=("Monospace", 10, "bold"), bg="#1e1e1e", fg="#9cdcfe", anchor="w")
        cal_notes_label.pack(side=tk.LEFT)

        tk.Button(cal_notes_header_frame, text="Save Sel As...", command=self.save_selected_as, bg="#333", fg="#fff", bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0))

        if self.use_vim:
            tk.Button(cal_notes_header_frame, text="Edit in Vim", command=lambda: self.open_in_vim(self.cal_notes_file, self.cal_notes_text), bg="#333", fg="#fff", bd=0, padx=8, pady=2).pack(side=tk.RIGHT)

        self.cal_notes_text = tk.Text(
            self.cal_frame, wrap=tk.WORD, bg="#1e1e1e", fg="#d4d4d4", 
            insertbackground="white", font=("Monospace", 10), bd=0, padx=10, pady=5
        )
        self.cal_notes_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=15, pady=10)
        self.load_cal_notes()

        if self.use_vim:
            self.cal_notes_text.config(state=tk.DISABLED)
            self.cal_notes_text.bind("<Control-e>", lambda e: self.open_in_vim(self.cal_notes_file, self.cal_notes_text))
            self.cal_notes_text.bind("<Control-E>", lambda e: self.open_in_vim(self.cal_notes_file, self.cal_notes_text))

        # --- VIEW 4: TODO ---
        self.todo_frame = tk.Frame(self.content_frame)
        todo_ctrl_frame = tk.Frame(self.todo_frame, bg="#2d2d2d", pady=4, padx=10)
        todo_ctrl_frame.pack(side=tk.TOP, fill=tk.X)
        
        lbl_todo = "To-Do (Vim Editor Mode - Press Ctrl-E)" if self.use_vim else "To-Do"
        tk.Label(todo_ctrl_frame, text=lbl_todo, bg="#2d2d2d", fg="#9cdcfe", font=("Monospace", 9, "bold")).pack(side=tk.LEFT)
        
        tk.Button(todo_ctrl_frame, text="Save Sel As...", command=self.save_selected_as, bg="#333", fg="#fff", bd=0, padx=8, pady=2).pack(side=tk.RIGHT, padx=(5, 0))

        if self.use_vim:
            tk.Button(todo_ctrl_frame, text="Edit in Vim", command=lambda: self.open_in_vim(self.todo_file, self.todo_text_area), bg="#333", fg="#fff", bd=0, padx=8, pady=2).pack(side=tk.RIGHT)

        self.todo_text_area = tk.Text(
            self.todo_frame, wrap=tk.WORD, bg="#1e1e1e", fg="#d4d4d4", 
            insertbackground="white", font=("Monospace", 11), bd=0, padx=10, pady=10
        )
        self.todo_text_area.pack(fill=tk.BOTH, expand=True)
        self.load_todo()

        if self.use_vim:
            self.todo_text_area.config(state=tk.DISABLED)
            self.todo_text_area.bind("<Control-e>", lambda e: self.open_in_vim(self.todo_file, self.todo_text_area))
            self.todo_text_area.bind("<Control-E>", lambda e: self.open_in_vim(self.todo_file, self.todo_text_area))

        self.ai_visible = False
        if start_with_ai:
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

        # Save Selected As Hotkeys
        self.root.bind("<Control-s>", self.save_selected_as)
        self.root.bind("<Control-S>", self.save_selected_as)
        self.text_area.bind("<Control-s>", self.save_selected_as)
        self.text_area.bind("<Control-S>", self.save_selected_as)
        self.todo_text_area.bind("<Control-s>", self.save_selected_as)
        self.todo_text_area.bind("<Control-S>", self.save_selected_as)
        self.cal_notes_text.bind("<Control-s>", self.save_selected_as)
        self.cal_notes_text.bind("<Control-S>", self.save_selected_as)

        self.root.bind("<Control-a>", lambda e: self.toggle_ai_bar())
        self.root.bind("<Control-A>", lambda e: self.toggle_ai_bar())

        self.root.bind("<Control-q>", lambda event: self.quit_app())
        self.root.bind("<Control-Q>", lambda event: self.quit_app())
        
        self.text_area.bind("<Control-q>", lambda event: self.quit_app())
        self.calc_display.bind("<Control-q>", lambda event: self.quit_app())
        self.todo_text_area.bind("<Control-q>", lambda event: self.quit_app())
        
        self.is_visible = False
        self.hotkey_listener = None

    def save_selected_as(self, event=None):
        widget = None
        if self.current_view == "notes":
            widget = self.text_area
        elif self.current_view == "todo":
            widget = self.todo_text_area
        elif self.current_view == "cal":
            widget = self.cal_notes_text

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
        with open(file_path, "w") as f:
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
            with open(file_path, "r") as f:
                text_widget.insert("1.0", f.read())

        if self.use_vim:
            text_widget.config(state=tk.DISABLED)

    def handle_tab_shortcut(self, view_name):
        self.switch_view(view_name)
        return "break"

    def toggle_ai_bar(self, force_state=None):
        if force_state is not None:
            self.ai_visible = not force_state 
            
        current_geometry = self.root.geometry().split("+")[0]
        w, h = map(int, current_geometry.split("x"))

        if self.ai_visible:
            self.ai_frame.pack_forget()
            self.ai_visible = False
            self.root.geometry(f"{w}x{max(400, h - 45)}")
        else:
            self.ai_frame.pack(side=tk.BOTTOM, fill=tk.X)
            self.ai_visible = True
            self.root.geometry(f"{w}x{h + 45}")
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
        win.configure(bg="#1e1e1e")

        q_label = tk.Label(win, text=f"Q: {query}", bg="#252526", fg="#9cdcfe", font=("Monospace", 9, "bold"), anchor="w", padx=10, pady=6)
        q_label.pack(side=tk.TOP, fill=tk.X)

        text_box = tk.Text(win, wrap=tk.WORD, bg="#1e1e1e", fg="#d4d4d4", insertbackground="white", font=("Monospace", 10), bd=0, padx=10, pady=10)
        text_box.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        text_box.insert("1.0", answer)
        text_box.config(state=tk.DISABLED, exportselection=True)

        ctrl_frame = tk.Frame(win, bg="#2d2d2d", pady=6, padx=10)
        ctrl_frame.pack(side=tk.BOTTOM, fill=tk.X)

        def copy_text():
            win.clipboard_clear()
            win.clipboard_append(text_box.get("1.0", tk.END).strip())
            copy_btn.config(text="Copied!")
            win.after(1500, lambda: copy_btn.config(text="Copy"))

        copy_btn = tk.Button(ctrl_frame, text="Copy", command=copy_text, bg="#333", fg="#fff", bd=0, padx=10, pady=4)
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

        edit_btn = tk.Button(ctrl_frame, text="Edit", command=toggle_edit, bg="#333", fg="#fff", bd=0, padx=10, pady=4)
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
            self.calc_history_text.config(state=tk.NORMAL)
            self.calc_history_text.insert("1.0", history_entry)
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
            if today_str in line_text.split():
                line_content = self.cal_text.get(f"{line_num}.0", f"{line_num}.end")
                col_idx = line_content.find(today_str)
                if col_idx != -1:
                    start_pos = f"{line_num}.{col_idx}"
                    end_pos = f"{line_num}.{col_idx + len(today_str)}"
                    self.cal_text.tag_add("today", start_pos, end_pos)
                break

        self.cal_text.config(state=tk.DISABLED)

    def load_notes(self):
        if os.path.exists(self.note_file):
            with open(self.note_file, "r") as f:
                self.text_area.insert("1.0", f.read())

    def load_cal_notes(self):
        if os.path.exists(self.cal_notes_file):
            with open(self.cal_notes_file, "r") as f:
                self.cal_notes_text.insert("1.0", f.read())

    def load_calc_history(self):
        if os.path.exists(self.calc_history_file):
            with open(self.calc_history_file, "r") as f:
                self.calc_history_text.config(state=tk.NORMAL)
                self.calc_history_text.insert("1.0", f.read())
                self.calc_history_text.config(state=tk.DISABLED)

    def load_todo(self):
        if os.path.exists(self.todo_file) and os.path.getsize(self.todo_file) > 0:
            with open(self.todo_file, "r") as f:
                self.todo_text_area.insert("1.0", f.read())
        else:
            default_todo = (
                "=== High Priority ===\n\n"
                "=== Medium Priority ===\n\n"
                "=== Low Priority ===\n"
            )
            self.todo_text_area.insert("1.0", default_todo)

    def save_notes(self):
        if not self.use_vim:
            with open(self.note_file, "w") as f:
                f.write(self.text_area.get("1.0", tk.END).strip())
            with open(self.cal_notes_file, "w") as f:
                f.write(self.cal_notes_text.get("1.0", tk.END).strip())
            with open(self.todo_file, "w") as f:
                f.write(self.todo_text_area.get("1.0", tk.END).strip())
        with open(self.calc_history_file, "w") as f:
            f.write(self.calc_history_text.get("1.0", tk.END).strip())

    def toggle_window(self):
        self.root.after(0, self._perform_toggle)

    def _perform_toggle(self):
        if self.is_visible:
            self.hide_window()
        else:
            self.show_window()

    def show_window(self):
        if self.current_view == "notes":
            self.save_notes()
            
        self.root.update_idletasks()
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        window_width = 640
        window_height = 545 if self.ai_visible else 500
        
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.root.deiconify()
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
        self.root.withdraw()
        self.is_visible = False

    def quit_app(self):
        self.save_notes()
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


if __name__ == "__main__":
    ensure_daemon()
    try:
        args = docopt(__doc__, version=VERSION)
    except Exception:
        args = {"--ai": "--ai" in sys.argv, "--vim": "--vim" in sys.argv}

    start_ai = args.get("--ai", False)
    use_vim = args.get("--vim", False)

    app = MiniSidekick(start_with_ai=start_ai, use_vim=use_vim)
    app.run()
