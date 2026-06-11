# MANANI FIT — Meal Planner

A web application for fitness coaches to create personalized meal plans with macro tracking, PDF export, and shopping lists for clients.

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Full Setup Guide](#full-setup-guide)
- [Starting the App](#starting-the-app)
- [First Steps After Launch](#first-steps-after-launch)
- [Expanding the Dish Database](#expanding-the-dish-database)
- [PDF Export](#pdf-export)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)

---

## Features

| Feature | Description |
|---|---|
| Client management | Store client profiles with biometrics, goals, allergies, and dietary restrictions |
| Automated plan generation | Dish selection based on calorie targets, macro ratios, and client restrictions |
| 500+ dishes | Recipe database covering breakfast, lunch, dinner, snacks, and supplements |
| PDF export | Branded PDF with macro pie charts (incl. macro/kcal explainer), shopping list, and coach disclaimer |
| Shopping list | Auto-generated ingredient list with scaled quantities per plan, per variant |
| Multiple variants | Generation creates two variants (A/B) per meal; add or remove further variants (C, D, …) on the edit screen |
| Branding settings | Customize logo, colors, coach name, disclaimer, and the "own variants" hint text under Settings |

---

## Quick Start

> For users who just want to get the app running as fast as possible.

**1. Clone and install**
```bash
git clone https://github.com/your-username/manani_fit_meal_planner.git
cd manani_fit_meal_planner
python -m venv .venv
pip install -e .
```

**2. Start**

| OS | Command |
|---|---|
| Linux | `bash start.sh` |
| macOS | `bash start_mac.sh` |
| Windows | Double-click `start.bat` |

The browser opens automatically at **http://localhost:5000**.

---

## Full Setup Guide

### Requirements

- **Python 3.11 or newer** — check with `python --version`
- **pip** — comes bundled with Python
- **Git** — to clone the repository

> **Important:** The virtual environment (`.venv`) must be created with Python 3.11+.
> The app uses modern type syntax (`X | Y`, `list[X]`) that does not work on Python 3.8 or 3.9.

### Step 1 — Clone the repository

```bash
git clone https://github.com/your-username/manani_fit_meal_planner.git
cd manani_fit_meal_planner
```

### Step 2 — Create a virtual environment

```bash
python3.11 -m venv .venv
```

### Step 3 — Activate the virtual environment

**Linux / macOS:**
```bash
source .venv/bin/activate
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

You will see `(.venv)` at the start of your terminal prompt when active.

### Step 4 — Install dependencies

```bash
pip install -e .
```

This reads `pyproject.toml` and installs all required packages (Flask, SQLAlchemy, WeasyPrint, etc.).

### Step 5 — Install system libraries for PDF export

WeasyPrint needs native graphics libraries that are not installed via pip.

**Ubuntu / Debian:**
```bash
sudo apt install libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0 libffi-dev
```

**macOS:**
```bash
brew install pango cairo libffi
```

**Windows:** Follow the [WeasyPrint Windows installation guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows).

> If you skip this step, everything works except PDF generation — the app will throw an error only when you try to export a PDF.

---

## Starting the App

### Linux — `start.sh`

```bash
bash start.sh
```

Or place it on your desktop and double-click (one-time setup):
```bash
chmod +x start.sh
```
Then right-click the file on the desktop → **Allow launching**.

### macOS — `start_mac.sh`

```bash
bash start_mac.sh
```

Make it double-clickable from Finder (one-time setup):
```bash
chmod +x start_mac.sh
```
Then right-click in Finder → **Open** (required once to bypass Gatekeeper).

### Windows — `start.bat`

Double-click `start.bat`. If Windows Defender SmartScreen blocks it, click **More info → Run anyway**.

### What the start scripts do

1. Navigate to the project folder automatically
2. Activate the Python virtual environment
3. Start the Flask server in the background (`http://localhost:5000`)
4. Wait 2 seconds for the server to boot
5. Open your default browser at `http://localhost:5000`

### Starting manually (without the scripts)

```bash
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
python app.py
```

Then open **http://localhost:5000** in your browser.

---

## First Steps After Launch

1. **Go to Settings** (top-right nav) — enter your coach name and upload your logo
2. **Add a client** — click *Clients* → *Neuer Client*, fill in biometrics and fitness goal
3. **Generate a plan** — click *Neuer Plan*, select the client and calorie target, click generate
4. **Edit the plan** — swap dish variants, or add/remove additional variants (C, D, …) per meal on the edit screen
5. **Export PDF** — click the PDF button on the plan edit screen to download the client document

---

## Expanding the Dish Database

The app automatically seeds ~500 dishes and 109 food items on first launch (when the database is empty).

To regenerate the database after a reset, or to re-run the seed script with updated data:

```bash
# 1. Expand seed_data.json to ~500 dishes (only needed if you modified the script)
python scripts/expand_seed_data.py

# 2. Delete the existing database
rm manani_fit.db          # Linux / macOS
del manani_fit.db         # Windows

# 3. Restart the app — it will re-seed automatically
python app.py
```

> **Note:** Deleting `manani_fit.db` removes all clients, plans, and settings.
> Only do this on a fresh install or when you intentionally want to reset all data.

---

## PDF Export

The PDF is generated with WeasyPrint and includes:

- **Cover page** — client name, coach branding, calorie target
- **Macro overview** — pie chart (protein / carbs / fat split) plus a short explainer of what calories and macros are
- **Meal plan** — all meal slots with every dish variant and ingredient quantities, plus the "own variants" hint
- **Shopping list** — aggregated ingredients across all meals, one column per variant
- **Disclaimer** — configurable text from Settings

The PDF layout uses fixed-size pages with CSS print rules. Logo and colors are pulled from Settings at generation time.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | Python 3.11, Flask 3 | Web framework, routing, templating |
| ORM | SQLAlchemy 2 | Database models and queries |
| Database | SQLite | Single-file database, no server needed |
| PDF | WeasyPrint | HTML/CSS → PDF rendering |
| Charts | Matplotlib | Macro pie chart in PDF |
| Frontend | Jinja2, HTMX 1.9 | Server-rendered templates, dynamic client select |
| Styling | Custom CSS (dark theme) | No CSS framework — hand-crafted styles |

---

## Project Structure

```
manani_fit_meal_planner/
│
├── app.py                  # App factory + all routes (single-file routing)
├── models.py               # SQLAlchemy models (Client, MealPlan, Dish, ...)
├── planner.py              # Core meal plan generation logic
├── pdf_generator.py        # PDF and chart generation (WeasyPrint + Matplotlib)
├── database.py             # DB initialization and seed data loader
│
├── data/
│   └── seed_data.json      # Master dish and food item database (~500 dishes)
│
├── scripts/
│   └── expand_seed_data.py # Standalone script to regenerate seed_data.json
│
├── static/
│   ├── css/
│   │   └── app.css         # All styles — dark industrial theme
│   └── uploads/            # Logo, background image, uploaded coach assets
│
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Shared layout (navbar, flash messages)
│   ├── index.html          # Dashboard
│   ├── clients/            # Client list, create, edit
│   ├── plans/              # Plan creator, editor, viewer
│   ├── dishes/             # Dish list, create, edit
│   └── settings.html       # App settings / branding
│
├── start.sh                # Start script — Linux
├── start_mac.sh            # Start script — macOS
├── start.bat               # Start script — Windows
├── pyproject.toml          # Dependencies and project metadata
└── CLAUDE.md               # Developer notes for AI-assisted development
```

---

## License

Private — all rights reserved.
