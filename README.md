MyCompanion
MyCompanion is a lightning-fast, lightweight desktop assistant that stays resident in the background, giving you instant access to quick notes, a calculator with saved history, and a dual-month calendar—all summoned or hidden with a single global hotkey.

Designed for minimal friction and maximum speed, it runs quietly as a single-instance daemon and stays out of your way until you need it.

✨ Features
Global Hotkey Toggle: Press Ctrl + Space from anywhere in your operating system to instantly pull up or hide the application window.

Tab 1: Notes – Ctrl-1: A clean, distraction-free markdown/text scratchpad with automatic saving.

Tab 2: Calculator & History – Ctrl-2:  Type out standard math expressions and hit Enter. Keeps an automatic, reverse-chronological history log (most recent at the top) saved across sessions.

Tab 3: Calendar & Calendar Notes – Ctrl-3: Displays a side-by-side view of the current and next month with today's date dynamically highlighted in bright yellow, backed by dedicated calendar notes.

Optional AI Gemini Query and Response – Ctrl-a

SETUP GEMINI AI: (if you want AI Query/Response)
  1. Generate an API key at: https://aistudio.google.com/app/apikey 
     (create project name, import projects, create project api_key - this is subject to change) 
  2. Export the key in your terminal session before launching:
     export GEMINI_API_KEY="AIzaSyYourKeyHere"

Live Header Clock: Displays the current date, live time, and day of the week at a glance.

Fast Navigation Shortcuts: Switch tabs instantly using Ctrl+1, Ctrl+2, or Ctrl+3, and quit cleanly with Ctrl+Q.

🛠️ Prerequisites
Python 3.x

Tkinter (usually bundled with Python on Linux/macOS/Windows)

pynput (for global hotkey listening)

You can install the required dependency via pip:

Bash
pip install pynput
🚀 Running the App
Clone the repository and run the script directly from your terminal:
  
Install these if you want to use Gemini AI
pip install google-genai 
pip install tiktoken --prefer-binary # only if your system complains that it is missing

Bash
python mycompanion.py
On first launch, the program automatically spawns as a background daemon, handles its own lock fileing, and listens for your Ctrl + Space toggle.

📁 Generated Files
To keep your data persistent between sessions, the app automatically creates local text files in your home directory based on the script's root name:

~/{rootname}_notes.txt

~/{rootname}_cal_notes.txt

~/{rootname}_calc_notes.txt
