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

## 🖥️ Desktop Menu & Global Hotkey Integration

1. Application Menu Integration (.desktop file)
To launch MyCompanion from your Linux application menu or dock (Budgie, MATE, GNOME, KDE, XFCE), create the following file:

File path: ~/.local/share/applications/mycompanion.desktop

```Ini, TOML
[Desktop Entry]
Type=Application
Name=MyCompanion
Comment=Personal Information Manager
Exec=/home/user/dev/python/venv/bin/python /home/user/mycompanion.py
Icon=utilities-terminal
Terminal=false
Categories=Utility;
StartupNotify=true
```

(Note: Adjust the file paths to match your local virtual environment and Python script location).

2. Native Wayland Global Shortcut (Ctrl+Space)
Since global key-hooking libraries like pynput are restricted under Wayland, bind Ctrl+Space directly in your desktop environment's settings:

* Open System Settings -> Keyboard -> Custom Shortcuts.

* Add a new shortcut named MyCompanion.

* Set Command to: `/home/geoffm/dev/python/venv/bin/python /home/geoffm/mycompanion.py`

**or** if you want it to pop up every time you hit the shortcut key 
    
* Set Command to: `bash -c 'wmctrl -x -a mycompanion || /home/geoffm/dev/python/venv/bin/python /home/geoffm/mycompanion.py'`

* Set Shortcut Key to: Ctrl + Space.


Because MyCompanion includes built-in single-instance locking (mycompanion.lock), pressing your assigned shortcut key will either launch the application or bring the existing window to the foreground without spawning duplicate instances.   

- Step 1: Identify Your Python Executable & Script PathMake sure you know the absolute path to your Python interpreter (or virtual environment) and your mycompanion.py script.Python binary: /home/geoffm/dev/python/venv/bin/python (or /usr/bin/python3)   Script path: /home/geoffm/mycompanion.py   
- Step 2: Configure the Desktop Custom ShortcutDepending on your desktop environment (Budgie, MATE, GNOME, KDE, or XFCE), follow the steps below:

### For Budgie / GNOME

* Open System Settings $\rightarrow$ Keyboard.   
* Scroll to the bottom and select View and Customize Shortcuts (or Custom Shortcuts).   
* Click Add Shortcut (+).   
* Fill in the fields:
    - Name: MyCompanion   
    - Command: /home/user/dev/python/venv/bin/python /home/geoffm/mycompanion.py   
    - Shortcut: Press your desired hotkey combination (e.g., Ctrl + Space or Super + M).   
    - Click Add.   

### For MATE Desktop
* Open Control Center $\rightarrow$ Keyboard Shortcuts.
* Click Add.
    - Set Name to MyCompanion.
    - Set Command to /home/user/dev/python/venv/bin/python /home/user/mycompanion.py.   
Highlight the newly created entry, click on the key sequence column, and press your desired hotkey combination.

### For KDE Plasma

* Open System Settings $\rightarrow$ Shortcuts $\rightarrow$ Custom Shortcuts.
* Click Edit $\rightarrow$ New $\rightarrow$ Global Shortcut $\rightarrow$ Command/URL.
    - Name it MyCompanion.
    - In the Trigger tab, set your key combination.
    - In the Action tab, enter /home/user/dev/python/venv/bin/python /home/user/mycompanion.py.   
* Click Apply.

---

## 💻 Navigation & Global Shortcuts

Ctrl-space — Toggle application window to top / send to background (remains resident in memory; all state is saved).
    (When running in X11 --toggle mode).

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


## Calculator Input Reference Guide

The `mycompanion` calculator supports standard mathematical operations, inline trigonometric and advanced math functions, and flexible algebraic proportion equations.

---

### 1. Standard Arithmetic & Operations

All basic Python arithmetic operators are supported out of the box.

| Category | Input Syntax | Example Input | Result |
| :--- | :--- | :--- | :--- |
| **Basic Arithmetic** | `+`, `-`, `*`, `/` | `(200 + 4) / 12` | `= 17` |
| **Exponents / Powers** | `**` | `2 ** 8` | `= 256` |
| **Square Roots** | `** 0.5` | `144 ** 0.5` | `= 12` |
| **N-th Roots** | `** (1/n)` | `27 ** (1/3)` | `= 3` |
| **Integer Division** | `//` | `100 // 7` | `= 14` |
| **Modulo (Remainder)** | `%` | `100 % 7` | `= 2` |

---

### 2. Advanced Math Functions & Constants

Common mathematical functions and constants can be called directly without prefixing `math.`.

### Functions & Aggregations
| Function | Description | Example Input | Result |
| :--- | :--- | :--- | :--- |
| `abs(x)` | Absolute value | `abs(-42.5)` | `= 42.5` |
| `round(x, n)` | Round to $n$ decimal places | `round(17 / 30, 4)` | `= 0.5667` |
| `sqrt(x)` | Square root function | `sqrt(144) + 10` | `= 22` |
| `log(x)` | Natural logarithm ($\ln$) | `log(10)` | `= 2.3026` |
| `log10(x)` | Base-10 logarithm | `log10(100)` | `= 2` |
| `factorial(n)` | Factorial ($n!$) | `factorial(5)` | `= 120` |
| `sum([a, b, ...])` | Sum of a list | `sum([12.50, 45.00, 100.25])` | `= 157.75` |
| `min(...)` / `max(...)` | Minimum or maximum value | `max(14.2, 98.6, 50.0)` | `= 98.6` |

### Trigonometry
Trigonometric functions accept angles in **radians**. To evaluate using **degrees**, wrap the input angle in `radians()`.

| Function / Type | Example Input | Result |
| :--- | :--- | :--- |
| **Sine (Radians)** | `sin(1.5708)` | `= 1` |
| **Sine (Degrees)** | `sin(radians(30))` | `= 0.5` |
| **Cosine (Degrees)** | `cos(radians(60))` | `= 0.5` |
| **Tangent (Degrees)** | `tan(radians(45))` | `= 1` |
| **Inverse Sine (Arcsine)** | `degrees(asin(0.5))` | `= 30` |

### Constants
| Constant | Symbol | Input Syntax | Value |
| :--- | :---: | :--- | :--- |
| **Pi** | $\pi$ | `pi` | `3.1416` |
| **Euler's Number** | $e$ | `e` | `2.7183` |

*Example using constants:* `2 * pi * 10` $\rightarrow$ `= 62.8319`

---

### 3. Algebraic Proportion Ratios

The calculator automatically detects and solves proportion ratios for any non-numeric variable name or symbol (e.g., `x`, `price`, `target`, `?`). 

It handles word-based phrasing, ratio colons, equation slashes, and mixed syntax styles.

### Supported Proportion Syntax Styles

| Style | Pattern Example | Input Example | Solved Output |
| :--- | :--- | :--- | :--- |
| **Text Phrase** | `A is to B as var is to D` | `17 is to 30 as price is to 170` | `= 96.3333` |
| **Fraction Equation** | `A/B = var/D` | `17/30 = x/170` | `= 96.3333` |
| **Colon Notation** | `A:B :: var:D` | `17:30 :: ? : 170` | `= 96.3333` |
| **Mixed Slash/Text** | `A/B as var/D` | `17/30 as x/170` | `= 96.3333` |
| **Mixed Colon/Equals** | `A:B = var/D` | `17:30 = target/170` | `= 96.3333` |

### Variable Positioning
The unknown variable can occupy any of the four positions in the ratio:

* **Position 1 ($A$):** `cost / 50 = 3 / 10` $\rightarrow$ `= 15`
* **Position 2 ($B$):** `100 / price = 4 / 20` $\rightarrow$ `= 500`
* **Position 3 ($C$):** `17/30 = x/170` $\rightarrow$ `= 96.3333`
* **Position 4 ($D$):** `4 : 8 :: 12 : ?` $\rightarrow$ `= 24`

---

### 4. Complex Compound Expressions

You can combine standard financial calculations, powers, and math built-ins into single-line entries:

```python
# Compound interest over 5 years at 5%:
1500 * (1 + 0.05) ** 5

# Hypotenuse of a right triangle (a² + b² = c²):
sqrt(3**2 + 4**2)

# Compound expression with rounding:
round(1000 * (1 + 0.07/12)**(12*10), 2)
```
---

**Enjoy!**
