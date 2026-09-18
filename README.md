# MyCompanion

MyCompanion is a lightning-fast, lightweight desktop assistant that stays resident in the background, giving you instant access to quick notes, a calculator with saved history, and a dual-month calendar—all summoned or hidden with a single global hotkey. Optional Gemini AI query and response.

Designed for minimal friction and maximum speed, it runs quietly as a single-instance daemon and stays out of your way until you need it.

A live header clock displays the current date, live time, and day of the week at a glance.

The app allows wiki-like links to other files.

## ✨ Features
Global Hotkey Toggle: Press Ctrl + Space from anywhere in your operating system to instantly pull up or hide the application window.

Tab 1: Notes – Ctrl-1: A clean, distraction-free markdown/text scratchpad with automatic saving.

Tab 2: Calculator & History – Ctrl-2:  Type out standard math expressions and hit Enter. Keeps an automatic, reverse-chronological history log (most recent at the top) saved across sessions. The calculator history is editable for adding any annotations you desire.

Tab 3: Calendar & Calendar Notes – Ctrl-3: Displays a side-by-side view of the current and next month with today's date dynamically highlighted in bright yellow, backed by dedicated calendar notes.

Tab 4: Todo – Ctrl-4: Dedicated task tracking pane to manage, edit, and organize daily action items and checklists.

## 🤖 Optional AI Gemini Query and Response – Ctrl-a if launched with --ai option.

- Set up your Gemini API Key: Generate an API key at Google AI Studio.

Bash
export GEMINI_API_KEY="AI-YourKeyHere"
SETUP GEMINI AI: (if you want AI Query/Response)
  1. Generate an API key at: https://aistudio.google.com/app/apikey 
     (create project name, import projects, create project api_key - this is subject to change) 
  2. Export the key in your terminal session before launching:
     export GEMINI_API_KEY="AI-YourKeyHere"



## 🛠️ Prerequisites
Python 3.x

Tkinter (usually bundled with Python on Linux/macOS/Windows)

pynput (for global hotkey listening)


You can install the required dependency via pip:

Bash
pip install pynput

Using HTTPS:


## 📥 Installation

Bash
pip install git+https://github.com/your-username/mycompanion.git


Using SSH:
Bash
pip install git+ssh://git@github.com/your-username/mycompanion.git


## 🚀 Running the App
Clone the repository and run the script directly from your terminal:
  
(Optional) Install these if you want to use Gemini AI
pip install google-genai 
pip install tiktoken --prefer-binary # only if your system complains that it is missing

Bash
python mycompanion.py
On first launch, the program automatically spawns as a background daemon, handles its own lock fileing, and listens for your Ctrl + Space toggle.

## 💻 Command-Line Interface
MyCompanion supports command-line flags for quick terminal editing:
    - use mycompanion.py --ai for AI prompt query and response # see above for configuring Gemini AI
    - use mycompanion.py --vim for launching vim as you editor for all edits

## 💻 Running navigation commands:
    - Ctrl-q      to quit and drop mycompanion out of memory (this is the only way to drop it out of memory) It saves data and status on exit.
    - Ctrl-space  toggles all active windows to the top - or to drop them back into the background (but still resident in memory) all data and status is saved
    - Ctrl-t      activates a theme selection window - selection gets saved to mycompanion.conf
    - Ctrl-1      make note pane active
    - Ctrl-2      make calc pane active
    - Ctrl-3      make calendar pane active
    - Ctrl-4      make todo pane active
    - Ctrl-a      active AI query and response windows if ai has been set up
    - Ctrl-v      active vim editing on current pane is vim mode option is active
    - Ctrl-s      if text is selected a new file choice window opens and navigates to another file for saving the selected text. (There is a button for this as well)

##

## 📁 Generated Files
To keep your data persistent between sessions, the app automatically creates local text files in your home directory based on the script's root name:

~/r<platform_dependant>/{rootname}_notes.txt

~/<platform_dependant>/{rootname}_cal_notes.txt

~/<platform_dependant>/{rootname}_calc_notes.txt

~/<platform_dependant>/{rootname}_todo_notes.txt

~/<platform_dependant>/{rootname}.conf  which holds geometry, position, theme, and under [Settings] --ai-mode and --vim-mode

also uses when running:

~/<platform_dependant>/{rootname}.lock

## 🌐 wiki-like connections
    - wiki-like links: use [my_name](file:///home/user/dev/nts/myfile.nts) - link will turn green and allows opening the file names
        Note: if you only use two slashes ie: "//" the link becomes relative (be careful with this)
    - url links are highlighted in blue and when clicked will open a browser on that url - syntax: https://google.com 

Enjoy!
