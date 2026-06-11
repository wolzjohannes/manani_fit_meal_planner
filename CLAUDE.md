# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projekt-Überblick

Flask-Webanwendung für Ernährungscoaches: Erstellt personalisierte Ernährungspläne mit Makro-Tracking, generiert PDFs und Einkaufslisten für Klienten.

---

## 1. Setup & Umgebung

> **Warnung — Python-Version:** `.venv` enthält Python 3.8.12, aber `pyproject.toml` verlangt `>=3.11`. Moderne Typ-Syntax (`X | Y`, `list[X]`, `from __future__ import annotations`) und MyPy strict mode funktionieren nur mit 3.11+. Für neue Arbeit Python 3.11 verwenden.

Keine `requirements.txt` vorhanden — Dependencies via:
```bash
pip install -e .          # aus pyproject.toml installieren
```

### Befehle

```bash
# Entwicklungsserver
python app.py             # → http://localhost:5000 (debug=True)

# Linting
ruff check .

# Formatierung
ruff format .

# Typ-Prüfung
mypy .

# Seed-Daten auf ~500 Gerichte erweitern (nur nach DB-Reset ausführen)
python scripts/expand_seed_data.py
```

Kein Test-Framework vorhanden. `SECRET_KEY` per Env-Variable setzen (Fallback: unsicherer Dev-Key).

---

## README-Pflicht

`README.md` ist die öffentliche Dokumentation dieses Projekts und muss **immer aktuell** gehalten werden.

Bei folgenden Änderungen die README sofort mitaktualisieren:

- Neue Features oder Routen hinzugefügt
- Setup-Schritte oder Abhängigkeiten geändert
- Neue Start-Scripts oder Befehle
- Projektstruktur verändert (neue Ordner, umbenannte Dateien)
- Tech-Stack erweitert (neue Bibliotheken)
- Bekannte Stolpersteine oder Einschränkungen entdeckt

**Regel:** Wer Code ändert, aktualisiert auch die README — kein separater „Doku-Schritt" am Ende.

---

## 2. Architektur-Überblick

### Einstiegspunkte

- `app.py` — `create_app()` → `db.init_app()` → `init_db(app)` → `_register_routes(app)` → `app.run()`
- `database.py` — `init_db()` erstellt alle Tabellen, befüllt DB aus `data/seed_data.json` (nur wenn `FoodItem`-Tabelle leer)

### Datenbankmodelle (`models.py`)

| Modell | Zweck |
|---|---|
| `Client` | Klient mit Biometrie, Allergenen, Restriktionen (Tags als JSON) |
| `MealPlan` | Tagesplan mit kcal-Ziel, verknüpft mit `Client` |
| `MealSlot` | Einzelmahlzeit (3–8 pro Plan); `variants`-Relationship zu beliebig vielen `MealVariant` |
| `MealVariant` | Eine Gericht-Variante (Buchstabe `A`/`B`/`C`…) eines `MealSlot`, verweist auf ein `Dish` |
| `Dish` | Gericht mit Zutaten; `base_kcal` ist computed property über Ingredients |
| `DishIngredient` | Basis-Zutatenmenge (in g) für ein Gericht |
| `PlanDishIngredient` | Skalierte Zutatenmenge für einen konkreten MealSlot |
| `FoodItem` | Nährwerte pro 100 g; `macros_for(amount_g)` berechnet Anteil |
| `MacroTemplate` | Makro-Verhältnis (P%/KH%/F%) nach Fitnessziel |
| `AppSettings` | KV-Store für Branding und Validierungsparameter |

### Kernmodule

| Datei | Einstieg | Rückgabe |
|---|---|---|
| `planner.py` | `generate_plan(plan_id, ...)` | `GenerationResult(plan, warnings)` |
| `planner.py` | `swap_variant(slot, variant, dish_id)` | `None` (tauscht Gericht der Variante) |
| `planner.py` | `add_variant(slot, dish_id)` | `None` (neue Variante mit nächstem Buchstaben) |
| `planner.py` | `remove_variant(slot, variant)` | `None` (entfernt + buchstabiert neu durch) |
| `planner.py` | `get_shopping_list(plan, variant)` | `list[dict]` |
| `pdf_generator.py` | `generate_pdf(plan, upload_folder)` | `bytes` |

**Varianten-Architektur:** Eine Mahlzeit hält N Varianten (`MealSlot.variants` → `MealVariant`).
`PlanDishIngredient.variant` (String-Buchstabe) ordnet skalierte Zutaten einer Variante zu. Die
Generierung erzeugt 2 Varianten (A/B); im Editor lassen sich weitere per `add_variant` hinzufügen bzw.
per `remove_variant` entfernen. Die alten Spalten `variant_a_dish_id`/`variant_b_dish_id` wurden durch
`MealVariant` ersetzt (Backfill via `_migrate_meal_variants` in `database.py`).

### Datenfluss: Plan erstellen

```
POST /plans/generate
  → planner.generate_plan()
      → _slot_kcal_targets()          # kcal auf Mahlzeiten verteilen
      → select_dish_variants()         # 2 Gerichte pro Slot wählen
          → _scale_dish()              # Zutaten proportional skalieren
      → _validate_daily_macros()       # Warnungen generieren
      → db.session.commit()
  → redirect /plans/<id>/edit
      → POST /plans/<id>/swap_variant  # einzelne Variante tauschen
  → GET /plans/<id>/pdf
      → pdf_generator.generate_pdf()
```

---

## 3. Neue Route hinzufügen

Alle Routen werden als nested functions in `_register_routes(app)` in `app.py` definiert:

```python
def _register_routes(app: Flask) -> None:
    # ... bestehende Routen ...

    @app.route("/entity/<int:entity_id>/action", methods=["GET", "POST"])
    def entity_action(entity_id: int) -> Response | str:
        entity = db.get_or_404(Entity, entity_id)
        # ...
        flash("Erfolgreich gespeichert.", "success")
        return redirect(url_for("entity_list"))
```

**Konventionen:**
- Funktionsname: `entity_action` (z.B. `clients_list`, `plans_generate`, `dishes_edit`)
- 404: `db.get_or_404(Model, id)` statt manuellem `abort(404)`
- 400: `abort(400)` bei ungültiger Zuordnung (z.B. Slot gehört nicht zu Plan)
- Flash-Kategorien: `"success"`, `"warning"`, `"danger"`, `"info"`

---

## 4. Datenbankmodelle — Patterns

### Session-Management

```python
# flush() für ID-Generierung vor abhängigen Inserts verwenden
db.session.add(parent)
db.session.flush()          # parent.id ist jetzt verfügbar

child = Child(parent_id=parent.id)
db.session.add(child)
db.session.commit()         # Nur am Ende einer logischen Operation
```

### JSON-Serialisierung für Listen (Tags, Allergene)

Models mit `list[str]`-Feldern nutzen Getter/Setter-Paare:

```python
def get_restriction_tags(self) -> list[str]:
    return json.loads(self.restriction_tags or "[]")

def set_restriction_tags(self, tags: list[str]) -> None:
    self.restriction_tags = json.dumps(tags, ensure_ascii=False)
```

### Relationships mit Cascade

```python
meal_slots = db.relationship(
    "MealSlot",
    back_populates="plan",
    order_by="MealSlot.position",
    cascade="all, delete-orphan",   # Slots beim Plan-Löschen mitlöschen
)
```

### AppSettings KV-Store

```python
# Lesen
primary_color = AppSettings.get("primary_color", "#2D6A4F")

# Schreiben
AppSettings.set("coach_name", "Mein Studio")
db.session.commit()
```

Bekannte Keys: `coach_name`, `primary_color`, `secondary_color`, `font_family`, `disclaimer_text`, `variant_freedom_text`, `logo_path`, `portion_min_g`, `portion_max_g`, `macro_tolerance_pct`. Default für `variant_freedom_text`: `DEFAULT_VARIANT_FREEDOM_TEXT` in `planner.py`.

### SQLAlchemy 2.0 Kompatibilität

Alle Models setzen `__allow_unmapped__ = True` — notwendig für SQLAlchemy 2.0 strict mode bei ungetypten Column-Deklarationen.

---

## 5. Planer-Algorithmus (`planner.py`)

### Rückgabe-Dataclasses

```python
@dataclass
class MacroSplit:
    kcal: float; protein_g: float; carbs_g: float; fat_g: float

@dataclass
class ValidationWarning:
    meal_slot_position: int | None
    message: str

@dataclass
class GenerationResult:
    plan: MealPlan
    warnings: list[ValidationWarning] = field(default_factory=list)
```

### Dish-Auswahl: 5-stufiger Filter (`select_dish_variants`)

```
1. Kategorie:    Dishes filtern nach Kategorie passend zur Slot-Position
                 (Position 1 → "breakfast", etc.)
2. Allergene:    Dishes ausschließen, deren Zutaten Klient-Allergene enthalten
3. Keywords:     Dishes matchen, die Keywords aus dem Guideline-Text enthalten
                 (Suche in dish.name + dish.search_tags)
4. Wiederholung: Bereits genutzte Dishes bevorzugt vermeiden (via used_dish_ids)
5. Fallback:     Wenn alle Filter leer → erste aktive Dish aus Kategorie
```

Gibt `(dish_a, dish_b)` zurück; wenn nur ein Gericht verfügbar: `(dish, dish)`.

### Skalierung

```python
scale_factor = slot_kcal / dish.base_kcal
# Warnung bei: scale_factor < 0.3 oder > 3.0
# Warnung wenn: skalierte Gesamtmenge außerhalb portion_min_g / portion_max_g
```

### Wichtige Sonderfälle

- **`"leicht"` im Guideline-Text:** Reduziert Portion auf 70% der Slot-kcal (hardcoded, kein i18n).
- **Makro-Template-Fallback:** Wenn Goal nicht in `MacroTemplate` gefunden → 35% P / 45% KH / 20% F.
- **`swap_variant()` / `add_variant()`:** Raisen `ValueError` wenn `dish_id` nicht existiert.
- **`remove_variant()`:** Raises `ValueError` wenn die Variante nicht existiert oder es die letzte ist; nummeriert verbleibende Varianten lückenlos neu (A, B, C…).

---

## 6. PDF-Generierung (`pdf_generator.py`)

### System-Abhängigkeiten

WeasyPrint benötigt native Bibliotheken — müssen separat installiert sein:
```bash
# Ubuntu/Debian
sudo apt install libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0 libffi-dev

# macOS
brew install pango cairo libffi
```

### Wichtige Implementierungsdetails

- **Lazy Import in `app.py`:** `from pdf_generator import generate_pdf` steht innerhalb der Route-Funktion — WeasyPrint wird nicht beim App-Start geladen.
- **Matplotlib Agg-Backend:** `matplotlib.use("Agg")` muss vor dem ersten Plot-Import gesetzt sein — kein Display auf Server.
- **HTML als f-String:** Kein Jinja2-Template — HTML/CSS werden programmatisch per f-string zusammengebaut; Branding via `AppSettings.get()` injiziert.
- **Pie-Chart:** SVG via `BytesIO` → base64 → inline in HTML. Farben hardcoded: `["#2D6A4F", "#95D5B2", "#D8F3DC"]`.
- **Logo:** Aus `upload_folder` gelesen, als Base64 data-URI eingebettet.

### CSS-Paginierung (WeasyPrint-spezifisch)

Seitenlayout über **zwei benannte `@page`-Kontexte** — nicht über `.page`-Padding:

```css
@page { margin: 0; }                          /* Default: Cover (Vollbleed, KEIN Footer) */
@page content {                               /* alle Inhaltsseiten */
  margin: 20mm 18mm 16mm 18mm;                /* untere 16mm = Footer-Band + Reserve */
  background-color: ...;
  @bottom-left  { content: "<coach>";  width: 50%; text-align: left;  border-top: 1px solid #e0e0e0; }
  @bottom-right { content: "<client>"; width: 50%; text-align: right; border-top: 1px solid #e0e0e0; }
}
.page { page: content; }

page-break-after: always;       /* nach Cover/Makro-Seite */
page-break-before: always;      /* Einkaufsliste + Disclaimer */
page-break-inside: avoid;       /* Mahlzeit-Abschnitte zusammenhalten */
.meal-section--continued { page-break-before: always; }  /* Varianten-Fortsetzung */
```

**Generelle Layout-Regel:** Der untere `@page content`-Rand (16mm) reserviert auf **jeder**
physischen Seite Platz für den Footer — so kann Inhalt nie darunter rutschen. Mahlzeiten
fließen per Auto-Fill in eine einzige `<div class="page">`; WeasyPrint paginiert anhand der
atomaren `.meal-section`-Blöcke (`page-break-inside: avoid`).

**Footer = `@page`-Margin-Boxes**, KEIN fixiertes Div (ein `position: fixed`-Element würde
relativ zur Inhaltsfläche statt zum Seitenrand positioniert und erschiene auch auf dem
Cover). `@bottom-left`/`@bottom-right` mit je `width: 50%` ergeben eine **durchgehende**
Trennlinie über die volle Inhaltsbreite (Coach links, Klient/Datum rechts). Eine leere
`@bottom-center`-Box kollabiert und reißt die Linie auf — daher 50/50 statt Mittelbox.
Cover nutzt das Default-`@page` ohne Margin-Boxes → bewusst kein Footer.

**Varianten-Paginierung:** Pro Mahlzeit werden die Varianten in Blöcke zu **max. 4**
gechunkt (`max_variants_per_page` in `_render_html`). Jeder Block ist eine eigene
`.meal-section` mit identisch wiederholtem Trenner; Fortsetzungsblöcke (ab dem 5. Variant)
erzwingen via `.meal-section--continued` einen Seitenumbruch.

**Einkaufsliste-Paginierung:** Analog werden die Varianten-Spalten zu **max. 3** pro Seite
gechunkt (`shopping_cols_per_page`); jede Gruppe ist eine eigene `.shopping-section`
(`page-break-before: always`) mit wiederholter „Einkaufsliste"-Überschrift. `.shopping-table`
nutzt `table-layout: fixed` für gleich breite Spalten.

---

## 7. Frontend-Templates

### Vorschau ↔ PDF Konsistenz (Pflicht)

`/plans/<id>/preview` (HTML-Vorschau) und `/plans/<id>/pdf` (WeasyPrint-PDF) müssen visuell stets übereinstimmen:
- Gleiches Logo, gleiche Farben, gleiches Cover-Hintergrundbild
- Gleicher Stil für Mahlzeiten-Trenner, Makro-Zeilen, Einkaufslisten-Header
- Wer eine der beiden Seiten ändert (`templates/plans/preview.html` oder `pdf_generator.py`), aktualisiert die andere ebenfalls

### Template-Blöcke (`base.html`)

Nur zwei Blöcke definiert:
- `title` — Seiten-Titel (Default: "MANANI FIT Meal Planner")
- `content` — Seiteninhalt

### HTMX-Verwendung

HTMX 1.9.12 ist geladen, wird aber **minimal** genutzt — nur auf `plans/creator.html`:

```html
<!-- Client-Select lädt Klient-Info nach -->
<select name="client_id" id="client_id"
        hx-get="{{ url_for('plans_new') }}"
        hx-target="#client-info"
        hx-include="#client_id"
        hx-trigger="change">
```

Alle anderen Formulare nutzen traditionelles POST (Full-Page-Reload).

### CSS-Variablen (`static/css/app.css`)

```css
--primary: #2D6A4F        /* Dunkelgrün — Buttons, Links, Akzente */
--secondary: #95D5B2      /* Hellgrün — Badges, Highlights */
--bg: #F8FAF9             /* Seitenhintergrund */
--surface: #FFFFFF        /* Karten */
--danger: #C0392B         /* Löschen-Buttons */
--warning: #E67E22        /* Warnungen */
--radius: 8px
```

Anpassungen über `AppSettings` (`primary_color`, `secondary_color`) fließen nur ins **PDF** — nicht in die Web-UI.

### JavaScript-Muster

- **Dynamische Zutaten-Zeilen** (`dishes/form.html`): `<template>`-Element-Cloning — neue Zeile per `template.content.cloneNode(true)` hinzufügen.
- **Lösch-Bestätigung:** `onsubmit="return confirm('...')"` auf Delete-Formularen.
- **Farbfelder** (`settings.html`): `oninput` synchronisiert Color-Picker mit Hex-Input.

---

## 8. Bekannte Stolpersteine

| Problem | Details |
|---|---|
| **SQLite-Pfad** | Liegt in **Projekt-Root** (`manani_fit.db`), nicht in `instance/` — trotz Flask-Standard |
| **Seed läuft nur einmal** | Guard: `FoodItem.query.count() == 0` in `database.py`; für Reset DB löschen |
| **Datenbank erweitern** | `python scripts/expand_seed_data.py` → `rm manani_fit.db` → `python app.py` (Skript erweitert `data/seed_data.json` auf ~500 Gerichte) |
| **`"leicht"`-Keyword** | Im Guideline-Text aktiviert 70%-Portionsreduktion — deutsch hardcoded in `planner.py` |
| **Makro-Fallback** | Goal ohne passendes `MacroTemplate` → 35% P / 45% KH / 20% F (hardcoded) |
| **WeasyPrint-Import** | Lazy import innerhalb der PDF-Route — nicht auf Top-Level verschieben |
| **Matplotlib-Backend** | `matplotlib.use("Agg")` muss vor Plot-Imports stehen — nicht entfernen |
| **`__allow_unmapped__`** | Auf allen Models gesetzt für SQLAlchemy 2.0 Kompatibilität — nicht entfernen |
