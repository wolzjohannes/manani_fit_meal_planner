"""Restore client Dennis Kliesing and his meal plan from PDF backup."""
from __future__ import annotations

import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from database import db
from models import Client, Dish, MealPlan, MealSlot, PlanDishIngredient

SLOTS = [
    {"position": 1, "label": "Breakfast", "kcal": 567.0, "dish_a": 11, "dish_b": 50},
    {"position": 2, "label": "Lunch", "kcal": 567.0, "dish_a": 6, "dish_b": 242},
    {"position": 3, "label": "Dinner", "kcal": 567.0, "dish_a": 7, "dish_b": 136},
]


def main() -> None:
    """Restore Dennis Kliesing client and meal plan."""
    app = create_app()

    with app.app_context():
        # Client
        client = Client(name="Dennis Kliesing", goal="Abnehmen")
        db.session.add(client)
        db.session.flush()
        print(f"✓ Client {client.id}: {client.name}")

        # Plan
        plan = MealPlan(
            client_id=client.id,
            name="Start LB Diät Plan 09.06.2026",
            kcal_target=1700,
            goal="Abnehmen",
            n_meals=3,
            status="final",
            date_created=date(2026, 6, 9),
        )
        db.session.add(plan)
        db.session.flush()
        print(f"✓ Plan {plan.id}: {plan.name}")

        # Slots + skalierte Zutaten
        for s in SLOTS:
            slot = MealSlot(
                plan_id=plan.id,
                position=s["position"],
                label=s["label"],
                kcal_target=s["kcal"],
                variant_a_dish_id=s["dish_a"],
                variant_b_dish_id=s["dish_b"],
            )
            db.session.add(slot)
            db.session.flush()

            # PlanDishIngredient für beide Varianten skalieren
            for variant, dish_id in [("A", s["dish_a"]), ("B", s["dish_b"])]:
                dish = db.session.get(Dish, dish_id)
                if dish and dish.base_kcal:
                    factor = s["kcal"] / dish.base_kcal
                    for di in dish.dish_ingredients:
                        scaled_amount = di.base_amount_g * factor
                        pdi = PlanDishIngredient(
                            meal_slot_id=slot.id,
                            variant=variant,
                            food_item_id=di.food_item_id,
                            amount_g=round(scaled_amount, 1),
                            kcal=round(
                                (scaled_amount / 100.0) * di.food_item.kcal_per_100g, 1
                            ),
                            protein_g=round(
                                (scaled_amount / 100.0) * di.food_item.protein_per_100g, 1
                            ),
                            carbs_g=round(
                                (scaled_amount / 100.0) * di.food_item.carbs_per_100g, 1
                            ),
                            fat_g=round(
                                (scaled_amount / 100.0) * di.food_item.fat_per_100g, 1
                            ),
                        )
                        db.session.add(pdi)

        db.session.commit()
        print("✓ Fertig. Alle Slots mit skalierten Zutaten erstellt.")


if __name__ == "__main__":
    main()
