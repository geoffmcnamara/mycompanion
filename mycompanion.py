#!/home/geoffm/dev/python/venv/bin/python
"""
=======================
    companion.py
=======================

Run this app from the command line.
The program becomes resident in memory and can be called up with Ctrl-space
Toggle is closed with the Ctrl-space
Switch tabs with the mouse or Ctrl-1, Ctrl-2, Ctrl-3 (when window is active).
While it is up - hit Ctrl-q to quit out of the program completely

"""

import sys
import tkinter as tk
from pynput import keyboard
import os
import subprocess
import calendar
import datetime
# from pathlib import Path

# ROOTNAME = Path(__file__).stem
ROOTNAME = "mycompanion"
LOCK_FILE = os.path.expanduser(f"~/{ROOTNAME}.lock")

def ensure_daemon():
    script_path = os.path.abspath(__file__)
    python_exec = sys.executable
    
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 0)
            sys.exit(0)
        except (ProcessLookupError, ValueError):
            os.remove(LOCK_FILE)
        except PermissionError:
            sys.exit(0)

    if os.environ.get("SIDEKICK_DAEMON") != "1":
        new_env = os.environ.copy()
        new_env["SIDEKICK_DAEMON"] = "1"
        subprocess.Popen(
            [python_exec, script_path],
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
    def __init__(self):
        self.note_file = os.path.expanduser(f"~/{ROOTNAME}_notes.txt")
        self.cal_notes_file = os.path.expanduser(f"~/{ROOTNAME}_cal_notes.txt")
        self.calc_history_file = os.path.expanduser(f"~/{ROOTNAME}_calc_notes.txt")
        
        self.root = tk.Tk()
        self.root.title(os.path.basename(__file__))
        self.root.geometry("640x500")
        self.root.attributes("-topmost", True)
        self.root.withdraw()
        
        # Initialize with today's date so it doesn't trigger an immediate redraw mismatch on startup
        self.last_checked_date = datetime.datetime.now().date()
        
        # Header frame for Date, Title, and Time
        self.header_frame = tk.Frame(self.root, bg="#1a1a1a", pady=5, padx=10)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)

        self.date_label = tk.Label(self.header_frame, text="", bg="#1a1a1a", fg="#9cdcfe", font=("Monospace", 9))
        self.date_label.pack(side=tk.LEFT)

        self.title_label = tk.Label(self.header_frame, text=f"{ROOTNAME}", bg="#1a1a1a", fg="#fff", font=("Monospace", 10, "bold"))
        self.title_label.pack(side=tk.LEFT, expand=True)

        self.time_label = tk.Label(self.header_frame, text="", bg="#1a1a1a", fg="#4ec9b0", font=("Monospace", 9))
        self.time_label.pack(side=tk.RIGHT)

        # Top tab navigation frame
        self.nav_frame = tk.Frame(self.root, bg="#2d2d2d")
        self.nav_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(self.nav_frame, text="1. Notes", command=lambda: self.switch_view("notes"), bg="#333", fg="#fff", bd=0, padx=10, pady=5).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(self.nav_frame, text="2. Calc", command=lambda: self.switch_view("calc"), bg="#333", fg="#fff", bd=0, padx=10, pady=5).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(self.nav_frame, text="3. Calendar", command=lambda: self.switch_view("cal"), bg="#333", fg="#fff", bd=0, padx=10, pady=5).pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Main Content Container
        self.content_frame = tk.Frame(self.root)
        self.content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # --------------------------
        # --- VIEW 1: NOTES ---
        # --------------------------
        self.notes_frame = tk.Frame(self.content_frame)
        self.text_area = tk.Text(
            self.notes_frame, wrap=tk.WORD, bg="#1e1e1e", fg="#d4d4d4", 
            insertbackground="white", font=("Monospace", 11), bd=0, padx=10, pady=10
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.load_notes()

        # --------------------------
        # --- VIEW 2: CALCULATOR ---
        # --------------------------
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

        # Calculator History Section (Most recent at the top)
        history_label = tk.Label(self.calc_frame, text="Calculation History:", font=("Monospace", 10, "bold"), bg="#1e1e1e", fg="#888", anchor="w")
        history_label.pack(padx=15, pady=(15, 5), anchor="w")

        self.calc_history_text = tk.Text(
            self.calc_frame, wrap=tk.WORD, bg="#2d2d2d", fg="#d4d4d4", 
            font=("Monospace", 10), bd=0, padx=10, pady=10
        )
        self.calc_history_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        self.calc_history_text.config(state=tk.DISABLED)
        self.load_calc_history()

        # --------------------------
        # --- VIEW 3: CALENDAR ---
        # --------------------------
        self.cal_frame = tk.Frame(self.content_frame, bg="#1e1e1e")
        
        self.cal_text = tk.Text(
            self.cal_frame, wrap=tk.NONE, bg="#1e1e1e", fg="#d4d4d4", 
            font=("Monospace", 10), bd=0, padx=15, pady=10, height=9
        )
        self.cal_text.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.load_calendar()

        cal_notes_label = tk.Label(self.cal_frame, text="Calendar Notes:", font=("Monospace", 10, "bold"), bg="#1e1e1e", fg="#9cdcfe", anchor="w")
        cal_notes_label.pack(side=tk.TOP, fill=tk.X, padx=15, pady=(5, 0))

        self.cal_notes_text = tk.Text(
            self.cal_frame, wrap=tk.WORD, bg="#1e1e1e", fg="#d4d4d4", 
            insertbackground="white", font=("Monospace", 10), bd=0, padx=10, pady=5
        )
        self.cal_notes_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=15, pady=10)
        self.load_cal_notes()

        # Start on notes view
        self.current_view = None
        self.switch_view("notes")

        # Start the clock loop now that all UI elements exist
        self.update_header_clock()

        # ### Bindings & Controls #### #
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        for ctrl_seq in ("<Control-1>", "<Control-Key-1>"):
            self.root.bind(ctrl_seq, lambda e: self.handle_tab_shortcut("notes"))
        for ctrl_seq in ("<Control-2>", "<Control-Key-2>"):
            self.root.bind(ctrl_seq, lambda e: self.handle_tab_shortcut("calc"))
        for ctrl_seq in ("<Control-3>", "<Control-Key-3>"):
            self.root.bind(ctrl_seq, lambda e: self.handle_tab_shortcut("cal"))

        self.root.bind("<Control-q>", lambda event: self.quit_app())
        self.root.bind("<Control-Q>", lambda event: self.quit_app())
        
        self.root.bind("<Control-q>", lambda event: self.quit_app())
        self.text_area.bind("<Control-q>", lambda event: self.quit_app())
        self.calc_display.bind("<Control-q>", lambda event: self.quit_app())
        
        self.root.bind("<Control-1>", lambda event: self.switch_view("notes"))
        self.text_area.bind("<Control-1>", lambda event: self.switch_view("notes"))
        self.calc_display.bind("<Control-1>", lambda event: self.switch_view("notes"))

        self.root.bind("<Control-2>", lambda event: self.switch_view("calc"))
        self.text_area.bind("<Control-2>", lambda event: self.switch_view("calc"))
        self.calc_display.bind("<Control-2>", lambda event: self.switch_view("calc"))

        self.root.bind("<Control-3>", lambda event: self.switch_view("cal"))
        self.text_area.bind("<Control-3>", lambda event: self.switch_view("cal"))
        self.calc_display.bind("<Control-3>", lambda event: self.switch_view("cal"))
        
        self.is_visible = False
        self.hotkey_listener = None

    def handle_tab_shortcut(self, view_name):
        self.switch_view(view_name)
        return "break"

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

    def evaluate_calc(self, event):
        expr = self.calc_display.get().strip()
        if not expr:
            return
        try:
            result = eval(expr, {"__builtins__": None}, {})
            result_str = f"= {result}"
            self.calc_result.config(text=result_str, fg="#4ec9b0")
            
            # Prepend calculation history (most recent at the top)
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
        
        # Highlight today's date in bright yellow on dark gray background
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

    def save_notes(self):
        with open(self.note_file, "w") as f:
            f.write(self.text_area.get("1.0", tk.END).strip())
        with open(self.cal_notes_file, "w") as f:
            f.write(self.cal_notes_text.get("1.0", tk.END).strip())
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
        window_height = 520
        
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        
        if self.current_view == "notes":
            self.text_area.focus_set()
        elif self.current_view == "calc":
            self.calc_display.focus_set()
            
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
    if len(sys.argv) > 1:
        print(__doc__)
    else:
        ensure_daemon()
        app = MiniSidekick()
        app.run()
