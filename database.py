from __future__ import annotations

import json
import logging
from pathlib import Path

from models import (
    AppSettings,
    Dish,
    DishIngredient,
    FoodItem,
    MacroTemplate,
    MealVariant,
    Supplement,
    db,
)

_LOGGER = logging.getLogger(__name__)

_SEED_PATH = Path(__file__).parent / "data" / "seed_data.json"


def init_db(app) -> None:
    """Erstellt alle Tabellen und befüllt sie mit Seed-Daten falls leer."""
    with app.app_context():
        db.create_all()
        _migrate_macro_template_columns(app)
        _migrate_macro_overrides_columns(app)
        _migrate_supplement_tables(app)
        _migrate_meal_variants(app)
        if FoodItem.query.count() == 0:
            _seed(app)
        _seed_protein_rolls(app)


def _migrate_macro_overrides_columns(app) -> None:
    """Fügt macro_overrides-Spalte zu clients und meal_plans hinzu, falls fehlend."""
    engine = db.engine
    for table in ("clients", "meal_plans"):
        with engine.connect() as conn:
            result = conn.execute(db.text(f"PRAGMA table_info({table})"))
            existing = {row[1] for row in result}
        if "macro_overrides" not in existing:
            with engine.begin() as conn:
                conn.execute(
                    db.text(f"ALTER TABLE {table} ADD COLUMN macro_overrides TEXT")
                )
            _LOGGER.info("Migration: Spalte 'macro_overrides' in %s hinzugefügt.", table)


def _migrate_macro_template_columns(app) -> None:
    """Fügt neue Spalten in macro_templates hinzu, falls sie noch fehlen (SQLite)."""
    engine = db.engine
    with engine.connect() as conn:
        result = conn.execute(db.text("PRAGMA table_info(macro_templates)"))
        existing = {row[1] for row in result}

    new_columns = {
        "calculation_mode": (
            "ALTER TABLE macro_templates"
            " ADD COLUMN calculation_mode VARCHAR(10) NOT NULL DEFAULT 'pct'"
        ),
        "protein_g_per_kg": (
            "ALTER TABLE macro_templates ADD COLUMN protein_g_per_kg FLOAT"
        ),
        "fat_g_per_kg": (
            "ALTER TABLE macro_templates ADD COLUMN fat_g_per_kg FLOAT"
        ),
    }
    for col, ddl in new_columns.items():
        if col not in existing:
            with engine.begin() as conn:
                conn.execute(db.text(ddl))
            _LOGGER.info("Migration: Spalte '%s' in macro_templates hinzugefügt.", col)


def _migrate_supplement_tables(app) -> None:
    """Erstellt supplements-Tabelle und stellt plan_supplements auf supplement_id um."""
    engine = db.engine

    with engine.connect() as conn:
        result = conn.execute(
            db.text(
                "SELECT COUNT(*) as cnt FROM supplements"
            )
        )
        supp_count = result.fetchone()[0]

    if supp_count == 0:
        with engine.begin() as conn:
            _seed_supplements_sql(conn)
        _LOGGER.info("Supplement-Standardliste eingefügt.")

    with engine.connect() as conn:
        result = conn.execute(db.text("PRAGMA table_info(plan_supplements)"))
        cols = {row[1] for row in result}

    if "dish_id" in cols:
        with engine.begin() as conn:
            conn.execute(db.text("DROP TABLE IF EXISTS plan_supplements"))
            conn.execute(
                db.text("""
                    CREATE TABLE plan_supplements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plan_id INTEGER NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
                        supplement_id INTEGER NOT NULL REFERENCES supplements(id),
                        amount VARCHAR(50),
                        unit_override VARCHAR(30),
                        note VARCHAR(500),
                        position INTEGER DEFAULT 0
                    )
                """)
            )
        _LOGGER.info("Migration: plan_supplements auf supplement_id umgestellt.")

    # Prüfe ob unit_override-Spalte existiert
    with engine.connect() as conn:
        result = conn.execute(db.text("PRAGMA table_info(plan_supplements)"))
        cols = {row[1] for row in result}

    if "unit_override" not in cols:
        with engine.begin() as conn:
            conn.execute(
                db.text("ALTER TABLE plan_supplements ADD COLUMN unit_override VARCHAR(30)")
            )
        _LOGGER.info("Migration: Spalte 'unit_override' zu plan_supplements hinzugefügt.")


def _migrate_meal_variants(app) -> None:
    """Befüllt meal_variants aus den alten variant_a/b_dish_id-Spalten (einmalig).

    Die Tabelle meal_variants wird von db.create_all() angelegt. Bestehende Pläne
    halten ihre Varianten noch in den alten Spalten variant_a_dish_id /
    variant_b_dish_id — diese werden hier nach meal_variants übertragen.
    """
    if MealVariant.query.count() > 0:
        return

    engine = db.engine
    with engine.connect() as conn:
        result = conn.execute(db.text("PRAGMA table_info(meal_slots)"))
        cols = {row[1] for row in result}
    if "variant_a_dish_id" not in cols:
        return

    with engine.connect() as conn:
        rows = conn.execute(
            db.text(
                "SELECT id, variant_a_dish_id, variant_b_dish_id FROM meal_slots"
            )
        ).fetchall()

    migrated = 0
    for slot_id, dish_a, dish_b in rows:
        for letter, dish_id in (("A", dish_a), ("B", dish_b)):
            if dish_id is not None:
                db.session.add(
                    MealVariant(
                        meal_slot_id=slot_id, variant=letter, dish_id=dish_id
                    )
                )
                migrated += 1
    if migrated:
        db.session.commit()
        _LOGGER.info(
            "Migration: %d Varianten nach meal_variants übertragen.", migrated
        )


_PROTEIN_FOOD_ITEMS = [
    {
        "name": "Eiweißbrötchen",
        "kcal_per_100g": 250,
        "protein_per_100g": 26.0,
        "carbs_per_100g": 9.0,
        "fat_per_100g": 11.0,
        "allergens": ["gluten"],
    },
    {
        "name": "Hähnchenbrust-Aufschnitt",
        "kcal_per_100g": 110,
        "protein_per_100g": 20.0,
        "carbs_per_100g": 1.0,
        "fat_per_100g": 2.5,
        "allergens": [],
    },
]

_PROTEIN_DISHES = [
    {
        "name": "Eiweißbrötchen mit Hähnchenaufschnitt",
        "category": "breakfast",
        "description": "Eiweißbrötchen belegt mit magerem Hähnchenaufschnitt, "
        "Gurke und Tomate.",
        "tags": ["high-protein", "schnelle Zubereitung", "gluten"],
        "ingredients": [
            {"food_item": "Eiweißbrötchen", "base_amount_g": 120},
            {"food_item": "Hähnchenbrust-Aufschnitt", "base_amount_g": 60},
            {"food_item": "Gurke", "base_amount_g": 40},
            {"food_item": "Tomaten (frisch)", "base_amount_g": 40},
        ],
    },
    {
        "name": "Eiweißbrötchen mit Magerquark & Putenaufschnitt",
        "category": "snack",
        "description": "Eiweißbrötchen mit Magerquark-Aufstrich und Putenaufschnitt.",
        "tags": ["high-protein", "snack", "gluten"],
        "ingredients": [
            {"food_item": "Eiweißbrötchen", "base_amount_g": 100},
            {"food_item": "Magerquark", "base_amount_g": 50},
            {"food_item": "Putenbrust", "base_amount_g": 50},
            {"food_item": "Gurke", "base_amount_g": 30},
        ],
    },
    {
        "name": "Eiweißbrötchen-Sandwich mit Hähnchen & Gurke",
        "category": "lunch",
        "description": "Herzhaftes Eiweißbrötchen-Sandwich mit Hähnchenaufschnitt, "
        "Avocado, Gurke und Rucola.",
        "tags": ["high-protein", "sandwich", "gluten"],
        "ingredients": [
            {"food_item": "Eiweißbrötchen", "base_amount_g": 120},
            {"food_item": "Hähnchenbrust-Aufschnitt", "base_amount_g": 70},
            {"food_item": "Avocado", "base_amount_g": 30},
            {"food_item": "Gurke", "base_amount_g": 50},
            {"food_item": "Rucola", "base_amount_g": 20},
        ],
    },
    {
        "name": "Eiweißbrötchen mit Ei & Hähnchenaufschnitt",
        "category": "breakfast",
        "description": "Eiweißbrötchen mit gekochtem Ei, Hähnchenaufschnitt und Tomate.",
        "tags": ["high-protein", "frühstück", "gluten"],
        "ingredients": [
            {"food_item": "Eiweißbrötchen", "base_amount_g": 120},
            {"food_item": "Eier", "base_amount_g": 60},
            {"food_item": "Hähnchenbrust-Aufschnitt", "base_amount_g": 50},
            {"food_item": "Tomaten (frisch)", "base_amount_g": 40},
        ],
    },
]


def _seed_protein_rolls(app) -> None:
    """Fügt Eiweißbrötchen-/Hähnchenaufschnitt-Lebensmittel und -Gerichte ein.

    Idempotent: läuft nur, wenn das FoodItem „Eiweißbrötchen" noch fehlt. Dadurch
    landen die neuen Einträge auch in einer bereits befüllten Live-DB.
    """
    if FoodItem.query.filter_by(name="Eiweißbrötchen").first() is not None:
        return

    for fi_data in _PROTEIN_FOOD_ITEMS:
        if FoodItem.query.filter_by(name=fi_data["name"]).first() is not None:
            continue
        fi = FoodItem(
            name=fi_data["name"],
            kcal_per_100g=fi_data["kcal_per_100g"],
            protein_per_100g=fi_data["protein_per_100g"],
            carbs_per_100g=fi_data["carbs_per_100g"],
            fat_per_100g=fi_data["fat_per_100g"],
        )
        fi.set_allergens(fi_data["allergens"])
        db.session.add(fi)
    db.session.flush()

    for dish_data in _PROTEIN_DISHES:
        if Dish.query.filter_by(name=dish_data["name"]).first() is not None:
            continue
        dish = Dish(
            name=dish_data["name"],
            category=dish_data["category"],
            description=dish_data["description"],
            is_custom=False,
        )
        dish.set_tags(dish_data["tags"])
        db.session.add(dish)
        db.session.flush()

        for ing in dish_data["ingredients"]:
            food_item = FoodItem.query.filter_by(name=ing["food_item"]).first()
            if food_item is None:
                _LOGGER.warning(
                    "Lebensmittel nicht gefunden: %s (Gericht: %s)",
                    ing["food_item"],
                    dish_data["name"],
                )
                continue
            db.session.add(
                DishIngredient(
                    dish_id=dish.id,
                    food_item_id=food_item.id,
                    base_amount_g=ing["base_amount_g"],
                )
            )

    db.session.commit()
    _LOGGER.info("Eiweißbrötchen-/Aufschnitt-Gerichte eingefügt.")


def _seed_supplements_sql(conn) -> None:
    """Befüllt die supplements-Tabelle mit einer Standardliste (raw SQL)."""
    entries = [
        ("Omega-3 Fischöl", "Kapsel", "EPA/DHA für Herzgesundheit und Entzündungshemmung"),
        ("Vitamin D3", "Kapsel", "Fettlösliches Vitamin, wichtig für Knochen und Immunsystem"),
        ("Magnesium", "Tablette", "Mineral für Muskel- und Nervenfunktion"),
        ("Zink", "Kapsel", "Spurenelement für Immunsystem und Testosteronproduktion"),
        ("Vitamin C", "Tablette", "Antioxidans und Immunstütze"),
        ("B-Komplex", "Kapsel", "B-Vitamine für Energie und Nervensystem"),
        ("Kreatin Monohydrat", "g", "Für Kraftsteigerung und Muskelaufbau"),
        ("Proteinpulver Whey", "g", "Schnell verfügbares Protein nach dem Training"),
        ("Casein Protein", "g", "Langsam verdauliches Protein, ideal vor dem Schlafen"),
        ("BCAA", "g", "Verzweigtkettige Aminosäuren für Muskelregeneration"),
        ("L-Glutamin", "g", "Aminosäure für Darmgesundheit und Regeneration"),
        ("Ashwagandha", "Kapsel", "Adaptogen für Stressreduktion und Erholung"),
        ("Coenzym Q10", "Kapsel", "Antioxidans für Zellenergie und Herzgesundheit"),
        ("Kurkuma / Curcumin", "Kapsel", "Entzündungshemmend, antioxidativ"),
        ("Probiotikum", "Kapsel", "Lebende Bakterienkulturen für die Darmflora"),
        ("Melatonin", "mg", "Schlafhormon für bessere Schlafqualität"),
        ("L-Carnitin", "ml", "Transportiert Fettsäuren in die Mitochondrien"),
        ("Eisen", "mg", "Spurenelement für Blutbildung und Sauerstofftransport"),
        ("Folsäure", "µg", "B-Vitamin, wichtig bei Schwangerschaft und Zellteilung"),
        ("Multivitamin", "Tablette", "Kombinationspräparat mit Vitaminen und Mineralstoffen"),
    ]
    for name, unit, desc in entries:
        conn.execute(db.text("""
            INSERT INTO supplements (name, unit, description, is_active)
            VALUES (:name, :unit, :desc, 1)
        """), {"name": name, "unit": unit, "desc": desc})
    _LOGGER.info("Supplement-Standardliste eingefügt (%d Einträge).", len(entries))


def _seed(app) -> None:
    """Befüllt die DB mit Starter-Gerichten und Standard-Einstellungen."""
    _LOGGER.info("Seed-Daten werden geladen: %s", _SEED_PATH)
    data = json.loads(_SEED_PATH.read_text(encoding="utf-8"))

    food_map: dict[str, FoodItem] = {}
    for fi_data in data["food_items"]:
        fi = FoodItem(
            name=fi_data["name"],
            kcal_per_100g=fi_data["kcal_per_100g"],
            protein_per_100g=fi_data["protein_per_100g"],
            carbs_per_100g=fi_data["carbs_per_100g"],
            fat_per_100g=fi_data["fat_per_100g"],
            is_supplement=fi_data.get("is_supplement", False),
        )
        fi.set_allergens(fi_data.get("allergens", []))
        db.session.add(fi)
        food_map[fi_data["name"]] = fi

    db.session.flush()

    for dish_data in data["dishes"]:
        dish = Dish(
            name=dish_data["name"],
            category=dish_data["category"],
            description=dish_data.get("description"),
            is_custom=False,
        )
        dish.set_tags(dish_data.get("tags", []))
        db.session.add(dish)
        db.session.flush()

        for ing in dish_data["ingredients"]:
            food_item = food_map.get(ing["food_item"])
            if food_item is None:
                _LOGGER.warning(
                    "Lebensmittel nicht gefunden: %s (Gericht: %s)",
                    ing["food_item"],
                    dish_data["name"],
                )
                continue
            db.session.add(
                DishIngredient(
                    dish_id=dish.id,
                    food_item_id=food_item.id,
                    base_amount_g=ing["base_amount_g"],
                )
            )

    for tmpl in data["macro_templates"]:
        db.session.add(
            MacroTemplate(
                goal_name=tmpl["goal_name"],
                protein_pct=tmpl["protein_pct"],
                carbs_pct=tmpl["carbs_pct"],
                fat_pct=tmpl["fat_pct"],
            )
        )

    for key, value in data["app_settings"].items():
        db.session.add(AppSettings(key=key, value=value))

    db.session.commit()
    _LOGGER.info("Seed abgeschlossen.")
