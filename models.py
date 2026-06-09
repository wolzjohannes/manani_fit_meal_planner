from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Client(db.Model):
    """Ein Coaching-Kunde mit Körperdaten und Einschränkungen."""

    __tablename__ = "clients"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(120), nullable=False)
    email: str | None = db.Column(db.String(200))
    phone: str | None = db.Column(db.String(50))
    birthdate: date | None = db.Column(db.Date)
    gender: str | None = db.Column(db.String(20))
    weight_kg: float | None = db.Column(db.Float)
    height_cm: float | None = db.Column(db.Float)
    goal: str = db.Column(db.String(30), nullable=False, default="Halten")
    restrictions_text: str | None = db.Column(db.Text)
    restriction_tags: str = db.Column(db.Text, default="[]")
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at: datetime = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_archived: bool = db.Column(db.Boolean, default=False)

    plans = db.relationship("MealPlan", back_populates="client", lazy="dynamic")

    def get_restriction_tags(self) -> list[str]:
        return json.loads(self.restriction_tags or "[]")

    def set_restriction_tags(self, tags: list[str]) -> None:
        self.restriction_tags = json.dumps(tags, ensure_ascii=False)

    def __repr__(self) -> str:
        return f"Client(id={self.id}, name={self.name!r})"


class MealPlan(db.Model):
    """Ein Tages-Essensplan für einen Client."""

    __tablename__ = "meal_plans"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    client_id: int = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    name: str = db.Column(db.String(200), nullable=False)
    date_created: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    date_modified: datetime = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    kcal_target: int = db.Column(db.Integer, nullable=False)
    n_meals: int = db.Column(db.Integer, nullable=False, default=3)
    goal: str = db.Column(db.String(30), nullable=False)
    notes: str | None = db.Column(db.Text)
    status: str = db.Column(db.String(10), default="draft")
    include_supplements: bool = db.Column(db.Boolean, default=False)

    client = db.relationship("Client", back_populates="plans")
    meal_slots = db.relationship(
        "MealSlot",
        back_populates="plan",
        order_by="MealSlot.position",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"MealPlan(id={self.id}, name={self.name!r})"


class MealSlot(db.Model):
    """Eine Mahlzeit-Position innerhalb eines Plans mit 2 Gericht-Varianten."""

    __tablename__ = "meal_slots"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    plan_id: int = db.Column(
        db.Integer, db.ForeignKey("meal_plans.id"), nullable=False
    )
    position: int = db.Column(db.Integer, nullable=False)
    label: str | None = db.Column(db.String(100))
    kcal_target: float = db.Column(db.Float, nullable=False)
    guidelines_text: str | None = db.Column(db.String(200))
    variant_a_dish_id: int | None = db.Column(db.Integer, db.ForeignKey("dishes.id"))
    variant_b_dish_id: int | None = db.Column(db.Integer, db.ForeignKey("dishes.id"))

    plan = db.relationship("MealPlan", back_populates="meal_slots")
    variant_a_dish = db.relationship("Dish", foreign_keys=[variant_a_dish_id])
    variant_b_dish = db.relationship("Dish", foreign_keys=[variant_b_dish_id])
    scaled_ingredients = db.relationship(
        "PlanDishIngredient",
        back_populates="meal_slot",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"MealSlot(plan={self.plan_id}, pos={self.position})"


class PlanDishIngredient(db.Model):
    """Skalierte Zutat für eine Variante innerhalb eines MealSlots."""

    __tablename__ = "plan_dish_ingredients"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    meal_slot_id: int = db.Column(
        db.Integer, db.ForeignKey("meal_slots.id"), nullable=False
    )
    variant: str = db.Column(db.String(1), nullable=False)
    food_item_id: int = db.Column(
        db.Integer, db.ForeignKey("food_items.id"), nullable=False
    )
    amount_g: float = db.Column(db.Float, nullable=False)
    kcal: float = db.Column(db.Float, nullable=False)
    protein_g: float = db.Column(db.Float, nullable=False)
    carbs_g: float = db.Column(db.Float, nullable=False)
    fat_g: float = db.Column(db.Float, nullable=False)

    meal_slot = db.relationship("MealSlot", back_populates="scaled_ingredients")
    food_item = db.relationship("FoodItem")

    def __repr__(self) -> str:
        return (
            f"PlanDishIngredient(slot={self.meal_slot_id}, "
            f"variant={self.variant}, item={self.food_item_id})"
        )


class Dish(db.Model):
    """Ein Gericht in der Datenbank mit Basis-Zutaten."""

    __tablename__ = "dishes"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(200), nullable=False)
    category: str = db.Column(db.String(30), nullable=False)
    description: str | None = db.Column(db.Text)
    tags: str = db.Column(db.Text, default="[]")
    is_custom: bool = db.Column(db.Boolean, default=False)
    is_active: bool = db.Column(db.Boolean, default=True)

    dish_ingredients = db.relationship(
        "DishIngredient",
        back_populates="dish",
        cascade="all, delete-orphan",
    )

    def get_tags(self) -> list[str]:
        return json.loads(self.tags or "[]")

    def set_tags(self, tags: list[str]) -> None:
        self.tags = json.dumps(tags, ensure_ascii=False)

    @property
    def base_kcal(self) -> float:
        return sum(
            (di.base_amount_g / 100.0) * di.food_item.kcal_per_100g
            for di in self.dish_ingredients
        )

    @property
    def base_protein_g(self) -> float:
        return sum(
            (di.base_amount_g / 100.0) * di.food_item.protein_per_100g
            for di in self.dish_ingredients
        )

    @property
    def base_carbs_g(self) -> float:
        return sum(
            (di.base_amount_g / 100.0) * di.food_item.carbs_per_100g
            for di in self.dish_ingredients
        )

    @property
    def base_fat_g(self) -> float:
        return sum(
            (di.base_amount_g / 100.0) * di.food_item.fat_per_100g
            for di in self.dish_ingredients
        )

    @property
    def base_total_g(self) -> float:
        return sum(di.base_amount_g for di in self.dish_ingredients)

    def __repr__(self) -> str:
        return f"Dish(id={self.id}, name={self.name!r})"


class DishIngredient(db.Model):
    """Verknüpft ein Gericht mit einem Lebensmittel und Basis-Menge."""

    __tablename__ = "dish_ingredients"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    dish_id: int = db.Column(db.Integer, db.ForeignKey("dishes.id"), nullable=False)
    food_item_id: int = db.Column(
        db.Integer, db.ForeignKey("food_items.id"), nullable=False
    )
    base_amount_g: float = db.Column(db.Float, nullable=False)

    dish = db.relationship("Dish", back_populates="dish_ingredients")
    food_item = db.relationship("FoodItem")

    def __repr__(self) -> str:
        return f"DishIngredient(dish={self.dish_id}, item={self.food_item_id})"


class FoodItem(db.Model):
    """Einzelnes Lebensmittel mit Nährwerten pro 100 g."""

    __tablename__ = "food_items"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(200), nullable=False)
    kcal_per_100g: float = db.Column(db.Float, nullable=False)
    protein_per_100g: float = db.Column(db.Float, nullable=False, default=0.0)
    carbs_per_100g: float = db.Column(db.Float, nullable=False, default=0.0)
    fat_per_100g: float = db.Column(db.Float, nullable=False, default=0.0)
    allergens: str = db.Column(db.Text, default="[]")
    is_supplement: bool = db.Column(db.Boolean, default=False)
    is_active: bool = db.Column(db.Boolean, default=True)

    def get_allergens(self) -> list[str]:
        return json.loads(self.allergens or "[]")

    def set_allergens(self, allergens: list[str]) -> None:
        self.allergens = json.dumps(allergens, ensure_ascii=False)

    def macros_for(self, amount_g: float) -> dict[str, float]:
        """Makros für eine gegebene Menge in Gramm."""
        factor = amount_g / 100.0
        return {
            "kcal": round(self.kcal_per_100g * factor, 1),
            "protein_g": round(self.protein_per_100g * factor, 1),
            "carbs_g": round(self.carbs_per_100g * factor, 1),
            "fat_g": round(self.fat_per_100g * factor, 1),
        }

    def __repr__(self) -> str:
        return f"FoodItem(id={self.id}, name={self.name!r})"


class MacroTemplate(db.Model):
    """Makro-Split-Vorlage für ein Fitness-Ziel."""

    __tablename__ = "macro_templates"
    __allow_unmapped__ = True

    id: int = db.Column(db.Integer, primary_key=True)
    goal_name: str = db.Column(db.String(30), nullable=False, unique=True)
    protein_pct: float = db.Column(db.Float, nullable=False)
    carbs_pct: float = db.Column(db.Float, nullable=False)
    fat_pct: float = db.Column(db.Float, nullable=False)
    calculation_mode: str = db.Column(
        db.String(10), nullable=False, default="pct", server_default="pct"
    )
    protein_g_per_kg: float | None = db.Column(db.Float, nullable=True)
    fat_g_per_kg: float | None = db.Column(db.Float, nullable=True)

    def __repr__(self) -> str:
        return f"MacroTemplate(goal={self.goal_name!r})"


class AppSettings(db.Model):
    """Key-Value-Store für App-weite Einstellungen."""

    __tablename__ = "app_settings"
    __allow_unmapped__ = True

    key: str = db.Column(db.String(100), primary_key=True)
    value: str | None = db.Column(db.Text)

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        row = cls.query.get(key)
        return row.value if row is not None else default

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        row = cls.query.get(key)
        if row is None:
            row = cls(key=key)
            db.session.add(row)
        row.value = str(value) if value is not None else None
        db.session.commit()

    def __repr__(self) -> str:
        return f"AppSettings(key={self.key!r})"
