# 🧰 MyCompanion

MyCompanion is a lightning-fast, lightweight desktop assistant (PIM Personal Information Manager) that stays resident in the background, giving you instant access to quick notes, a todo list, a calculator with saved history, and a dual-month calendar—all summoned or hidden with a single global hotkey. Optional Gemini AI query and response support.

Designed for minimal friction and maximum speed, it runs quietly as a single-instance daemon and stays out of your way until you need it.

A live header clock displays the current date, live time, and day of the week at a glance.

The app supports wiki-like links to external files.

---

## ✨ Features

- **Global Hotkey Toggle:** Press `Ctrl + Space` from anywhere in your operating system to instantly pull up or hide the application window.
- **Tab 1: Notes (`Ctrl-1`):** A clean, distraction-free markdown/text scratchpad with automatic saving.
- **Tab 2: Calculator & History (`Ctrl-2`):** Type out standard math expressions and hit Enter. Keeps an automatic, reverse-chronological history log (most recent at the top) saved across sessions. The calculator history is editable for adding annotations.
- **Tab 3: Calendar & Notes (`Ctrl-3`):** Displays a side-by-side view of the current and next month with today's date dynamically highlighted, backed by dedicated calendar notes.
- **Tab 4: Todo (`Ctrl-4`):** Dedicated task tracking pane to manage, edit, and organize daily action items and checklists.

---

## 🤖 Optional Gemini AI Setup

To enable AI Query and Response (`Ctrl-a` when launched with `--ai`):

1. Generate an API key at [Google AI Studio](https://aistudio.google.com/app/apikey).

2. Export the key in your environment before launching:

   ```bash
   export GEMINI_API_KEY="AI-YourKeyHere"
   ```

3. Install the Gemini Python library:

```Bash
pip install google-genai
pip install tiktoken --prefer-binary  # Optional: only if your system requests it
```

---

## 🛠️ Prerequisites & Installation

Python 3.x

Tkinter (usually bundled with Python on Linux/macOS/Windows)

Install dependencies via pip:

```Bash
pip install pynput docopt
```

Install directly from GitHub:

```Bash
pip install git+[https://github.com/your-username/mycompanion.git](https://github.com/your-username/mycompanion.git)
```

---

### 🚀 Running the App

Run the script directly from your terminal:

```Bash
mycompanion.py
```

On first launch, the program automatically spawns as a background daemon, manages its own lock file, and listens for your Ctrl + Space toggle.

Command-Line Flags
mycompanion.py --ai — Launch with AI prompt query and response enabled.

mycompanion.py --vim — Launch using Vim as the default editor for all external edits.

---

## 💻 Navigation & Global Shortcuts

Ctrl-space — Toggle application window to top / send to background (remains resident in memory; all state is saved).

Ctrl-q — Save state and quit mycompanion completely (removes daemon from memory).

Ctrl-t — Activate theme selection window (saves selection to mycompanion.conf).

Ctrl-1 — Switch to Notes tab.

Ctrl-2 — Switch to Calculator tab.

Ctrl-3 — Switch to Calendar tab.

Ctrl-4 — Switch to Todo tab.

Ctrl-r — Run custom command (supports modes: terminal, window, silent, or raw).

Ctrl-a — Activate AI query prompt (at bottom).

Alt-c — View and edit mycompanion.conf.

Ctrl-e — If [Settings] editor is defined then it will be launcged to open the current file.

Ctrl-s — If text is selected, opens file choice window to save selected text to a new file.

### Window Behavior

Note: mycompanion runs as a floating, topmost window. 

To minimize or hide the app, press Ctrl+Space or click anywhere on the footer status message at the bottom of the window.

---

## ⚙️ Configuration Syntax (cmd_*)

Custom command entries defined in mycompanion.conf support flexible launcher modes:

```Ini, TOML
[Window]
geometry = 950x630+325+28

[Theme]
name = Cyberpunk Neon

[Settings]
ai_mode = false
md_editor = ghostwriter

# External Editor Command for Ctrl-e
# -----------------------------------------------------------
# Set 'editor' to a native GUI editor (e.g. gvim -f, ghostwriter, gedit) 
# OR provide a full terminal wrapper command if using a CLI
#   editor (e.g. vim, nvim).
#   editor = xterm -bw 4 -bd #00f3ff -geometry 100x30 -e vim

[cmd_htop]
shortcut = <Alt-t>
command = htop
mode = terminal
title = htop

[cmd_finsyms]
shortcut = <Control-Shift-F>
command = /home/geoffm/dev/python/econ/finsyms.py
mode = terminal
title = finsyms

[cmd_xterm]
shortcut = <Control-Shift-x>
command = xterm -geometry 180x40 -T 'Weather Report' -e bash -c 'curl -s wttr.in/Elizabeth_City ; echo "Please use Ctrl-D to exit" ; exec bash --norc'
mode = raw
```

---

## 📁 Generated Files
To maintain persistence across sessions, local files are managed automatically inside your platform's user configuration directory:

~/<platform_dependent>/{rootname}_notes.txt

~/<platform_dependent>/{rootname}_cal_notes.txt

~/<platform_dependent>/{rootname}_calc_notes.txt

~/<platform_dependent>/{rootname}_todo_notes.txt

~/<platform_dependent>/{rootname}.conf (stores geometry, theme, --ai-mode, and --vim-mode)

~/<platform_dependent>/{rootname}.lock (daemon runtime lock file)

---

## 🌐 Wiki Links & Web URLs

Wiki Links: Format links as 

```markdown
[label](file:///absolute/path/to/file.nts). The text turns green and opens the target file on click.
```

Note: Using two slashes (e.g. file://relative/path) builds a relative link.

Web URLs: Standard HTTP/HTTPS URLs (e.g., https://google.com) highlight in blue and launch in your default web browser on click.

```markdown
https://calendar.google.com
```

Tip: If you use google calendar and contacts put this in your calendar notes on the mycompanion calendar pane:

```
https://calendar.google.com
https://contacts.google.com
https://mail.google.com
```

---

**Enjoy!**
