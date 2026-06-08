#!/usr/bin/env python3
"""Expand seed_data.json to ~500 fitness-appropriate dishes.

Run once (or after a DB reset) to populate a richer dish database:
    python scripts/expand_seed_data.py
    rm manani_fit.db
    python app.py
"""
from __future__ import annotations

import json
from itertools import product
from pathlib import Path

ROOT = Path(__file__).parent.parent
SEED = ROOT / "data" / "seed_data.json"

# ── New FoodItems ─────────────────────────────────────────────────────────────

NEW_FOOD_ITEMS: list[dict] = [
    # Proteins
    {"name": "Putenbrust", "kcal_per_100g": 107, "protein_per_100g": 24.0, "carbs_per_100g": 0.0, "fat_per_100g": 1.5, "allergens": []},
    {"name": "Rindfleisch mager", "kcal_per_100g": 143, "protein_per_100g": 22.0, "carbs_per_100g": 0.0, "fat_per_100g": 6.0, "allergens": []},
    {"name": "Lachsfilet", "kcal_per_100g": 208, "protein_per_100g": 20.0, "carbs_per_100g": 0.0, "fat_per_100g": 14.0, "allergens": ["fisch"]},
    {"name": "Kabeljau", "kcal_per_100g": 82, "protein_per_100g": 18.0, "carbs_per_100g": 0.0, "fat_per_100g": 0.7, "allergens": ["fisch"]},
    {"name": "Garnelen", "kcal_per_100g": 71, "protein_per_100g": 15.0, "carbs_per_100g": 0.5, "fat_per_100g": 0.6, "allergens": ["krebstiere"]},
    {"name": "Lachs geräuchert", "kcal_per_100g": 170, "protein_per_100g": 20.0, "carbs_per_100g": 0.0, "fat_per_100g": 10.0, "allergens": ["fisch"]},
    {"name": "Putenhackfleisch", "kcal_per_100g": 120, "protein_per_100g": 19.0, "carbs_per_100g": 0.0, "fat_per_100g": 5.0, "allergens": []},
    {"name": "Rinderhackfleisch mager", "kcal_per_100g": 135, "protein_per_100g": 18.0, "carbs_per_100g": 0.0, "fat_per_100g": 7.0, "allergens": []},
    {"name": "Griechischer Joghurt (0%)", "kcal_per_100g": 57, "protein_per_100g": 10.0, "carbs_per_100g": 4.0, "fat_per_100g": 0.2, "allergens": ["milch"]},
    {"name": "Eiklar", "kcal_per_100g": 52, "protein_per_100g": 11.0, "carbs_per_100g": 0.7, "fat_per_100g": 0.2, "allergens": ["ei"]},
    {"name": "Edamame", "kcal_per_100g": 122, "protein_per_100g": 11.0, "carbs_per_100g": 8.0, "fat_per_100g": 5.0, "allergens": ["soja"]},
    {"name": "Tempeh", "kcal_per_100g": 195, "protein_per_100g": 19.0, "carbs_per_100g": 8.0, "fat_per_100g": 11.0, "allergens": ["soja"]},
    {"name": "Linsen grün (roh)", "kcal_per_100g": 353, "protein_per_100g": 26.0, "carbs_per_100g": 60.0, "fat_per_100g": 1.5, "allergens": []},
    {"name": "Kichererbsen (gegart)", "kcal_per_100g": 164, "protein_per_100g": 8.9, "carbs_per_100g": 27.0, "fat_per_100g": 2.6, "allergens": []},
    {"name": "Schwarze Bohnen (gegart)", "kcal_per_100g": 132, "protein_per_100g": 8.9, "carbs_per_100g": 24.0, "fat_per_100g": 0.5, "allergens": []},
    {"name": "Kidneybohnen (gegart)", "kcal_per_100g": 127, "protein_per_100g": 8.7, "carbs_per_100g": 22.0, "fat_per_100g": 0.5, "allergens": []},
    {"name": "Proteinpulver Schoko", "kcal_per_100g": 375, "protein_per_100g": 74.0, "carbs_per_100g": 11.0, "fat_per_100g": 4.0, "allergens": ["milch", "soja"], "is_supplement": True},
    {"name": "Casein-Protein", "kcal_per_100g": 360, "protein_per_100g": 75.0, "carbs_per_100g": 6.0, "fat_per_100g": 3.0, "allergens": ["milch"], "is_supplement": True},
    {"name": "Proteinpulver Erdbeere", "kcal_per_100g": 378, "protein_per_100g": 74.0, "carbs_per_100g": 11.0, "fat_per_100g": 4.5, "allergens": ["milch", "soja"], "is_supplement": True},
    # Carbs
    {"name": "Quinoa (roh)", "kcal_per_100g": 368, "protein_per_100g": 14.0, "carbs_per_100g": 64.0, "fat_per_100g": 6.0, "allergens": []},
    {"name": "Vollkorn-Pasta (roh)", "kcal_per_100g": 340, "protein_per_100g": 13.0, "carbs_per_100g": 66.0, "fat_per_100g": 2.5, "allergens": ["gluten", "weizen"]},
    {"name": "Vollkorn-Spaghetti (roh)", "kcal_per_100g": 338, "protein_per_100g": 13.5, "carbs_per_100g": 65.0, "fat_per_100g": 2.5, "allergens": ["gluten", "weizen"]},
    {"name": "Buchweizen (roh)", "kcal_per_100g": 343, "protein_per_100g": 13.0, "carbs_per_100g": 71.0, "fat_per_100g": 3.4, "allergens": []},
    {"name": "Bulgur (roh)", "kcal_per_100g": 342, "protein_per_100g": 12.0, "carbs_per_100g": 72.0, "fat_per_100g": 1.3, "allergens": ["gluten", "weizen"]},
    {"name": "Couscous (roh)", "kcal_per_100g": 376, "protein_per_100g": 13.0, "carbs_per_100g": 77.0, "fat_per_100g": 0.6, "allergens": ["gluten", "weizen"]},
    {"name": "Polenta (roh)", "kcal_per_100g": 362, "protein_per_100g": 8.5, "carbs_per_100g": 76.0, "fat_per_100g": 1.0, "allergens": []},
    {"name": "Reiswaffeln", "kcal_per_100g": 387, "protein_per_100g": 8.0, "carbs_per_100g": 82.0, "fat_per_100g": 2.5, "allergens": []},
    {"name": "Vollkornbrot", "kcal_per_100g": 232, "protein_per_100g": 8.5, "carbs_per_100g": 42.0, "fat_per_100g": 3.0, "allergens": ["gluten", "weizen"]},
    {"name": "Vollkorn-Reis (roh)", "kcal_per_100g": 340, "protein_per_100g": 7.0, "carbs_per_100g": 73.0, "fat_per_100g": 2.2, "allergens": []},
    {"name": "Kartoffeln", "kcal_per_100g": 77, "protein_per_100g": 2.1, "carbs_per_100g": 17.0, "fat_per_100g": 0.1, "allergens": []},
    # Vegetables
    {"name": "Spargel", "kcal_per_100g": 20, "protein_per_100g": 2.2, "carbs_per_100g": 1.8, "fat_per_100g": 0.1, "allergens": []},
    {"name": "Blumenkohl", "kcal_per_100g": 25, "protein_per_100g": 2.0, "carbs_per_100g": 3.0, "fat_per_100g": 0.3, "allergens": []},
    {"name": "Grüne Bohnen", "kcal_per_100g": 31, "protein_per_100g": 1.8, "carbs_per_100g": 5.7, "fat_per_100g": 0.1, "allergens": []},
    {"name": "Pilze (Champignons)", "kcal_per_100g": 22, "protein_per_100g": 3.1, "carbs_per_100g": 2.0, "fat_per_100g": 0.3, "allergens": []},
    {"name": "Aubergine", "kcal_per_100g": 25, "protein_per_100g": 1.0, "carbs_per_100g": 5.7, "fat_per_100g": 0.2, "allergens": []},
    {"name": "Tomaten (frisch)", "kcal_per_100g": 18, "protein_per_100g": 0.9, "carbs_per_100g": 3.5, "fat_per_100g": 0.2, "allergens": []},
    {"name": "Feldsalat", "kcal_per_100g": 22, "protein_per_100g": 2.0, "carbs_per_100g": 2.4, "fat_per_100g": 0.4, "allergens": []},
    {"name": "Rucola", "kcal_per_100g": 25, "protein_per_100g": 2.6, "carbs_per_100g": 2.0, "fat_per_100g": 0.7, "allergens": []},
    {"name": "Rote Beete (gegart)", "kcal_per_100g": 43, "protein_per_100g": 1.6, "carbs_per_100g": 9.5, "fat_per_100g": 0.1, "allergens": []},
    {"name": "Lauch", "kcal_per_100g": 31, "protein_per_100g": 1.8, "carbs_per_100g": 6.0, "fat_per_100g": 0.3, "allergens": []},
    {"name": "Pak Choi", "kcal_per_100g": 13, "protein_per_100g": 1.5, "carbs_per_100g": 1.2, "fat_per_100g": 0.2, "allergens": []},
    {"name": "Erbsen (gefroren)", "kcal_per_100g": 81, "protein_per_100g": 5.4, "carbs_per_100g": 14.0, "fat_per_100g": 0.4, "allergens": []},
    {"name": "Rosenkohl", "kcal_per_100g": 43, "protein_per_100g": 3.4, "carbs_per_100g": 7.0, "fat_per_100g": 0.5, "allergens": []},
    {"name": "Zwiebeln", "kcal_per_100g": 40, "protein_per_100g": 1.1, "carbs_per_100g": 9.3, "fat_per_100g": 0.1, "allergens": []},
    # Fats / nuts
    {"name": "Walnüsse", "kcal_per_100g": 654, "protein_per_100g": 15.0, "carbs_per_100g": 14.0, "fat_per_100g": 65.0, "allergens": ["schalenfrüchte"]},
    {"name": "Mandeln", "kcal_per_100g": 579, "protein_per_100g": 21.0, "carbs_per_100g": 22.0, "fat_per_100g": 50.0, "allergens": ["schalenfrüchte"]},
    {"name": "Avocado", "kcal_per_100g": 160, "protein_per_100g": 2.0, "carbs_per_100g": 8.5, "fat_per_100g": 15.0, "allergens": []},
    {"name": "Chiasamen", "kcal_per_100g": 486, "protein_per_100g": 16.5, "carbs_per_100g": 42.0, "fat_per_100g": 31.0, "allergens": []},
    {"name": "Erdnussbutter", "kcal_per_100g": 588, "protein_per_100g": 25.0, "carbs_per_100g": 20.0, "fat_per_100g": 50.0, "allergens": ["erdnüsse"]},
    {"name": "Tahini", "kcal_per_100g": 595, "protein_per_100g": 17.0, "carbs_per_100g": 21.0, "fat_per_100g": 54.0, "allergens": ["sesam"]},
    {"name": "Kürbiskerne", "kcal_per_100g": 559, "protein_per_100g": 30.0, "carbs_per_100g": 11.0, "fat_per_100g": 49.0, "allergens": ["schalenfrüchte"]},
    {"name": "Kokosmilch light", "kcal_per_100g": 75, "protein_per_100g": 0.8, "carbs_per_100g": 3.5, "fat_per_100g": 6.0, "allergens": []},
    # Fruits
    {"name": "Mango", "kcal_per_100g": 60, "protein_per_100g": 0.8, "carbs_per_100g": 15.0, "fat_per_100g": 0.4, "allergens": []},
    {"name": "Ananas", "kcal_per_100g": 50, "protein_per_100g": 0.5, "carbs_per_100g": 12.0, "fat_per_100g": 0.1, "allergens": []},
    {"name": "Kiwi", "kcal_per_100g": 61, "protein_per_100g": 1.1, "carbs_per_100g": 15.0, "fat_per_100g": 0.5, "allergens": []},
    {"name": "Himbeeren", "kcal_per_100g": 52, "protein_per_100g": 1.2, "carbs_per_100g": 12.0, "fat_per_100g": 0.7, "allergens": []},
    {"name": "Äpfel", "kcal_per_100g": 52, "protein_per_100g": 0.3, "carbs_per_100g": 14.0, "fat_per_100g": 0.2, "allergens": []},
    {"name": "Heidelbeeren", "kcal_per_100g": 57, "protein_per_100g": 0.7, "carbs_per_100g": 14.0, "fat_per_100g": 0.3, "allergens": []},
    {"name": "Granatapfelkerne", "kcal_per_100g": 83, "protein_per_100g": 1.7, "carbs_per_100g": 19.0, "fat_per_100g": 1.2, "allergens": []},
    {"name": "Kirschen", "kcal_per_100g": 63, "protein_per_100g": 1.1, "carbs_per_100g": 16.0, "fat_per_100g": 0.2, "allergens": []},
    # Misc
    {"name": "Mandelmilch ungesüßt", "kcal_per_100g": 13, "protein_per_100g": 0.5, "carbs_per_100g": 0.5, "fat_per_100g": 1.0, "allergens": ["schalenfrüchte"]},
    {"name": "Haferdrink", "kcal_per_100g": 45, "protein_per_100g": 1.0, "carbs_per_100g": 7.0, "fat_per_100g": 1.5, "allergens": ["gluten"]},
    {"name": "Tomatenmark", "kcal_per_100g": 82, "protein_per_100g": 4.5, "carbs_per_100g": 15.0, "fat_per_100g": 0.5, "allergens": []},
    {"name": "Zitronensaft", "kcal_per_100g": 22, "protein_per_100g": 0.4, "carbs_per_100g": 6.9, "fat_per_100g": 0.3, "allergens": []},
    {"name": "Kokosnussöl", "kcal_per_100g": 884, "protein_per_100g": 0.0, "carbs_per_100g": 0.0, "fat_per_100g": 100.0, "allergens": []},
    {"name": "Apfelessig", "kcal_per_100g": 22, "protein_per_100g": 0.0, "carbs_per_100g": 0.9, "fat_per_100g": 0.0, "allergens": []},
    {"name": "Miso-Paste", "kcal_per_100g": 199, "protein_per_100g": 12.0, "carbs_per_100g": 26.0, "fat_per_100g": 6.0, "allergens": ["soja"]},
    {"name": "Kokosraspeln", "kcal_per_100g": 604, "protein_per_100g": 6.0, "carbs_per_100g": 60.0, "fat_per_100g": 40.0, "allergens": []},
]

# ── Component tables for template-based bowl generation ───────────────────────

# (display_name, food_item_name, amount_g, extra_tags)
_ANIMAL_PROTEINS = [
    ("Hähnchenbrust", "Hähnchenbrust", 180, ["high-protein"]),
    ("Putenbrust", "Putenbrust", 175, ["high-protein"]),
    ("Lachsfilet", "Lachsfilet", 160, ["high-protein", "fisch"]),
    ("Kabeljau", "Kabeljau", 180, ["high-protein", "fisch"]),
    ("Thunfisch", "Thunfisch im eigenen Saft", 150, ["high-protein", "fisch"]),
    ("Garnelen", "Garnelen", 170, ["high-protein"]),
    ("Putenhackfleisch", "Putenhackfleisch", 180, ["high-protein"]),
    ("Rindfleisch", "Rindfleisch mager", 160, ["high-protein"]),
]

_PLANT_PROTEINS = [
    ("Tofu", "Tofu natur", 200, ["vegetarisch", "vegan", "soja", "glutenfrei"]),
    ("Kichererbsen", "Kichererbsen (gegart)", 200, ["vegetarisch", "vegan", "glutenfrei"]),
    ("Tempeh", "Tempeh", 160, ["vegetarisch", "soja"]),
    ("Linsen", "Linsen grün (roh)", 100, ["vegetarisch", "vegan", "glutenfrei"]),
]

_CARBS = [
    ("Quinoa", "Quinoa (roh)", 80, ["glutenfrei"]),
    ("Basmati-Reis", "Basmati-Reis (roh)", 80, []),
    ("Vollkorn-Reis", "Vollkorn-Reis (roh)", 80, []),
    ("Süßkartoffel", "Süßkartoffel", 200, ["glutenfrei"]),
    ("Buchweizen", "Buchweizen (roh)", 80, ["glutenfrei"]),
    ("Couscous", "Couscous (roh)", 80, ["gluten"]),
    ("Bulgur", "Bulgur (roh)", 80, ["gluten"]),
    ("Kartoffeln", "Kartoffeln", 250, ["glutenfrei"]),
]

# (dative display, food_item_name, amount_g)
_VEGGIES = [
    ("Brokkoli", "Brokkoli", 150),
    ("Spinat", "Spinat frisch", 100),
    ("Zucchini", "Zucchini", 150),
    ("Paprika", "Paprika rot", 120),
    ("Grünen Bohnen", "Grüne Bohnen", 150),
    ("Pilzen", "Pilze (Champignons)", 150),
    ("Spargel", "Spargel", 150),
    ("Rosenkohl", "Rosenkohl", 150),
]


def _bowl(
    pname: str,
    pitem: str,
    pg: int,
    ptags: list[str],
    cname: str,
    citem: str,
    cg: int,
    ctags: list[str],
    vname: str,
    vitem: str,
    vg: int,
    category: str,
) -> dict:
    tags = sorted(set(ptags + ctags + ["meal-prep"]))
    return {
        "name": f"{pname} mit {cname} und {vname}",
        "category": category,
        "description": (
            f"Gebratenes {pname} mit {cname} und {vname} — "
            "proteinreich und ausgewogen."
        ),
        "tags": tags,
        "ingredients": [
            {"food_item": pitem, "base_amount_g": pg},
            {"food_item": citem, "base_amount_g": cg},
            {"food_item": vitem, "base_amount_g": vg},
            {"food_item": "Olivenöl", "base_amount_g": 10},
            {"food_item": "Gewürze (gemischt)", "base_amount_g": 5},
        ],
    }


def _generate_bowls() -> list[dict]:
    """Generate template bowls: 8×5×4 animal (160) + 4×4×4 plant (64) = 224 total."""
    dishes: list[dict] = []

    # Animal: 8 proteins × 5 carbs × 4 veggies = 160, alternating lunch/dinner
    for i, (p, c, v) in enumerate(
        product(_ANIMAL_PROTEINS, _CARBS[:5], _VEGGIES[:4])
    ):
        category = "lunch" if i % 2 == 0 else "dinner"
        pname, pitem, pg, ptags = p
        cname, citem, cg, ctags = c
        vname, vitem, vg = v
        dishes.append(
            _bowl(pname, pitem, pg, ptags, cname, citem, cg, ctags, vname, vitem, vg, category)
        )

    # Plant: 4 proteins × 4 carbs × 4 veggies = 64, alternating lunch/dinner
    for i, (p, c, v) in enumerate(
        product(_PLANT_PROTEINS, _CARBS[:4], _VEGGIES[:4])
    ):
        category = "lunch" if i % 2 == 0 else "dinner"
        pname, pitem, pg, ptags = p
        cname, citem, cg, ctags = c
        vname, vitem, vg = v
        dishes.append(
            _bowl(pname, pitem, pg, ptags, cname, citem, cg, ctags, vname, vitem, vg, category)
        )

    return dishes


# ── Curated breakfast dishes ──────────────────────────────────────────────────

def _breakfast_dishes() -> list[dict]:
    d = []

    # Overnight Oats variations
    oat_toppings = [
        ("mit Erdbeeren und Chiasamen", [("Erdbeeren", 100), ("Chiasamen", 10), ("Honig", 8)], ["vegetarisch", "laktose", "gluten"]),
        ("mit Mango und Kokosmilch", [("Mango", 100), ("Kokosmilch light", 50), ("Honig", 8)], ["vegetarisch", "gluten"]),
        ("mit Himbeeren und Walnüssen", [("Himbeeren", 80), ("Walnüsse", 15), ("Honig", 8)], ["vegetarisch", "laktose", "gluten"]),
        ("mit Äpfeln und Zimt", [("Äpfel", 100), ("Honig", 10)], ["vegetarisch", "laktose", "gluten"]),
        ("mit Banane und Mandeln", [("Banane", 80), ("Mandeln", 15)], ["vegetarisch", "laktose", "gluten"]),
        ("mit Schoko-Protein", [("Proteinpulver Schoko", 25), ("Heidelbeeren", 60)], ["laktose", "gluten", "high-protein"]),
        ("mit Kirschen", [("Kirschen", 100), ("Honig", 8)], ["vegetarisch", "laktose", "gluten"]),
        ("mit Kiwi und Granatapfel", [("Kiwi", 80), ("Granatapfelkerne", 30)], ["vegetarisch", "laktose", "gluten"]),
        ("mit Heidelbeeren und Chiasamen", [("Heidelbeeren", 80), ("Chiasamen", 10), ("Honig", 8)], ["vegetarisch", "laktose", "gluten"]),
        ("mit Erdnussbutter und Banane", [("Erdnussbutter", 20), ("Banane", 80)], ["vegetarisch", "laktose", "gluten", "erdnüsse"]),
    ]
    for suffix, extras, tags in oat_toppings:
        ingredients = (
            [{"food_item": "Haferflocken", "base_amount_g": 80},
             {"food_item": "Skyr natur", "base_amount_g": 120},
             {"food_item": "Milch 1,5%", "base_amount_g": 80}]
            + [{"food_item": item, "base_amount_g": amt} for item, amt in extras]
        )
        d.append({
            "name": f"Overnight Oats {suffix}",
            "category": "breakfast",
            "description": f"Haferflocken über Nacht in Skyr eingeweicht, {suffix[4:]}.",
            "tags": tags + ["schnelle Zubereitung"],
            "ingredients": ingredients,
        })

    # Porridge / warm oats
    porridge_variants = [
        ("mit Heidelbeeren", [("Heidelbeeren", 80), ("Honig", 10)], ["laktose", "gluten"]),
        ("mit Erdbeeren und Skyr", [("Erdbeeren", 100), ("Skyr natur", 80)], ["laktose", "gluten"]),
        ("mit Mango", [("Mango", 80), ("Kokosmilch light", 50)], ["gluten"]),
        ("mit Chiasamen und Kiwi", [("Chiasamen", 10), ("Kiwi", 80)], ["laktose", "gluten"]),
        ("mit Walnüssen und Honig", [("Walnüsse", 15), ("Honig", 12)], ["laktose", "gluten", "schalenfrüchte"]),
        ("mit Mandeln und Zimt", [("Mandeln", 20), ("Honig", 8)], ["laktose", "gluten", "schalenfrüchte"]),
        ("Protein-Porridge Vanille", [("Proteinpulver Vanille", 25), ("Blaubeeren", 60)], ["laktose", "gluten", "high-protein"]),
        ("Protein-Porridge Schoko", [("Proteinpulver Schoko", 25), ("Banane", 70)], ["laktose", "gluten", "high-protein"]),
    ]
    for suffix, extras, tags in porridge_variants:
        ingredients = (
            [{"food_item": "Haferflocken", "base_amount_g": 80},
             {"food_item": "Milch 1,5%", "base_amount_g": 200}]
            + [{"food_item": item, "base_amount_g": amt} for item, amt in extras]
        )
        d.append({
            "name": f"Haferbrei {suffix}",
            "category": "breakfast",
            "description": f"Warmer Haferbrei {suffix[4:] if suffix.startswith('mit') else suffix}.",
            "tags": tags + ["vegetarisch"],
            "ingredients": ingredients,
        })

    # Egg-based dishes
    egg_dishes = [
        ("Spinat-Feta-Omelett", "Herzhaftes Omelett mit frischem Spinat und Fetakäse.",
         [("Eier", 200), ("Spinat frisch", 80), ("Fetakäse light", 40), ("Olivenöl", 8)],
         ["vegetarisch", "ei", "low-carb", "laktose", "glutenfrei"]),
        ("Pilz-Omelett", "Omelett mit Champignons und Frühlingszwiebeln.",
         [("Eier", 200), ("Pilze (Champignons)", 120), ("Zwiebeln", 30), ("Olivenöl", 8), ("Gewürze (gemischt)", 3)],
         ["vegetarisch", "ei", "low-carb", "glutenfrei"]),
        ("Brokkoli-Cheddar-Omelett", "Omelett mit gedämpftem Brokkoli.",
         [("Eier", 200), ("Brokkoli", 100), ("Mozzarella light", 30), ("Olivenöl", 8)],
         ["vegetarisch", "ei", "low-carb", "laktose", "glutenfrei"]),
        ("Scrambled Eggs mit Lachs", "Cremige Rühreier mit geräuchertem Lachs.",
         [("Eier", 200), ("Lachs geräuchert", 60), ("Spinat frisch", 50), ("Olivenöl", 8)],
         ["ei", "fisch", "low-carb", "glutenfrei", "high-protein"]),
        ("Omelett mit Tomaten und Feta", "Klassisches Omelett mediterran.",
         [("Eier", 200), ("Tomaten (frisch)", 80), ("Fetakäse light", 40), ("Olivenöl", 8)],
         ["vegetarisch", "ei", "low-carb", "laktose", "glutenfrei", "mediterran"]),
        ("Eier-Avocado-Bowl", "Rührei auf Avocado mit Tomaten.",
         [("Eier", 160), ("Avocado", 80), ("Tomaten (frisch)", 60), ("Zitronensaft", 10)],
         ["vegetarisch", "ei", "low-carb", "glutenfrei"]),
        ("Omelett mit Zucchini und Mozzarella", "Leichtes Omelett mit Zucchini.",
         [("Eier", 200), ("Zucchini", 100), ("Mozzarella light", 30), ("Olivenöl", 8)],
         ["vegetarisch", "ei", "low-carb", "laktose", "glutenfrei"]),
        ("Eiklar-Omelett mit Paprika", "Leichtes Eiweiß-Omelett mit Paprika.",
         [("Eiklar", 250), ("Paprika rot", 80), ("Spinat frisch", 50), ("Olivenöl", 8)],
         ["vegetarisch", "ei", "low-carb", "glutenfrei", "high-protein"]),
        ("Rührei mit Pilzen und Spinat", "Rührei mit sautierten Pilzen.",
         [("Eier", 200), ("Pilze (Champignons)", 100), ("Spinat frisch", 60), ("Olivenöl", 8)],
         ["vegetarisch", "ei", "low-carb", "glutenfrei"]),
        ("Frittata mit Gemüse", "Gebackene Ei-Frittata mit Brokkoli und Paprika.",
         [("Eier", 200), ("Brokkoli", 100), ("Paprika rot", 60), ("Zwiebeln", 40), ("Olivenöl", 10)],
         ["vegetarisch", "ei", "low-carb", "glutenfrei"]),
    ]
    for name, desc, ingredients, tags in egg_dishes:
        d.append({
            "name": name,
            "category": "breakfast",
            "description": desc,
            "tags": tags,
            "ingredients": [{"food_item": fi, "base_amount_g": amt} for fi, amt in ingredients],
        })

    # Protein shakes
    shake_variants = [
        ("Protein-Shake Schoko", "Schoko-Proteinshake mit Milch.",
         [("Proteinpulver Schoko", 30), ("Milch 1,5%", 300), ("Banane", 60)],
         ["laktose", "soja", "high-protein", "schnelle Zubereitung"]),
        ("Protein-Shake Erdbeere", "Erdbeer-Proteinshake.",
         [("Proteinpulver Erdbeere", 30), ("Milch 1,5%", 300), ("Erdbeeren", 80)],
         ["laktose", "soja", "high-protein", "schnelle Zubereitung"]),
        ("Protein-Shake Banane-Vanille", "Cremiger Bananen-Shake.",
         [("Proteinpulver Vanille", 30), ("Milch 1,5%", 250), ("Banane", 100)],
         ["laktose", "soja", "high-protein", "schnelle Zubereitung"]),
        ("Protein-Shake Mandelmilch", "Leichter Shake mit Mandelmilch.",
         [("Proteinpulver Vanille", 30), ("Mandelmilch ungesüßt", 350), ("Heidelbeeren", 60)],
         ["soja", "schalenfrüchte", "high-protein", "schnelle Zubereitung"]),
        ("Grüner Power-Shake", "Grüner Smoothie mit Protein.",
         [("Proteinpulver Vanille", 25), ("Spinat frisch", 60), ("Banane", 80), ("Mandelmilch ungesüßt", 250)],
         ["soja", "schalenfrüchte", "high-protein", "schnelle Zubereitung"]),
        ("Himbeer-Schoko-Shake", "Schoko-Shake mit Himbeeren.",
         [("Proteinpulver Schoko", 30), ("Milch 1,5%", 300), ("Himbeeren", 80)],
         ["laktose", "soja", "high-protein", "schnelle Zubereitung"]),
        ("Mango-Protein-Shake", "Tropischer Proteinshake.",
         [("Proteinpulver Vanille", 30), ("Mandelmilch ungesüßt", 250), ("Mango", 100)],
         ["soja", "schalenfrüchte", "high-protein", "schnelle Zubereitung"]),
        ("Ananas-Ingwer-Shake", "Erfrischender Shake mit Ananas.",
         [("Proteinpulver Vanille", 25), ("Mandelmilch ungesüßt", 250), ("Ananas", 100), ("Ingwer frisch", 5)],
         ["soja", "schalenfrüchte", "high-protein", "schnelle Zubereitung"]),
    ]
    for name, desc, ingredients, tags in shake_variants:
        d.append({
            "name": name,
            "category": "breakfast",
            "description": desc,
            "tags": tags,
            "ingredients": [{"food_item": fi, "base_amount_g": amt} for fi, amt in ingredients],
        })

    # Smoothie Bowls
    smoothie_bowls = [
        ("Smoothie Bowl Mango-Banane", "Dicke Smoothie Bowl mit Mango-Banane.",
         [("Mango", 120), ("Banane", 80), ("Skyr natur", 100), ("Chiasamen", 10), ("Kokosmilch light", 50)],
         ["vegetarisch", "laktose"]),
        ("Smoothie Bowl Erdbeere", "Rosa Erdbeersmoothie als Bowl.",
         [("Erdbeeren", 150), ("Banane", 60), ("Skyr natur", 100), ("Heidelbeeren", 40)],
         ["vegetarisch", "laktose"]),
        ("Smoothie Bowl Heidelbeere-Açaí", "Violette Smoothie Bowl.",
         [("Heidelbeeren", 150), ("Banane", 80), ("Griechischer Joghurt (0%)", 100), ("Chiasamen", 10)],
         ["vegetarisch", "laktose"]),
        ("Smoothie Bowl Tropical", "Tropische Bowl mit Mango und Ananas.",
         [("Mango", 100), ("Ananas", 80), ("Kokosmilch light", 80), ("Kokosraspeln", 10), ("Chiasamen", 8)],
         ["vegetarisch", "vegan"]),
        ("Smoothie Bowl Green Power", "Grüne Power-Bowl mit Spinat.",
         [("Spinat frisch", 50), ("Banane", 80), ("Mango", 80), ("Mandelmilch ungesüßt", 100), ("Chiasamen", 10)],
         ["vegetarisch", "vegan", "schalenfrüchte"]),
        ("Smoothie Bowl Himbeer-Protein", "Protein-Bowl mit Himbeeren.",
         [("Himbeeren", 120), ("Banane", 60), ("Proteinpulver Vanille", 20), ("Skyr natur", 80)],
         ["laktose", "soja", "high-protein"]),
    ]
    for name, desc, ingredients, tags in smoothie_bowls:
        d.append({
            "name": name,
            "category": "breakfast",
            "description": desc,
            "tags": tags,
            "ingredients": [{"food_item": fi, "base_amount_g": amt} for fi, amt in ingredients],
        })

    # Protein pancakes
    pancake_variants = [
        ("Bananen-Protein-Pancakes", "Proteinreiche Pancakes mit Banane.",
         [("Banane", 120), ("Eier", 120), ("Haferflocken", 60), ("Proteinpulver Vanille", 20), ("Backpulver", 3)],
         ["ei", "laktose", "gluten", "soja", "high-protein"]),
        ("Hafer-Pancakes mit Heidelbeeren", "Fluffige Hafer-Pancakes.",
         [("Haferflocken", 80), ("Eier", 100), ("Magerquark", 100), ("Heidelbeeren", 60), ("Backpulver", 3)],
         ["vegetarisch", "ei", "laktose", "gluten", "high-protein"]),
        ("Buchweizen-Pancakes", "Glutenfreie Buchweizen-Pancakes.",
         [("Buchweizen (roh)", 80), ("Eier", 100), ("Milch 1,5%", 100), ("Backpulver", 3), ("Erdbeeren", 80)],
         ["vegetarisch", "ei", "laktose", "glutenfrei"]),
        ("Protein-Waffeln", "Proteinreiche Waffeln aus Quark und Ei.",
         [("Magerquark", 150), ("Eier", 100), ("Haferflocken", 50), ("Backpulver", 3), ("Honig", 10)],
         ["vegetarisch", "ei", "laktose", "gluten", "high-protein"]),
        ("Schoko-Protein-Pancakes", "Schokoladengeschmack ohne Schuldgefühle.",
         [("Proteinpulver Schoko", 25), ("Banane", 100), ("Eier", 100), ("Backpulver", 3)],
         ["ei", "laktose", "soja", "glutenfrei", "high-protein"]),
    ]
    for name, desc, ingredients, tags in pancake_variants:
        d.append({
            "name": name,
            "category": "breakfast",
            "description": desc,
            "tags": tags,
            "ingredients": [{"food_item": fi, "base_amount_g": amt} for fi, amt in ingredients],
        })

    # Yogurt / Quark bowls (sweet)
    yogurt_bowls = [
        ("Skyr-Bowl mit Mango und Chiasamen",
         [("Skyr natur", 200), ("Mango", 100), ("Chiasamen", 12), ("Honig", 8)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Skyr-Bowl mit Heidelbeeren und Walnüssen",
         [("Skyr natur", 200), ("Heidelbeeren", 80), ("Walnüsse", 15), ("Honig", 8)],
         ["vegetarisch", "laktose", "schalenfrüchte", "schnelle Zubereitung"]),
        ("Griechischer Joghurt Bowl mit Honig und Nüssen",
         [("Griechischer Joghurt (0%)", 200), ("Honig", 15), ("Mandeln", 20), ("Heidelbeeren", 60)],
         ["vegetarisch", "laktose", "schalenfrüchte", "schnelle Zubereitung"]),
        ("Griechischer Joghurt Bowl mit Früchten",
         [("Griechischer Joghurt (0%)", 200), ("Erdbeeren", 80), ("Kiwi", 60), ("Granatapfelkerne", 30)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Magerquark-Bowl süß mit Erdbeeren",
         [("Magerquark", 200), ("Erdbeeren", 100), ("Honig", 10), ("Chiasamen", 10)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Skyr mit Kiwi und Granatapfel",
         [("Skyr natur", 200), ("Kiwi", 80), ("Granatapfelkerne", 40), ("Honig", 8)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Protein-Joghurt Bowl mit Beeren",
         [("Griechischer Joghurt (0%)", 150), ("Proteinpulver Vanille", 20), ("Himbeeren", 80), ("Walnüsse", 15)],
         ["laktose", "soja", "schalenfrüchte", "high-protein", "schnelle Zubereitung"]),
        ("Cottage Cheese mit Mango und Chiasamen",
         [("Cottage Cheese", 200), ("Mango", 100), ("Chiasamen", 10), ("Honig", 8)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
    ]
    for name, ingredients, tags in yogurt_bowls:
        d.append({
            "name": name,
            "category": "breakfast",
            "description": f"Cremige Bowl mit Joghurt oder Quark und frischen Früchten.",
            "tags": tags,
            "ingredients": [{"food_item": fi, "base_amount_g": amt} for fi, amt in ingredients],
        })

    # Misc / toast / chia
    misc_breakfast = [
        ("Avocado-Toast mit Ei",
         "Vollkornbrot mit Avocado und Spiegelei.",
         [("Vollkornbrot", 80), ("Avocado", 100), ("Eier", 120), ("Zitronensaft", 8)],
         ["ei", "gluten", "weizen", "schnelle Zubereitung"]),
        ("Vollkornbrot mit Lachs und Skyr",
         "Vollkornbrot mit geräuchertem Lachs.",
         [("Vollkornbrot", 80), ("Lachs geräuchert", 80), ("Skyr natur", 50), ("Gurke", 60)],
         ["fisch", "gluten", "laktose", "schnelle Zubereitung"]),
        ("Chia-Pudding Vanille",
         "Chia-Pudding über Nacht mit Vanille.",
         [("Chiasamen", 40), ("Mandelmilch ungesüßt", 300), ("Honig", 10), ("Erdbeeren", 80)],
         ["vegetarisch", "vegan", "schalenfrüchte", "glutenfrei"]),
        ("Chia-Pudding Mango-Kokosmilch",
         "Tropischer Chia-Pudding.",
         [("Chiasamen", 40), ("Kokosmilch light", 200), ("Mandelmilch ungesüßt", 100), ("Mango", 80)],
         ["vegetarisch", "vegan", "schalenfrüchte", "glutenfrei"]),
        ("Chia-Pudding Schoko",
         "Schoko-Chia-Pudding mit Proteinpulver.",
         [("Chiasamen", 40), ("Milch 1,5%", 280), ("Proteinpulver Schoko", 20), ("Banane", 60)],
         ["laktose", "soja", "high-protein"]),
        ("Vollkornbrot mit Erdnussbutter und Banane",
         "Klassische Kombination für Energie.",
         [("Vollkornbrot", 80), ("Erdnussbutter", 30), ("Banane", 100)],
         ["vegetarisch", "vegan", "gluten", "erdnüsse", "schnelle Zubereitung"]),
        ("Reiswaffeln mit Erdnussbutter",
         "Leichte Reiswaffeln mit Erdnussbutter und Banane.",
         [("Reiswaffeln", 60), ("Erdnussbutter", 30), ("Banane", 80), ("Honig", 8)],
         ["vegetarisch", "erdnüsse", "schnelle Zubereitung", "glutenfrei"]),
        ("Protein-Granola Bowl",
         "Müsli mit Joghurt und frischen Früchten.",
         [("Haferflocken", 60), ("Griechischer Joghurt (0%)", 150), ("Himbeeren", 60), ("Mandeln", 15), ("Honig", 8)],
         ["vegetarisch", "laktose", "gluten", "schalenfrüchte"]),
        ("Bircher Müsli",
         "Overnight-Müsli nach Schweizer Art.",
         [("Haferflocken", 80), ("Milch 1,5%", 150), ("Äpfel", 80), ("Walnüsse", 15), ("Honig", 10)],
         ["vegetarisch", "laktose", "gluten", "schalenfrüchte"]),
        ("Quinoa-Frühstücksbrei",
         "Warmer Quinoa-Brei mit Früchten.",
         [("Quinoa (roh)", 70), ("Mandelmilch ungesüßt", 200), ("Mango", 80), ("Honig", 10), ("Chiasamen", 8)],
         ["vegetarisch", "vegan", "schalenfrüchte", "glutenfrei"]),
        ("Avocado-Toast mit Lachs",
         "Vollkornbrot mit Avocado und geräuchertem Lachs.",
         [("Vollkornbrot", 80), ("Avocado", 80), ("Lachs geräuchert", 70), ("Zitronensaft", 8)],
         ["fisch", "gluten", "schnelle Zubereitung"]),
        ("Vollkornbrot mit Magerquark und Heidelbeeren",
         "Leichtes süßes Vollkornbrot-Frühstück.",
         [("Vollkornbrot", 80), ("Magerquark", 100), ("Heidelbeeren", 80), ("Honig", 8)],
         ["vegetarisch", "laktose", "gluten", "schnelle Zubereitung"]),
        ("Ei-Tomaten-Toast",
         "Rührei auf Vollkorntoast.",
         [("Eier", 160), ("Tomaten (frisch)", 80), ("Vollkornbrot", 80), ("Olivenöl", 6)],
         ["vegetarisch", "ei", "gluten", "schnelle Zubereitung"]),
        ("Warmer Buchweizen-Brei",
         "Glutenfreier Frühstücksbrei aus Buchweizen.",
         [("Buchweizen (roh)", 70), ("Mandelmilch ungesüßt", 200), ("Banane", 80), ("Honig", 10)],
         ["vegetarisch", "vegan", "schalenfrüchte", "glutenfrei"]),
        ("Protein-Bowl mit Lachs",
         "Herzhaftes Frühstück mit geräuchertem Lachs.",
         [("Lachs geräuchert", 80), ("Eier", 120), ("Spinat frisch", 60), ("Avocado", 60)],
         ["fisch", "ei", "glutenfrei", "high-protein"]),
        ("Skyr-Pancakes",
         "Luftige Pancakes mit Skyr.",
         [("Skyr natur", 150), ("Eier", 100), ("Haferflocken", 50), ("Backpulver", 3), ("Erdbeeren", 80)],
         ["vegetarisch", "ei", "laktose", "gluten", "high-protein"]),
        ("Eier-Wrap süß",
         "Süßes Omelett gerollt mit Obst.",
         [("Eier", 160), ("Banane", 60), ("Erdnussbutter", 20), ("Honig", 8)],
         ["vegetarisch", "ei", "erdnüsse", "glutenfrei", "schnelle Zubereitung"]),
        ("Mandelmilch-Haferbrei mit Beeren",
         "Veganer Porridge.",
         [("Haferflocken", 80), ("Mandelmilch ungesüßt", 250), ("Himbeeren", 60), ("Heidelbeeren", 40), ("Chiasamen", 8)],
         ["vegetarisch", "vegan", "gluten", "schalenfrüchte"]),
        ("Joghurt-Granola-Bowl",
         "Joghurt mit knusprigem Granola.",
         [("Griechischer Joghurt (0%)", 150), ("Haferflocken", 40), ("Honig", 10), ("Mandeln", 15), ("Erdbeeren", 80)],
         ["vegetarisch", "laktose", "gluten", "schalenfrüchte"]),
        ("Bananen-Ei-Pancakes",
         "Nur 2 Zutaten — klassisches Fitness-Frühstück.",
         [("Banane", 150), ("Eier", 120), ("Backpulver", 2), ("Heidelbeeren", 60)],
         ["vegetarisch", "ei", "glutenfrei", "high-protein", "schnelle Zubereitung"]),
        ("Mango-Chia-Bowl",
         "Chia-Pudding mit frischer Mango.",
         [("Chiasamen", 40), ("Kokosmilch light", 250), ("Mango", 120), ("Kokosraspeln", 8)],
         ["vegetarisch", "vegan", "glutenfrei"]),
        ("High-Protein-Müsli",
         "Ballaststoffreiches Müsli mit Protein.",
         [("Haferflocken", 60), ("Proteinpulver Vanille", 20), ("Griechischer Joghurt (0%)", 100), ("Blaubeeren", 60), ("Walnüsse", 15)],
         ["laktose", "soja", "gluten", "schalenfrüchte", "high-protein"]),
        ("Chia-Pudding Heidelbeere-Mandelmilch",
         "Chia-Pudding mit Mandelmilch und Heidelbeeren.",
         [("Chiasamen", 40), ("Mandelmilch ungesüßt", 300), ("Heidelbeeren", 80), ("Honig", 10)],
         ["vegetarisch", "vegan", "schalenfrüchte", "glutenfrei"]),
        ("Omelett mit Lachs und Spinat",
         "Proteinreiches Lachs-Omelett.",
         [("Eiklar", 200), ("Lachsfilet", 80), ("Spinat frisch", 60), ("Olivenöl", 8)],
         ["ei", "fisch", "glutenfrei", "low-carb", "high-protein"]),
        ("Overnight Oats Ananas-Kokos",
         "Tropische Overnight Oats.",
         [("Haferflocken", 80), ("Kokosmilch light", 150), ("Skyr natur", 80), ("Ananas", 80), ("Kokosraspeln", 10)],
         ["vegetarisch", "laktose", "gluten", "schnelle Zubereitung"]),
        ("Skyr-Pancakes mit Mango",
         "Leichte Pancakes mit Mango-Topping.",
         [("Skyr natur", 150), ("Eier", 100), ("Haferflocken", 50), ("Backpulver", 3), ("Mango", 80)],
         ["vegetarisch", "ei", "laktose", "gluten", "high-protein"]),
        ("Protein-Omelett mit Kichererbsen",
         "Herzhaftes Omelett mit Kichererbsen.",
         [("Eiklar", 200), ("Kichererbsen (gegart)", 100), ("Paprika rot", 60), ("Olivenöl", 8)],
         ["vegetarisch", "ei", "glutenfrei", "high-protein"]),
        ("Overnight Oats mit Protein-Schoko",
         "Schokoladiger Start in den Tag.",
         [("Haferflocken", 80), ("Proteinpulver Schoko", 25), ("Milch 1,5%", 150), ("Banane", 60)],
         ["laktose", "soja", "gluten", "high-protein", "schnelle Zubereitung"]),
        ("Griechischer Joghurt Parfait",
         "Schichtdessert als Frühstück.",
         [("Griechischer Joghurt (0%)", 150), ("Haferflocken", 40), ("Erdbeeren", 80), ("Heidelbeeren", 40), ("Honig", 8)],
         ["vegetarisch", "laktose", "gluten"]),
    ]
    for name, desc, ingredients, tags in misc_breakfast:
        d.append({
            "name": name,
            "category": "breakfast",
            "description": desc,
            "tags": tags,
            "ingredients": [{"food_item": fi, "base_amount_g": amt} for fi, amt in ingredients],
        })

    return d


# ── Curated lunch dishes (non-bowl) ──────────────────────────────────────────

def _lunch_extra_dishes() -> list[dict]:
    d = []
    items = [
        # Salads
        ("Quinoa-Salat mit Kichererbsen und Feta",
         "lunch", "Frischer Quinoa-Salat mit Kichererbsen.",
         [("Quinoa (roh)", 80), ("Kichererbsen (gegart)", 100), ("Fetakäse light", 50), ("Gurke", 80), ("Tomaten (frisch)", 80), ("Olivenöl", 12), ("Zitronensaft", 10)],
         ["vegetarisch", "laktose", "glutenfrei", "high-protein", "mediterran"]),
        ("Bulgur-Salat mit Feta und Tomaten",
         "lunch", "Levantinischer Salat mit Bulgur.",
         [("Bulgur (roh)", 80), ("Fetakäse light", 50), ("Tomaten (frisch)", 100), ("Gurke", 80), ("Olivenöl", 12)],
         ["vegetarisch", "laktose", "gluten", "mediterran"]),
        ("Feldsalat mit Hähnchen und Walnüssen",
         "lunch", "Feldsalat-Bowl mit Hähnchenbrust.",
         [("Hähnchenbrust", 150), ("Feldsalat", 80), ("Walnüsse", 20), ("Rote Beete (gegart)", 80), ("Olivenöl", 12), ("Apfelessig", 10)],
         ["high-protein", "schalenfrüchte", "glutenfrei"]),
        ("Rucola-Salat mit Lachs und Avocado",
         "lunch", "Eleganter Lachs-Salat mit Rucola.",
         [("Lachsfilet", 150), ("Rucola", 80), ("Avocado", 80), ("Tomaten (frisch)", 60), ("Zitronensaft", 10), ("Olivenöl", 10)],
         ["high-protein", "fisch", "glutenfrei"]),
        ("Kichererbsen-Salat mediterran",
         "lunch", "Bunter Kichererbsen-Salat.",
         [("Kichererbsen (gegart)", 200), ("Gurke", 80), ("Tomaten (frisch)", 80), ("Fetakäse light", 50), ("Oliven", 20), ("Olivenöl", 12)],
         ["vegetarisch", "laktose", "glutenfrei", "mediterran"]),
        ("Linsen-Salat mit Feta",
         "lunch", "Herzlicher Linsen-Salat.",
         [("Linsen grün (roh)", 100), ("Fetakäse light", 50), ("Paprika rot", 80), ("Zwiebeln", 30), ("Olivenöl", 12), ("Apfelessig", 10)],
         ["vegetarisch", "laktose", "glutenfrei", "high-protein"]),
        ("Spinat-Salat mit Ei und Walnüssen",
         "lunch", "Nährstoffreicher Spinat-Salat.",
         [("Spinat frisch", 100), ("Eier", 120), ("Walnüsse", 20), ("Tomaten (frisch)", 60), ("Olivenöl", 10), ("Apfelessig", 8)],
         ["vegetarisch", "ei", "schalenfrüchte", "low-carb", "glutenfrei"]),
        ("Edamame-Bowl asiatisch",
         "lunch", "Asiatische Bowl mit Edamame.",
         [("Edamame", 150), ("Basmati-Reis (roh)", 80), ("Gurke", 60), ("Sojasoße", 15), ("Sesamöl", 8), ("Ingwer frisch", 5)],
         ["vegetarisch", "vegan", "soja", "glutenfrei"]),
        # Wraps and sandwiches
        ("Lachs-Wrap mit Avocado",
         "lunch", "Vollkorn-Wrap mit Lachs und Avocado.",
         [("Vollkorn-Wraps", 80), ("Lachsfilet", 130), ("Avocado", 70), ("Spinat frisch", 40), ("Zitronensaft", 8)],
         ["fisch", "gluten", "high-protein"]),
        ("Turkey-Wrap mit Rucola",
         "lunch", "Leichter Wrap mit Putenbrust.",
         [("Vollkorn-Wraps", 80), ("Putenbrust", 150), ("Rucola", 40), ("Gurke", 60), ("Magerquark", 40)],
         ["gluten", "laktose", "high-protein"]),
        ("Veggie-Wrap mit Hummus und Gemüse",
         "lunch", "Bunter Veggie-Wrap.",
         [("Vollkorn-Wraps", 80), ("Kichererbsen (gegart)", 100), ("Tahini", 20), ("Paprika rot", 60), ("Spinat frisch", 40), ("Gurke", 50)],
         ["vegetarisch", "vegan", "gluten", "sesam"]),
        ("Vollkornbrot mit Hähnchen und Avocado",
         "lunch", "Belegtes Vollkornbrot high-protein.",
         [("Vollkornbrot", 80), ("Hähnchenbrust", 130), ("Avocado", 70), ("Tomaten (frisch)", 50), ("Eisbergsalat", 30)],
         ["gluten", "high-protein"]),
        ("Vollkornbrot mit Thunfisch",
         "lunch", "Schnelles Thunfisch-Sandwich.",
         [("Vollkornbrot", 80), ("Thunfisch im eigenen Saft", 120), ("Gurke", 60), ("Magerquark", 40)],
         ["fisch", "gluten", "laktose", "high-protein", "schnelle Zubereitung"]),
        # Soups
        ("Linseneintopf herzhaft",
         "lunch", "Klassischer Linseneintopf.",
         [("Rote Linsen (roh)", 100), ("Möhren", 100), ("Sellerie", 60), ("Tomatenmark", 30), ("Zwiebeln", 50), ("Olivenöl", 8), ("Gewürze (gemischt)", 5)],
         ["vegetarisch", "vegan", "glutenfrei", "high-protein", "meal-prep"]),
        ("Brokkoli-Cremesuppe",
         "lunch", "Cremige Brokkoli-Suppe mit wenig Fett.",
         [("Brokkoli", 300), ("Kartoffeln", 100), ("Zwiebeln", 50), ("Magerquark", 80), ("Gewürze (gemischt)", 5)],
         ["vegetarisch", "laktose", "glutenfrei"]),
        ("Hühnersuppe mit Gemüse",
         "lunch", "Klassische Hühnerbrühe.",
         [("Hähnchenbrust", 180), ("Möhren", 100), ("Sellerie", 60), ("Lauch", 80), ("Gewürze (gemischt)", 5)],
         ["high-protein", "glutenfrei"]),
        ("Kichererbsen-Tomaten-Suppe",
         "lunch", "Herzhafte Suppe mit Kichererbsen.",
         [("Kichererbsen (gegart)", 200), ("Tomaten (frisch)", 200), ("Tomatenmark", 30), ("Zwiebeln", 50), ("Olivenöl", 8), ("Gewürze (gemischt)", 5)],
         ["vegetarisch", "vegan", "glutenfrei", "high-protein"]),
        ("Thai-Kokos-Suppe mit Hähnchen",
         "lunch", "Leichte Kokossuppe Thai-Style.",
         [("Hähnchenbrust", 180), ("Kokosmilch light", 200), ("Pak Choi", 100), ("Ingwer frisch", 10), ("Sojasoße", 15), ("Zitronensaft", 10)],
         ["fisch", "soja", "glutenfrei", "high-protein"]),
        # Asian dishes
        ("Tofu-Stir-fry mit Pak Choi",
         "lunch", "Knuspriger Tofu mit Pak Choi aus dem Wok.",
         [("Tofu natur", 200), ("Pak Choi", 150), ("Paprika rot", 80), ("Sojasoße", 20), ("Sesamöl", 8), ("Ingwer frisch", 8)],
         ["vegetarisch", "vegan", "soja", "glutenfrei"]),
        ("Reisnudeln mit Garnelen asiatisch",
         "lunch", "Schnelle Reisnudeln mit Garnelen.",
         [("Reisnudeln", 80), ("Garnelen", 150), ("Pak Choi", 100), ("Sojasoße", 20), ("Sesamöl", 8)],
         ["fisch", "soja", "glutenfrei", "high-protein"]),
        ("Hähnchen-Wok mit Pak Choi",
         "lunch", "Klassischer Hähnchen-Wok.",
         [("Hähnchenbrust", 180), ("Pak Choi", 150), ("Paprika rot", 80), ("Sojasoße", 20), ("Sesamöl", 8), ("Ingwer frisch", 8)],
         ["high-protein", "soja", "glutenfrei"]),
        ("Tempeh-Stir-fry mit Gemüse",
         "lunch", "Proteinreicher Tempeh Wok.",
         [("Tempeh", 180), ("Brokkoli", 120), ("Paprika rot", 80), ("Sojasoße", 20), ("Sesamöl", 8)],
         ["vegetarisch", "soja", "glutenfrei"]),
        # Mexican / misc
        ("Burrito-Bowl mit Hähnchen",
         "lunch", "Tex-Mex Bowl mit Hähnchen und schwarzen Bohnen.",
         [("Hähnchenbrust", 150), ("Schwarze Bohnen (gegart)", 100), ("Basmati-Reis (roh)", 70), ("Paprika rot", 80), ("Magerquark", 50)],
         ["high-protein", "glutenfrei"]),
        ("Burrito-Bowl vegetarisch",
         "lunch", "Vegane Tex-Mex Bowl.",
         [("Schwarze Bohnen (gegart)", 150), ("Kidneybohnen (gegart)", 100), ("Basmati-Reis (roh)", 80), ("Paprika rot", 80), ("Avocado", 60)],
         ["vegetarisch", "vegan", "glutenfrei"]),
        ("Gefüllte Paprika mit Quinoa",
         "lunch", "Mit Quinoa und Gemüse gefüllte Paprikaschote.",
         [("Paprika rot", 200), ("Quinoa (roh)", 80), ("Tomatenmark", 40), ("Zwiebeln", 40), ("Pilze (Champignons)", 80)],
         ["vegetarisch", "vegan", "glutenfrei"]),
    ]
    for item in items:
        name, category, desc, ingredients, tags = item
        d.append({
            "name": name,
            "category": category,
            "description": desc,
            "tags": tags,
            "ingredients": [{"food_item": fi, "base_amount_g": amt} for fi, amt in ingredients],
        })
    return d


# ── Curated dinner dishes (non-bowl) ─────────────────────────────────────────

def _dinner_extra_dishes() -> list[dict]:
    d = []
    items = [
        # Pasta
        ("Vollkorn-Spaghetti Bolognese",
         "Herzhaftes Bolognese mit Putenhack.",
         [("Vollkorn-Spaghetti (roh)", 90), ("Putenhackfleisch", 200), ("Tomatenmark", 60), ("Zwiebeln", 60), ("Möhren", 60), ("Olivenöl", 10)],
         ["gluten", "weizen", "high-protein", "meal-prep"]),
        ("Vollkorn-Pasta mit Hähnchen und Brokkoli",
         "Cremige Pasta mit Hähnchen.",
         [("Vollkorn-Pasta (roh)", 90), ("Hähnchenbrust", 160), ("Brokkoli", 120), ("Magerquark", 60), ("Gewürze (gemischt)", 5)],
         ["gluten", "laktose", "high-protein"]),
        ("Vollkorn-Pasta mit Lachs",
         "Lachs-Pasta mit Spinat.",
         [("Vollkorn-Pasta (roh)", 90), ("Lachsfilet", 150), ("Spinat frisch", 80), ("Magerquark", 60), ("Zitronensaft", 10)],
         ["gluten", "fisch", "laktose", "high-protein"]),
        ("Rinderhack-Pasta",
         "Pasta mit magerem Rinderhackfleisch.",
         [("Vollkorn-Spaghetti (roh)", 90), ("Rinderhackfleisch mager", 180), ("Tomatenmark", 60), ("Zwiebeln", 60), ("Olivenöl", 10)],
         ["gluten", "weizen", "high-protein"]),
        ("Pasta Primavera high-protein",
         "Bunte Gemüse-Pasta.",
         [("Vollkorn-Pasta (roh)", 90), ("Zucchini", 100), ("Paprika rot", 80), ("Pilze (Champignons)", 100), ("Mozzarella light", 50), ("Olivenöl", 10)],
         ["vegetarisch", "gluten", "laktose"]),
        # Wok / stir-fry
        ("Hähnchen-Gemüse-Wok",
         "Klassischer Hähnchenwok mit viel Gemüse.",
         [("Hähnchenbrust", 200), ("Brokkoli", 120), ("Pak Choi", 100), ("Paprika rot", 80), ("Sojasoße", 20), ("Sesamöl", 8)],
         ["high-protein", "soja", "glutenfrei"]),
        ("Garnelen-Wok mit Gemüse",
         "Schneller Garnelenwok.",
         [("Garnelen", 200), ("Pak Choi", 120), ("Pilze (Champignons)", 100), ("Sojasoße", 20), ("Sesamöl", 8), ("Ingwer frisch", 8)],
         ["fisch", "soja", "glutenfrei", "high-protein", "schnelle Zubereitung"]),
        ("Rindfleisch-Stir-fry",
         "Mageres Rindfleisch asiatisch.",
         [("Rindfleisch mager", 180), ("Brokkoli", 150), ("Pak Choi", 100), ("Sojasoße", 20), ("Sesamöl", 8)],
         ["soja", "glutenfrei", "high-protein"]),
        # Casseroles / bakes
        ("Hähnchen-Gemüse-Auflauf",
         "Einfacher Auflauf aus dem Ofen.",
         [("Hähnchenbrust", 200), ("Zucchini", 120), ("Paprika rot", 100), ("Tomatenmark", 60), ("Mozzarella light", 50), ("Olivenöl", 10)],
         ["laktose", "glutenfrei", "high-protein", "meal-prep"]),
        ("Lachs-Gemüse-Auflauf",
         "Leichter Fischouflauf.",
         [("Lachsfilet", 180), ("Kartoffeln", 200), ("Brokkoli", 150), ("Magerquark", 80), ("Zitronensaft", 10)],
         ["fisch", "laktose", "glutenfrei", "high-protein"]),
        ("Hackfleisch-Zucchini-Auflauf",
         "Low-Carb-Auflauf.",
         [("Putenhackfleisch", 200), ("Zucchini", 200), ("Tomatenmark", 60), ("Mozzarella light", 60), ("Olivenöl", 10)],
         ["laktose", "glutenfrei", "high-protein"]),
        # Curry
        ("Hähnchen-Curry light",
         "Leichtes Curry mit Kokosmilch.",
         [("Hähnchenbrust", 200), ("Kokosmilch light", 150), ("Spinat frisch", 80), ("Zwiebeln", 50), ("Tomatenmark", 40), ("Gewürze (gemischt)", 8)],
         ["high-protein", "glutenfrei"]),
        ("Kichererbsen-Curry vegan",
         "Vollwertiges veganes Curry.",
         [("Kichererbsen (gegart)", 200), ("Kokosmilch light", 150), ("Spinat frisch", 80), ("Tomatenmark", 60), ("Zwiebeln", 50), ("Gewürze (gemischt)", 8)],
         ["vegetarisch", "vegan", "glutenfrei"]),
        ("Lachs-Curry",
         "Asiatisches Lachs-Curry.",
         [("Lachsfilet", 180), ("Kokosmilch light", 150), ("Pak Choi", 100), ("Ingwer frisch", 10), ("Sojasoße", 15)],
         ["fisch", "soja", "glutenfrei", "high-protein"]),
        # Veggie mains
        ("Proteinpizza Vollkorn",
         "Pizza auf Vollkornboden mit Quark.",
         [("Vollkornbrot", 80), ("Magerquark", 100), ("Tomatenmark", 80), ("Mozzarella light", 60), ("Paprika rot", 80)],
         ["vegetarisch", "laktose", "gluten", "high-protein"]),
        ("Shakshuka herzhaft",
         "Eier in Tomatensauce.",
         [("Eier", 200), ("Tomatenmark", 100), ("Paprika rot", 100), ("Zwiebeln", 60), ("Olivenöl", 10), ("Gewürze (gemischt)", 5)],
         ["vegetarisch", "ei", "glutenfrei"]),
        ("Gefüllte Aubergine mit Hackfleisch",
         "Aubergine mit Hackfleischfüllung.",
         [("Aubergine", 300), ("Putenhackfleisch", 180), ("Tomatenmark", 60), ("Zwiebeln", 50), ("Olivenöl", 10)],
         ["glutenfrei", "high-protein"]),
        ("Ratatouille mit Hähnchen",
         "Provenzalisches Gemüsegericht.",
         [("Hähnchenbrust", 180), ("Aubergine", 150), ("Zucchini", 120), ("Tomaten (frisch)", 150), ("Olivenöl", 12), ("Gewürze (gemischt)", 5)],
         ["glutenfrei", "high-protein", "mediterran"]),
        ("Polenta mit Pilzragout",
         "Cremige Polenta mit Pilzragout.",
         [("Polenta (roh)", 100), ("Pilze (Champignons)", 200), ("Zwiebeln", 60), ("Magerquark", 60), ("Olivenöl", 10)],
         ["vegetarisch", "laktose", "glutenfrei"]),
        ("Kabeljau mit Kartoffeln und Spargel",
         "Klassisches Fischgericht.",
         [("Kabeljau", 200), ("Kartoffeln", 250), ("Spargel", 150), ("Olivenöl", 10), ("Zitronensaft", 10)],
         ["fisch", "glutenfrei", "high-protein"]),
        ("Rindfleisch mit Kartoffeln und Rosenkohl",
         "Klassisches Abendessen.",
         [("Rindfleisch mager", 180), ("Kartoffeln", 200), ("Rosenkohl", 150), ("Olivenöl", 10), ("Gewürze (gemischt)", 5)],
         ["glutenfrei", "high-protein"]),
    ]
    for item in items:
        name, desc, ingredients, tags = item
        d.append({
            "name": name,
            "category": "dinner",
            "description": desc,
            "tags": tags,
            "ingredients": [{"food_item": fi, "base_amount_g": amt} for fi, amt in ingredients],
        })
    return d


# ── Snack dishes ──────────────────────────────────────────────────────────────

def _snack_dishes() -> list[dict]:
    d = []
    items = [
        # Quark variations
        ("Magerquark mit Heidelbeeren und Honig",
         [("Magerquark", 200), ("Heidelbeeren", 80), ("Honig", 10)],
         ["vegetarisch", "laktose", "low-carb", "schnelle Zubereitung"]),
        ("Magerquark mit Himbeeren",
         [("Magerquark", 200), ("Himbeeren", 80), ("Honig", 8)],
         ["vegetarisch", "laktose", "low-carb", "schnelle Zubereitung"]),
        ("Magerquark mit Banane und Erdnussbutter",
         [("Magerquark", 200), ("Banane", 80), ("Erdnussbutter", 15)],
         ["vegetarisch", "laktose", "erdnüsse", "schnelle Zubereitung"]),
        ("Magerquark mit Mango und Chiasamen",
         [("Magerquark", 200), ("Mango", 80), ("Chiasamen", 10)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Magerquark mit Kirschen",
         [("Magerquark", 200), ("Kirschen", 80), ("Honig", 8)],
         ["vegetarisch", "laktose", "low-carb", "schnelle Zubereitung"]),
        ("Magerquark mit Äpfeln und Zimt",
         [("Magerquark", 200), ("Äpfel", 100), ("Honig", 8)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Magerquark mit Walnüssen und Honig",
         [("Magerquark", 200), ("Walnüsse", 20), ("Honig", 10)],
         ["vegetarisch", "laktose", "schalenfrüchte", "schnelle Zubereitung"]),
        # Skyr variations
        ("Skyr mit Erdbeeren und Mandeln",
         [("Skyr natur", 200), ("Erdbeeren", 100), ("Mandeln", 15)],
         ["vegetarisch", "laktose", "schalenfrüchte", "schnelle Zubereitung"]),
        ("Skyr mit Ananas und Kokosraspeln",
         [("Skyr natur", 200), ("Ananas", 80), ("Kokosraspeln", 10)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Skyr mit Banane und Chiasamen",
         [("Skyr natur", 200), ("Banane", 80), ("Chiasamen", 10), ("Honig", 8)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Skyr mit Granatapfel und Walnüssen",
         [("Skyr natur", 200), ("Granatapfelkerne", 50), ("Walnüsse", 15)],
         ["vegetarisch", "laktose", "schalenfrüchte", "schnelle Zubereitung"]),
        # Greek yogurt snacks
        ("Griechischer Joghurt mit Honig und Kirschen",
         [("Griechischer Joghurt (0%)", 200), ("Kirschen", 80), ("Honig", 10)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Griechischer Joghurt mit Mandeln und Mango",
         [("Griechischer Joghurt (0%)", 200), ("Mango", 80), ("Mandeln", 15)],
         ["vegetarisch", "laktose", "schalenfrüchte", "schnelle Zubereitung"]),
        ("Griechischer Joghurt mit Heidelbeeren",
         [("Griechischer Joghurt (0%)", 200), ("Heidelbeeren", 80), ("Chiasamen", 8)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        # Cottage Cheese snacks
        ("Cottage Cheese mit Ananas",
         [("Cottage Cheese", 200), ("Ananas", 100), ("Chiasamen", 8)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Cottage Cheese mit Himbeeren und Walnüssen",
         [("Cottage Cheese", 200), ("Himbeeren", 80), ("Walnüsse", 15)],
         ["vegetarisch", "laktose", "schalenfrüchte", "schnelle Zubereitung"]),
        ("Cottage Cheese mit Gurke und Tomaten",
         [("Cottage Cheese", 200), ("Gurke", 80), ("Tomaten (frisch)", 80), ("Gewürze (gemischt)", 3)],
         ["vegetarisch", "laktose", "low-carb", "schnelle Zubereitung"]),
        # Reiswaffeln / bread snacks
        ("Reiswaffeln mit Avocado und Tomate",
         [("Reiswaffeln", 40), ("Avocado", 80), ("Tomaten (frisch)", 60), ("Zitronensaft", 5)],
         ["vegetarisch", "vegan", "glutenfrei", "schnelle Zubereitung"]),
        ("Reiswaffeln mit Magerquark und Erdbeeren",
         [("Reiswaffeln", 40), ("Magerquark", 100), ("Erdbeeren", 80)],
         ["vegetarisch", "laktose", "glutenfrei", "schnelle Zubereitung"]),
        ("Reiswaffeln mit Lachs und Quark",
         [("Reiswaffeln", 40), ("Lachs geräuchert", 60), ("Magerquark", 60), ("Gurke", 40)],
         ["fisch", "laktose", "glutenfrei", "high-protein", "schnelle Zubereitung"]),
        ("Vollkornbrot mit Hähnchen und Avocado",
         [("Vollkornbrot", 60), ("Hähnchenbrust", 100), ("Avocado", 60)],
         ["gluten", "high-protein", "schnelle Zubereitung"]),
        ("Vollkornbrot mit Thunfisch und Gurke",
         [("Vollkornbrot", 60), ("Thunfisch im eigenen Saft", 100), ("Gurke", 60)],
         ["fisch", "gluten", "high-protein", "schnelle Zubereitung"]),
        # Smoothies
        ("Bananen-Mandelmilch-Smoothie",
         [("Banane", 120), ("Mandelmilch ungesüßt", 300), ("Erdnussbutter", 15)],
         ["vegetarisch", "vegan", "schalenfrüchte", "erdnüsse", "schnelle Zubereitung"]),
        ("Erdbeer-Bananen-Smoothie",
         [("Erdbeeren", 120), ("Banane", 80), ("Mandelmilch ungesüßt", 250)],
         ["vegetarisch", "vegan", "schalenfrüchte", "schnelle Zubereitung"]),
        ("Mango-Ananas-Smoothie",
         [("Mango", 100), ("Ananas", 80), ("Mandelmilch ungesüßt", 200), ("Ingwer frisch", 5)],
         ["vegetarisch", "vegan", "schalenfrüchte", "schnelle Zubereitung"]),
        ("Grüner Smoothie mit Spinat",
         [("Spinat frisch", 60), ("Banane", 80), ("Äpfel", 80), ("Mandelmilch ungesüßt", 200)],
         ["vegetarisch", "vegan", "schalenfrüchte", "schnelle Zubereitung"]),
        # Nuts/seeds
        ("Nuss-Mix mit Kürbiskernen",
         [("Walnüsse", 25), ("Mandeln", 20), ("Kürbiskerne", 15)],
         ["vegetarisch", "vegan", "schalenfrüchte", "low-carb", "schnelle Zubereitung"]),
        ("Mandeln mit Heidelbeeren",
         [("Mandeln", 30), ("Heidelbeeren", 80)],
         ["vegetarisch", "vegan", "schalenfrüchte", "schnelle Zubereitung"]),
        ("Erdnussbutter-Bananen-Snack",
         [("Erdnussbutter", 30), ("Banane", 100), ("Reiswaffeln", 30)],
         ["vegetarisch", "vegan", "erdnüsse", "schnelle Zubereitung"]),
        # Misc protein snacks
        ("Edamame pur",
         [("Edamame", 200), ("Gewürze (gemischt)", 2)],
         ["vegetarisch", "vegan", "soja", "glutenfrei", "schnelle Zubereitung"]),
        ("Kichererbsen geröstet",
         [("Kichererbsen (gegart)", 200), ("Olivenöl", 8), ("Gewürze (gemischt)", 5)],
         ["vegetarisch", "vegan", "glutenfrei", "schnelle Zubereitung"]),
        ("Hähnchen-Salat-Wrap Mini",
         [("Hähnchenbrust", 100), ("Eisbergsalat", 50), ("Tomaten (frisch)", 60), ("Magerquark", 30)],
         ["high-protein", "laktose", "glutenfrei", "schnelle Zubereitung"]),
        ("Proteinriegel selbstgemacht",
         [("Haferflocken", 50), ("Erdnussbutter", 30), ("Proteinpulver Vanille", 20), ("Honig", 15)],
         ["gluten", "erdnüsse", "laktose", "soja", "high-protein"]),
        ("Avocado mit Reiswaffeln",
         [("Avocado", 100), ("Reiswaffeln", 40), ("Zitronensaft", 8), ("Gewürze (gemischt)", 2)],
         ["vegetarisch", "vegan", "glutenfrei", "schnelle Zubereitung"]),
        # More quark / yogurt combos
        ("Magerquark mit Ananas",
         [("Magerquark", 200), ("Ananas", 100), ("Honig", 8)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Magerquark mit Granatapfel und Chiasamen",
         [("Magerquark", 200), ("Granatapfelkerne", 50), ("Chiasamen", 10)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Magerquark mit Kiwi und Honig",
         [("Magerquark", 200), ("Kiwi", 80), ("Honig", 8)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Skyr mit Himbeeren und Kürbiskernen",
         [("Skyr natur", 200), ("Himbeeren", 80), ("Kürbiskerne", 15)],
         ["vegetarisch", "laktose", "schalenfrüchte", "schnelle Zubereitung"]),
        ("Skyr mit Kirschen",
         [("Skyr natur", 200), ("Kirschen", 100), ("Honig", 8)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Griechischer Joghurt mit Walnüssen und Honig",
         [("Griechischer Joghurt (0%)", 200), ("Walnüsse", 20), ("Honig", 12)],
         ["vegetarisch", "laktose", "schalenfrüchte", "schnelle Zubereitung"]),
        ("Griechischer Joghurt mit Kiwi und Chia",
         [("Griechischer Joghurt (0%)", 200), ("Kiwi", 80), ("Chiasamen", 10)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Cottage Cheese mit Heidelbeeren",
         [("Cottage Cheese", 200), ("Heidelbeeren", 80), ("Honig", 8)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Cottage Cheese mit Kirschen und Mandeln",
         [("Cottage Cheese", 200), ("Kirschen", 80), ("Mandeln", 15)],
         ["vegetarisch", "laktose", "schalenfrüchte", "schnelle Zubereitung"]),
        # Rice cake combos
        ("Reiswaffeln mit Lachs und Avocado",
         [("Reiswaffeln", 40), ("Lachs geräuchert", 60), ("Avocado", 50)],
         ["fisch", "glutenfrei", "high-protein", "schnelle Zubereitung"]),
        ("Reiswaffeln mit Thunfisch und Gurke",
         [("Reiswaffeln", 40), ("Thunfisch im eigenen Saft", 80), ("Gurke", 60)],
         ["fisch", "glutenfrei", "high-protein", "schnelle Zubereitung"]),
        ("Reiswaffeln mit Hähnchen und Tomaten",
         [("Reiswaffeln", 40), ("Hähnchenbrust", 80), ("Tomaten (frisch)", 60)],
         ["glutenfrei", "high-protein", "schnelle Zubereitung"]),
        # Protein smoothie snacks
        ("Protein-Smoothie Erdbeere-Banane",
         [("Proteinpulver Erdbeere", 25), ("Erdbeeren", 80), ("Banane", 60), ("Milch 1,5%", 200)],
         ["laktose", "soja", "high-protein", "schnelle Zubereitung"]),
        ("Protein-Smoothie Mango-Vanille",
         [("Proteinpulver Vanille", 25), ("Mango", 100), ("Mandelmilch ungesüßt", 200)],
         ["soja", "schalenfrüchte", "high-protein", "schnelle Zubereitung"]),
        ("Protein-Smoothie Schoko-Banane",
         [("Proteinpulver Schoko", 25), ("Banane", 80), ("Milch 1,5%", 250)],
         ["laktose", "soja", "high-protein", "schnelle Zubereitung"]),
        # Veggie snacks
        ("Brokkoli-Rohkost mit Hummus",
         [("Brokkoli", 150), ("Kichererbsen (gegart)", 80), ("Tahini", 15), ("Zitronensaft", 8)],
         ["vegetarisch", "vegan", "sesam", "glutenfrei"]),
        ("Möhren-Rohkost mit Magerquark-Dip",
         [("Möhren", 150), ("Magerquark", 80), ("Gewürze (gemischt)", 3)],
         ["vegetarisch", "laktose", "glutenfrei", "low-carb"]),
        ("Paprika-Rohkost mit Guacamole",
         [("Paprika rot", 150), ("Avocado", 80), ("Zitronensaft", 8)],
         ["vegetarisch", "vegan", "glutenfrei", "low-carb"]),
        # Additional protein snacks
        ("Thunfisch pur mit Zitrone",
         [("Thunfisch im eigenen Saft", 150), ("Zitronensaft", 10), ("Gewürze (gemischt)", 3)],
         ["fisch", "glutenfrei", "low-carb", "high-protein", "schnelle Zubereitung"]),
        ("Hähnchen-Streifen pur",
         [("Hähnchenbrust", 150), ("Gewürze (gemischt)", 5), ("Olivenöl", 5)],
         ["glutenfrei", "low-carb", "high-protein", "schnelle Zubereitung"]),
        ("Hartes Ei mit Vollkornbrot",
         [("Eier", 120), ("Vollkornbrot", 60), ("Gewürze (gemischt)", 2)],
         ["vegetarisch", "ei", "gluten", "schnelle Zubereitung"]),
        ("Eier mit Avocado",
         [("Eier", 120), ("Avocado", 80), ("Tomaten (frisch)", 60)],
         ["vegetarisch", "ei", "glutenfrei", "low-carb", "schnelle Zubereitung"]),
        # More snacks to reach ~90 total
        ("Skyr mit Äpfeln und Walnüssen",
         [("Skyr natur", 200), ("Äpfel", 80), ("Walnüsse", 15), ("Honig", 8)],
         ["vegetarisch", "laktose", "schalenfrüchte", "schnelle Zubereitung"]),
        ("Skyr mit Ananas und Mandeln",
         [("Skyr natur", 200), ("Ananas", 80), ("Mandeln", 15)],
         ["vegetarisch", "laktose", "schalenfrüchte", "schnelle Zubereitung"]),
        ("Magerquark mit Kirschen und Vanille",
         [("Magerquark", 200), ("Kirschen", 100), ("Honig", 8), ("Protein-Flavour Drops", 5)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Magerquark mit Brombeeren",
         [("Magerquark", 200), ("Himbeeren", 60), ("Blaubeeren", 60), ("Honig", 8)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Griechischer Joghurt mit Ananas",
         [("Griechischer Joghurt (0%)", 200), ("Ananas", 100), ("Kokosraspeln", 10)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Griechischer Joghurt mit Granatapfel",
         [("Griechischer Joghurt (0%)", 200), ("Granatapfelkerne", 50), ("Honig", 10)],
         ["vegetarisch", "laktose", "schnelle Zubereitung"]),
        ("Griechischer Joghurt mit Kirschen und Schokoprotein",
         [("Griechischer Joghurt (0%)", 200), ("Kirschen", 80), ("Proteinpulver Schoko", 15)],
         ["laktose", "soja", "high-protein", "schnelle Zubereitung"]),
        ("Cottage Cheese mit Erdnussbutter und Banane",
         [("Cottage Cheese", 200), ("Erdnussbutter", 20), ("Banane", 60)],
         ["vegetarisch", "laktose", "erdnüsse", "schnelle Zubereitung"]),
        ("Cottage Cheese herzhaft mit Gurke",
         [("Cottage Cheese", 200), ("Gurke", 80), ("Tomaten (frisch)", 60), ("Gewürze (gemischt)", 3)],
         ["vegetarisch", "laktose", "low-carb", "schnelle Zubereitung"]),
        ("Cashewkerne und Trockenfrüchte Mix",
         [("Walnüsse", 20), ("Mandeln", 15), ("Heidelbeeren", 60)],
         ["vegetarisch", "vegan", "schalenfrüchte", "low-carb", "schnelle Zubereitung"]),
        ("Reiswaffeln mit Skyr und Kiwi",
         [("Reiswaffeln", 40), ("Skyr natur", 100), ("Kiwi", 80)],
         ["vegetarisch", "laktose", "glutenfrei", "schnelle Zubereitung"]),
        ("Reiswaffeln mit Magerquark und Banane",
         [("Reiswaffeln", 40), ("Magerquark", 100), ("Banane", 80)],
         ["vegetarisch", "laktose", "glutenfrei", "schnelle Zubereitung"]),
        ("Vollkornbrot mit Lachs",
         [("Vollkornbrot", 60), ("Lachs geräuchert", 70), ("Gurke", 50)],
         ["fisch", "gluten", "high-protein", "schnelle Zubereitung"]),
        ("Vollkornbrot mit Ei und Tomaten",
         [("Vollkornbrot", 60), ("Eier", 100), ("Tomaten (frisch)", 60)],
         ["vegetarisch", "ei", "gluten", "schnelle Zubereitung"]),
        ("Smoothie Ananas-Spinat",
         [("Ananas", 100), ("Spinat frisch", 50), ("Mandelmilch ungesüßt", 250), ("Ingwer frisch", 5)],
         ["vegetarisch", "vegan", "schalenfrüchte", "schnelle Zubereitung"]),
        ("Smoothie Heidelbeere-Mandelmilch",
         [("Heidelbeeren", 100), ("Mandelmilch ungesüßt", 250), ("Banane", 60), ("Chiasamen", 8)],
         ["vegetarisch", "vegan", "schalenfrüchte", "schnelle Zubereitung"]),
        ("Smoothie Kiwi-Limette",
         [("Kiwi", 100), ("Banane", 60), ("Mandelmilch ungesüßt", 250), ("Zitronensaft", 10)],
         ["vegetarisch", "vegan", "schalenfrüchte", "schnelle Zubereitung"]),
        ("Protein-Riegel Oats-Nuss",
         [("Haferflocken", 60), ("Walnüsse", 20), ("Honig", 15), ("Proteinpulver Vanille", 20)],
         ["laktose", "soja", "gluten", "schalenfrüchte", "high-protein"]),
        ("Edamame mit Meersalz",
         [("Edamame", 200), ("Gewürze (gemischt)", 3)],
         ["vegetarisch", "vegan", "soja", "glutenfrei", "schnelle Zubereitung"]),
        ("Kichererbsen-Chips selbstgemacht",
         [("Kichererbsen (gegart)", 200), ("Olivenöl", 8), ("Gewürze (gemischt)", 5)],
         ["vegetarisch", "vegan", "glutenfrei", "high-protein"]),
        ("Schwarze Bohnen Snack Bowl",
         [("Schwarze Bohnen (gegart)", 150), ("Tomaten (frisch)", 80), ("Avocado", 60)],
         ["vegetarisch", "vegan", "glutenfrei", "high-protein", "schnelle Zubereitung"]),
        ("Lachs-Gurken-Häppchen",
         [("Lachs geräuchert", 80), ("Gurke", 120), ("Magerquark", 50)],
         ["fisch", "laktose", "glutenfrei", "low-carb", "high-protein", "schnelle Zubereitung"]),
        ("Putenbrust-Salat-Röllchen",
         [("Putenbrust", 120), ("Eisbergsalat", 60), ("Tomaten (frisch)", 60), ("Magerquark", 40)],
         ["laktose", "glutenfrei", "high-protein", "low-carb", "schnelle Zubereitung"]),
        ("Mini-Omelett Snack",
         [("Eiklar", 180), ("Spinat frisch", 50), ("Pilze (Champignons)", 60)],
         ["vegetarisch", "ei", "glutenfrei", "low-carb", "high-protein", "schnelle Zubereitung"]),
        ("Thunfisch-Avocado-Snack",
         [("Thunfisch im eigenen Saft", 120), ("Avocado", 70), ("Zitronensaft", 8)],
         ["fisch", "glutenfrei", "low-carb", "high-protein", "schnelle Zubereitung"]),
        ("Rote-Beete-Joghurt-Bowl",
         [("Griechischer Joghurt (0%)", 150), ("Rote Beete (gegart)", 80), ("Walnüsse", 15)],
         ["vegetarisch", "laktose", "schalenfrüchte", "glutenfrei"]),
        ("Hafer-Schoko-Energy-Ball",
         [("Haferflocken", 60), ("Proteinpulver Schoko", 20), ("Erdnussbutter", 25), ("Honig", 15)],
         ["gluten", "erdnüsse", "laktose", "soja", "high-protein"]),
        ("Mandeln mit Dunkler Schokolade Snack",
         [("Mandeln", 25), ("Heidelbeeren", 80), ("Skyr natur", 100)],
         ["vegetarisch", "laktose", "schalenfrüchte", "schnelle Zubereitung"]),
        ("Spargel mit Ei Snack",
         [("Spargel", 150), ("Eier", 100), ("Olivenöl", 8)],
         ["vegetarisch", "ei", "glutenfrei", "low-carb"]),
        ("Blumenkohl-Snack mit Joghurt-Dip",
         [("Blumenkohl", 200), ("Griechischer Joghurt (0%)", 80), ("Gewürze (gemischt)", 3)],
         ["vegetarisch", "laktose", "glutenfrei", "low-carb"]),
        ("Linsen-Snack Bowl",
         [("Rote Linsen (roh)", 80), ("Tomaten (frisch)", 80), ("Olivenöl", 8), ("Gewürze (gemischt)", 3)],
         ["vegetarisch", "vegan", "glutenfrei", "high-protein"]),
    ]
    for item in items:
        name, ingredients, tags = item
        d.append({
            "name": name,
            "category": "snack",
            "description": "Proteinreicher Snack für zwischendurch.",
            "tags": tags,
            "ingredients": [{"food_item": fi, "base_amount_g": amt} for fi, amt in ingredients],
        })
    return d


# ── Supplement dishes ─────────────────────────────────────────────────────────

def _supplement_dishes() -> list[dict]:
    d = []
    items = [
        # Post-workout shakes
        ("Post-Workout Shake Schoko",
         "Regenerationsshake nach dem Training.",
         [("Proteinpulver Schoko", 40), ("Milch 1,5%", 350), ("Banane", 80)],
         ["supplement", "laktose", "soja", "high-protein", "schnelle Zubereitung"]),
        ("Post-Workout Shake Vanille-Erdbeere",
         "Erdbeer-Shake zur Muskelregeneration.",
         [("Proteinpulver Vanille", 40), ("Milch 1,5%", 300), ("Erdbeeren", 100)],
         ["supplement", "laktose", "soja", "high-protein", "schnelle Zubereitung"]),
        ("Post-Workout Shake Banane-Protein",
         "Kohlenhydrat-Protein-Shake.",
         [("Proteinpulver Vanille", 35), ("Banane", 120), ("Milch 1,5%", 300)],
         ["supplement", "laktose", "soja", "high-protein", "schnelle Zubereitung"]),
        ("Post-Workout Protein-Rice Bowl",
         "Reis mit Proteinpulver-Milch nach Training.",
         [("Basmati-Reis (roh)", 80), ("Proteinpulver Vanille", 25), ("Milch 1,5%", 200), ("Banane", 60)],
         ["supplement", "laktose", "soja", "high-protein"]),
        ("Recovery Shake mit Haferflocken",
         "Komplexe KH + Protein nach langen Einheiten.",
         [("Haferflocken", 50), ("Proteinpulver Schoko", 30), ("Milch 1,5%", 300), ("Banane", 80)],
         ["supplement", "laktose", "soja", "gluten", "high-protein", "schnelle Zubereitung"]),
        # Pre-workout meals
        ("Pre-Workout Bananen-Shake",
         "Leichter Shake vor dem Training.",
         [("Banane", 120), ("Milch 1,5%", 250), ("Honig", 15)],
         ["supplement", "laktose", "high-carb", "schnelle Zubereitung"]),
        ("Pre-Workout Hafer-Shake",
         "Hafer-Shake für anhaltende Energie.",
         [("Haferflocken", 60), ("Banane", 80), ("Milch 1,5%", 300), ("Honig", 10)],
         ["supplement", "laktose", "gluten", "high-carb", "schnelle Zubereitung"]),
        ("Pre-Workout Bowl mit Reis und Hähnchen",
         "Vollwertige Mahlzeit 2h vor Training.",
         [("Basmati-Reis (roh)", 100), ("Hähnchenbrust", 150), ("Brokkoli", 100), ("Olivenöl", 8)],
         ["supplement", "high-protein", "meal-prep"]),
        ("Pre-Workout Quinoa-Bowl",
         "Quinoa mit Hähnchen für Energie.",
         [("Quinoa (roh)", 80), ("Hähnchenbrust", 150), ("Spinat frisch", 80), ("Olivenöl", 8)],
         ["supplement", "glutenfrei", "high-protein"]),
        ("Pre-Workout Süßkartoffel-Bowl",
         "Süßkartoffel-Bowl vor intensivem Training.",
         [("Süßkartoffel", 250), ("Hähnchenbrust", 140), ("Spinat frisch", 60), ("Olivenöl", 8)],
         ["supplement", "glutenfrei", "high-protein"]),
        # Night / slow protein
        ("Casein-Shake Nacht",
         "Langsam verdaulicher Protein-Shake für die Nacht.",
         [("Casein-Protein", 35), ("Milch 1,5%", 250)],
         ["supplement", "laktose", "high-protein", "schnelle Zubereitung"]),
        ("Casein-Shake Schoko Nacht",
         "Schoko-Casein-Shake zur Nacht.",
         [("Casein-Protein", 35), ("Milch 1,5%", 250), ("Proteinpulver Schoko", 10)],
         ["supplement", "laktose", "soja", "high-protein", "schnelle Zubereitung"]),
        ("Nacht-Magerquark Bowl",
         "Magerquark mit langsamen Proteinen vor dem Schlafen.",
         [("Magerquark", 250), ("Casein-Protein", 20), ("Heidelbeeren", 60)],
         ["supplement", "laktose", "high-protein", "schnelle Zubereitung"]),
        ("Nacht-Skyr mit Chiasamen",
         "Skyr mit Chiasamen als Nacht-Protein.",
         [("Skyr natur", 250), ("Chiasamen", 12), ("Walnüsse", 15)],
         ["supplement", "laktose", "schalenfrüchte", "high-protein", "schnelle Zubereitung"]),
        # Protein-Shake water-based
        ("Protein-Shake Wasser-Schoko",
         "Shake mit Wasser für wenig Kalorien.",
         [("Proteinpulver Schoko", 35), ("Wasser", 400)],
         ["supplement", "soja", "high-protein", "schnelle Zubereitung"]),
        ("Protein-Shake Wasser-Vanille",
         "Leichter Vanille-Shake.",
         [("Proteinpulver Vanille", 35), ("Wasser", 400)],
         ["supplement", "soja", "high-protein", "schnelle Zubereitung"]),
        ("Protein-Shake Wasser-Erdbeere",
         "Erfrischender Erdbeer-Shake.",
         [("Proteinpulver Erdbeere", 35), ("Wasser", 400)],
         ["supplement", "soja", "high-protein", "schnelle Zubereitung"]),
        # Recovery meals
        ("Recovery-Bowl mit Lachs",
         "Lachs-Bowl zur Regeneration.",
         [("Lachsfilet", 180), ("Quinoa (roh)", 80), ("Spinat frisch", 80), ("Avocado", 60)],
         ["supplement", "fisch", "glutenfrei", "high-protein"]),
        ("Recovery-Shake mit Beeren",
         "Antioxidativer Recovery-Shake.",
         [("Proteinpulver Vanille", 30), ("Heidelbeeren", 80), ("Himbeeren", 60), ("Milch 1,5%", 300)],
         ["supplement", "laktose", "soja", "high-protein", "schnelle Zubereitung"]),
        ("Recovery Hähnchen-Kartoffel-Bowl",
         "Kohlenhydratreiche Bowl nach Ausdauertraining.",
         [("Hähnchenbrust", 200), ("Kartoffeln", 300), ("Brokkoli", 120), ("Olivenöl", 10)],
         ["supplement", "glutenfrei", "high-protein"]),
        # More pre-workout options
        ("Pre-Workout Reis-Hähnchen-Bowl",
         "Klassische Pre-Workout-Mahlzeit.",
         [("Basmati-Reis (roh)", 100), ("Hähnchenbrust", 140), ("Spinat frisch", 60), ("Olivenöl", 8)],
         ["supplement", "high-protein"]),
        ("Pre-Workout Vollkorn-Toast mit Ei",
         "Leichte Pre-Workout-Mahlzeit.",
         [("Vollkornbrot", 80), ("Eier", 120), ("Avocado", 60)],
         ["supplement", "ei", "gluten", "schnelle Zubereitung"]),
        ("Pre-Workout Hafer-Bananen-Bowl",
         "Energie-Kick vor dem Training.",
         [("Haferflocken", 80), ("Banane", 100), ("Mandelmilch ungesüßt", 200), ("Honig", 15)],
         ["supplement", "gluten", "schalenfrüchte", "high-carb", "schnelle Zubereitung"]),
        # More night protein
        ("Nacht-Casein-Quark-Bowl",
         "Langsames Protein für die Nacht.",
         [("Magerquark", 200), ("Casein-Protein", 25), ("Heidelbeeren", 60)],
         ["supplement", "laktose", "high-protein", "schnelle Zubereitung"]),
        ("Nacht-Griechischer Joghurt",
         "Griechischer Joghurt als Nacht-Snack.",
         [("Griechischer Joghurt (0%)", 250), ("Casein-Protein", 20), ("Walnüsse", 15)],
         ["supplement", "laktose", "schalenfrüchte", "high-protein", "schnelle Zubereitung"]),
        # More post-workout
        ("Post-Workout Shake Mango",
         "Tropischer Post-Workout-Shake.",
         [("Proteinpulver Vanille", 35), ("Mango", 100), ("Mandelmilch ungesüßt", 300)],
         ["supplement", "soja", "schalenfrüchte", "high-protein", "schnelle Zubereitung"]),
        ("Post-Workout Shake Ananas-Ingwer",
         "Entzündungshemmender Recovery-Shake.",
         [("Proteinpulver Vanille", 35), ("Ananas", 100), ("Ingwer frisch", 8), ("Mandelmilch ungesüßt", 280)],
         ["supplement", "soja", "schalenfrüchte", "high-protein", "schnelle Zubereitung"]),
        ("Post-Workout Lachs-Quinoa-Bowl",
         "Komplette Recovery-Mahlzeit.",
         [("Lachsfilet", 180), ("Quinoa (roh)", 80), ("Brokkoli", 150), ("Olivenöl", 10)],
         ["supplement", "fisch", "glutenfrei", "high-protein"]),
        ("Post-Workout Hähnchen-Süßkartoffel",
         "Optimale Protein-KH-Kombination.",
         [("Hähnchenbrust", 200), ("Süßkartoffel", 250), ("Spinat frisch", 60)],
         ["supplement", "glutenfrei", "high-protein"]),
        ("Pre-Workout Bananen-Erdnussbutter-Shake",
         "Schnelle Energie vor dem Training.",
         [("Banane", 120), ("Erdnussbutter", 20), ("Milch 1,5%", 250), ("Honig", 10)],
         ["supplement", "laktose", "erdnüsse", "high-carb", "schnelle Zubereitung"]),
        ("Pre-Workout Skyr mit Beeren",
         "Leichte Pre-Workout-Mahlzeit.",
         [("Skyr natur", 200), ("Blaubeeren", 80), ("Haferflocken", 40), ("Honig", 8)],
         ["supplement", "laktose", "gluten", "high-protein"]),
        ("Recovery Lachsbowl mit Quinoa",
         "Omega-3-reiche Recovery-Mahlzeit.",
         [("Lachsfilet", 200), ("Quinoa (roh)", 80), ("Spargel", 150), ("Olivenöl", 10)],
         ["supplement", "fisch", "glutenfrei", "high-protein"]),
        ("Recovery Putenbrust-Süßkartoffel",
         "Aufbauende Mahlzeit nach hartem Training.",
         [("Putenbrust", 200), ("Süßkartoffel", 250), ("Brokkoli", 120), ("Olivenöl", 8)],
         ["supplement", "glutenfrei", "high-protein"]),
        ("Nacht-Protein-Shake Schoko",
         "Casein-Schoko-Shake für die Nacht.",
         [("Casein-Protein", 40), ("Milch 1,5%", 200), ("Proteinpulver Schoko", 10)],
         ["supplement", "laktose", "soja", "high-protein", "schnelle Zubereitung"]),
        ("Post-Workout Vollkorn-Pasta mit Putenhack",
         "KH + Protein sofort nach dem Training.",
         [("Vollkorn-Pasta (roh)", 100), ("Putenhackfleisch", 180), ("Tomatenmark", 60), ("Olivenöl", 8)],
         ["supplement", "gluten", "high-protein"]),
        ("Pre-Workout Cottage Cheese Bowl",
         "Langsames + schnelles Protein vor Training.",
         [("Cottage Cheese", 200), ("Banane", 100), ("Haferflocken", 40)],
         ["supplement", "laktose", "gluten", "high-protein"]),
        ("Recovery Kichererbsen-Curry-Bowl",
         "Entzündungshemmende Recovery-Mahlzeit.",
         [("Kichererbsen (gegart)", 200), ("Kokosmilch light", 150), ("Spinat frisch", 80), ("Gewürze (gemischt)", 8)],
         ["supplement", "vegetarisch", "vegan", "glutenfrei"]),
        ("Post-Workout Griechischer Joghurt-Shake",
         "Sofort-Shake mit Joghurt und Banane.",
         [("Griechischer Joghurt (0%)", 200), ("Banane", 100), ("Proteinpulver Vanille", 20), ("Milch 1,5%", 150)],
         ["supplement", "laktose", "soja", "high-protein", "schnelle Zubereitung"]),
    ]
    for item in items:
        name, desc, ingredients, tags = item
        d.append({
            "name": name,
            "category": "supplement",
            "description": desc,
            "tags": tags,
            "ingredients": [{"food_item": fi, "base_amount_g": amt} for fi, amt in ingredients],
        })
    return d


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    data: dict = json.loads(SEED.read_text(encoding="utf-8"))

    # Merge FoodItems (skip duplicates by name)
    existing_fi = {fi["name"] for fi in data["food_items"]}
    for fi in NEW_FOOD_ITEMS:
        if fi["name"] not in existing_fi:
            data["food_items"].append(fi)
            existing_fi.add(fi["name"])

    all_food_names = existing_fi

    # Collect new dishes (deduplicate by name, validate food items)
    existing_dish_names = {d["name"] for d in data["dishes"]}
    new_dishes = (
        _breakfast_dishes()
        + _lunch_extra_dishes()
        + _dinner_extra_dishes()
        + _snack_dishes()
        + _supplement_dishes()
        + _generate_bowls()
    )

    added = 0
    skipped_dup = 0
    skipped_missing = 0
    for dish in new_dishes:
        if dish["name"] in existing_dish_names:
            skipped_dup += 1
            continue
        missing = [
            ing["food_item"]
            for ing in dish["ingredients"]
            if ing["food_item"] not in all_food_names
        ]
        if missing:
            print(f"  WARNUNG: '{dish['name']}' — unbekannte Zutaten: {missing}")
            skipped_missing += 1
            continue
        data["dishes"].append(dish)
        existing_dish_names.add(dish["name"])
        added += 1

    SEED.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    fi_total = len(data["food_items"])
    dish_total = len(data["dishes"])
    print(
        f"Fertig — FoodItems: {fi_total} | Dishes: {dish_total} "
        f"(+{added} neu, {skipped_dup} Duplikate, {skipped_missing} fehlerhafte)"
    )
    by_cat: dict[str, int] = {}
    for dish in data["dishes"]:
        by_cat[dish["category"]] = by_cat.get(dish["category"], 0) + 1
    for cat, count in sorted(by_cat.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
