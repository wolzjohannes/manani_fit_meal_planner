from __future__ import annotations

import json
import logging
from pathlib import Path

from models import AppSettings, Dish, DishIngredient, FoodItem, MacroTemplate, db

_LOGGER = logging.getLogger(__name__)

_SEED_PATH = Path(__file__).parent / "data" / "seed_data.json"


def init_db(app) -> None:
    """Erstellt alle Tabellen und befüllt sie mit Seed-Daten falls leer."""
    with app.app_context():
        db.create_all()
        _migrate_macro_template_columns(app)
        if FoodItem.query.count() == 0:
            _seed(app)


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
