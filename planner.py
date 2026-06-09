from __future__ import annotations

import logging
from dataclasses import dataclass, field

from models import (
    AppSettings,
    Client,
    Dish,
    DishIngredient,
    MacroTemplate,
    MealPlan,
    MealSlot,
    PlanDishIngredient,
    db,
)

_LOGGER = logging.getLogger(__name__)

_CATEGORY_BY_POSITION = {
    1: "breakfast",
    2: "lunch",
    3: "lunch",
    4: "snack",
    5: "dinner",
    6: "snack",
    7: "dinner",
    8: "supplement",
}

_LIGHT_FACTOR = 0.70


@dataclass
class MacroSplit:
    """Makro-Aufschlüsselung in Gramm für eine Kalorienmenge."""

    kcal: float
    protein_g: float
    carbs_g: float
    fat_g: float


@dataclass
class ValidationWarning:
    """Warnung aus der Plan-Validierung."""

    meal_slot_position: int | None
    message: str


@dataclass
class GenerationResult:
    """Ergebnis der Plan-Generierung."""

    plan: MealPlan
    warnings: list[ValidationWarning] = field(default_factory=list)


def resolve_macro_overrides(plan: MealPlan) -> dict:
    """Gibt die effektiven Makro-Overrides für einen Plan zurück.

    Priorität: Plan-Override > Klient-Override > leeres dict (→ globales Template).
    """
    plan_ov = plan.get_macro_overrides()
    if plan_ov:
        return plan_ov
    return plan.client.get_macro_overrides()


def calculate_macros(
    kcal: float,
    goal: str,
    weight_kg: float | None = None,
    overrides: dict | None = None,
) -> MacroSplit:
    """Berechnet Makros in Gramm für ein Kalorienziel und ein Fitness-Ziel.

    Priorität: overrides (Klient/Plan-spezifisch) > globales MacroTemplate.
    Modi: "pct" (Prozentual) oder "g_per_kg" (per kg Körpergewicht).
    """
    if overrides:
        mode = overrides.get("mode", "pct")
        if mode == "g_per_kg" and weight_kg is not None:
            p_gkg = overrides.get("protein_g_per_kg")
            f_gkg = overrides.get("fat_g_per_kg")
            if p_gkg is not None and f_gkg is not None:
                protein_g = float(p_gkg) * weight_kg
                fat_g = float(f_gkg) * weight_kg
                carbs_kcal = kcal - protein_g * 4.0 - fat_g * 9.0
                carbs_g = max(0.0, carbs_kcal / 4.0)
                return MacroSplit(kcal=kcal, protein_g=protein_g, carbs_g=carbs_g, fat_g=fat_g)
        else:
            p_pct = overrides.get("protein_pct")
            c_pct = overrides.get("carbs_pct")
            f_pct = overrides.get("fat_pct")
            if p_pct is not None and c_pct is not None and f_pct is not None:
                protein_g = (kcal * float(p_pct) / 100.0) / 4.0
                carbs_g = (kcal * float(c_pct) / 100.0) / 4.0
                fat_g = (kcal * float(f_pct) / 100.0) / 9.0
                return MacroSplit(kcal=kcal, protein_g=protein_g, carbs_g=carbs_g, fat_g=fat_g)

    tmpl = MacroTemplate.query.filter_by(goal_name=goal).first()
    if tmpl is None:
        tmpl = MacroTemplate(
            protein_pct=35.0, carbs_pct=45.0, fat_pct=20.0, calculation_mode="pct"
        )

    use_g_per_kg = (
        getattr(tmpl, "calculation_mode", "pct") == "g_per_kg"
        and weight_kg is not None
        and tmpl.protein_g_per_kg is not None
        and tmpl.fat_g_per_kg is not None
    )

    if use_g_per_kg:
        protein_g = tmpl.protein_g_per_kg * weight_kg
        fat_g = tmpl.fat_g_per_kg * weight_kg
        carbs_kcal = kcal - protein_g * 4.0 - fat_g * 9.0
        carbs_g = max(0.0, carbs_kcal / 4.0)
    else:
        protein_g = (kcal * tmpl.protein_pct / 100.0) / 4.0
        carbs_g = (kcal * tmpl.carbs_pct / 100.0) / 4.0
        fat_g = (kcal * tmpl.fat_pct / 100.0) / 9.0

    return MacroSplit(kcal=kcal, protein_g=protein_g, carbs_g=carbs_g, fat_g=fat_g)


def _slot_kcal_targets(kcal_total: float, slots_data: list[dict]) -> list[float]:
    """Verteilt Tageskalorien auf Mahlzeiten — 'leicht' erhält 0.70× des Anteils."""
    n = len(slots_data)
    base = kcal_total / n

    raw: list[float] = []
    for sd in slots_data:
        guidelines = (sd.get("guidelines_text") or "").lower()
        if "leicht" in guidelines:
            raw.append(base * _LIGHT_FACTOR)
        else:
            raw.append(base)

    deficit = kcal_total - sum(raw)
    light_count = sum(
        1
        for sd in slots_data
        if "leicht" in (sd.get("guidelines_text") or "").lower()
    )
    normal_count = n - light_count
    if normal_count > 0:
        bonus = deficit / normal_count
        result = []
        for i, sd in enumerate(slots_data):
            guidelines = (sd.get("guidelines_text") or "").lower()
            if "leicht" in guidelines:
                result.append(raw[i])
            else:
                result.append(raw[i] + bonus)
    else:
        result = raw

    return result


def _category_for_position(position: int, n_meals: int) -> str:
    """Bestimmt die sinnvolle Mahlzeit-Kategorie anhand der Position."""
    if n_meals == 1:
        return "lunch"
    if n_meals == 2:
        return "breakfast" if position == 1 else "dinner"

    mapping = {
        1: "breakfast",
        2: "lunch",
        3: "lunch" if n_meals <= 4 else "snack",
        4: "dinner" if n_meals <= 4 else "lunch",
        5: "dinner",
        6: "snack",
        7: "dinner",
        8: "supplement",
    }
    return mapping.get(position, "snack")


def _client_forbidden_allergens(client: Client) -> set[str]:
    """Gibt die gesperrten Allergen-Tags eines Clients zurück."""
    tags = client.get_restriction_tags()
    allergen_map = {
        "laktosefrei": "milch",
        "glutenfrei": "gluten",
        "nussallergie": "nüsse",
        "kein schweinefleisch": "schwein",
        "kein fisch": "fisch",
        "vegetarisch": None,
        "vegan": None,
    }
    blocked: set[str] = set()
    for tag in tags:
        mapped = allergen_map.get(tag.lower())
        if mapped:
            blocked.add(mapped)
    return blocked


def _keyword_filter(dish: Dish, guidelines: str) -> bool:
    """Prüft ob ein Gericht zu den Richtlinien-Keywords passt."""
    if not guidelines:
        return True
    kw = guidelines.lower()
    dish_tags_str = " ".join(dish.get_tags()).lower()
    dish_name_lower = dish.name.lower()
    keywords = [w.strip() for w in kw.split() if len(w.strip()) > 2]
    for kw_word in keywords:
        if kw_word in dish_tags_str or kw_word in dish_name_lower:
            return True
    return not keywords


def _dish_macro_ratios(dish: Dish) -> tuple[float, float, float]:
    """Gibt (protein_ratio, carbs_ratio, fat_ratio) als Anteil an Gesamt-kcal zurück."""
    protein_kcal = 0.0
    carbs_kcal = 0.0
    fat_kcal = 0.0
    total_kcal = 0.0
    for di in dish.dish_ingredients:
        macros = di.food_item.macros_for(di.base_amount_g)
        protein_kcal += macros["protein_g"] * 4
        carbs_kcal += macros["carbs_g"] * 4
        fat_kcal += macros["fat_g"] * 9
        total_kcal += macros["kcal"]
    if total_kcal <= 0:
        return (0.33, 0.34, 0.33)
    return (protein_kcal / total_kcal, carbs_kcal / total_kcal, fat_kcal / total_kcal)


def _macro_distance(
    r1: tuple[float, float, float], r2: tuple[float, float, float]
) -> float:
    """Euklidischer Abstand zweier Makro-Verhältnis-Tupel."""
    return sum((a - b) ** 2 for a, b in zip(r1, r2)) ** 0.5


def select_dish_variants(
    position: int,
    n_meals: int,
    guidelines: str,
    client: Client,
    used_dish_ids: set[int],
    target_macro_ratios: tuple[float, float, float] | None = None,
) -> tuple[Dish | None, Dish | None]:
    """Wählt 2 verschiedene Gerichte für eine Mahlzeit aus der DB.

    Filterreihenfolge:
    1. Kategorie passend zur Position
    2. Client-Einschränkungen (Allergen-Tags) ausschließen
    3. Richtlinien-Keywords matchen
    4. Bereits verwendete Gerichte bevorzugt vermeiden
    5. Wenn target_macro_ratios angegeben: nach Makro-Nähe sortieren
    6. Fallback: alle aktiven Gerichte ohne Allergen-Konflikt
    """
    category = _category_for_position(position, n_meals)
    forbidden = _client_forbidden_allergens(client)

    all_dishes: list[Dish] = Dish.query.filter_by(
        is_active=True, category=category
    ).all()

    def _is_allowed(dish: Dish) -> bool:
        for di in dish.dish_ingredients:
            for allergen in di.food_item.get_allergens():
                if allergen.lower() in forbidden:
                    return False
        return True

    allowed = [d for d in all_dishes if _is_allowed(d)]

    if not allowed:
        all_active = Dish.query.filter_by(is_active=True).all()
        allowed = [d for d in all_active if _is_allowed(d)]

    if not allowed:
        return None, None

    keyword_matched = [d for d in allowed if _keyword_filter(d, guidelines)]
    pool = keyword_matched if keyword_matched else allowed

    fresh = [d for d in pool if d.id not in used_dish_ids]
    ordered = fresh + [d for d in pool if d.id in used_dish_ids]

    if len(ordered) == 0:
        return None, None
    if len(ordered) == 1:
        return ordered[0], ordered[0]

    if target_macro_ratios is not None:
        ordered.sort(
            key=lambda d: _macro_distance(target_macro_ratios, _dish_macro_ratios(d))
        )
        return ordered[0], ordered[1]

    dish_a = ordered[0]
    ratios_a = _dish_macro_ratios(dish_a)
    remaining = sorted(
        ordered[1:],
        key=lambda d: _macro_distance(ratios_a, _dish_macro_ratios(d)),
    )
    return dish_a, remaining[0]


def _scale_dish(
    dish: Dish,
    meal_kcal: float,
    variant: str,
    meal_slot_id: int,
    warnings: list[ValidationWarning],
    position: int,
) -> list[PlanDishIngredient]:
    """Skaliert alle Zutaten eines Gerichts auf die Mahlzeit-Kalorien."""
    base_kcal = dish.base_kcal
    if base_kcal <= 0:
        _LOGGER.warning("Gericht %r hat 0 Basis-Kalorien", dish.name)
        return []

    scale = meal_kcal / base_kcal

    min_g = float(AppSettings.get("portion_min_g", 150))
    max_g = float(AppSettings.get("portion_max_g", 1200))
    scaled_total = dish.base_total_g * scale

    if scaled_total < min_g or scaled_total > max_g:
        warnings.append(
            ValidationWarning(
                meal_slot_position=position,
                message=(
                    f"Mahlzeit {position} Variante {variant} ({dish.name}): "
                    f"Portionsgröße {scaled_total:.0f} g liegt außerhalb "
                    f"[{min_g:.0f} g – {max_g:.0f} g]."
                ),
            )
        )

    if scale > 3.0 or scale < 0.3:
        warnings.append(
            ValidationWarning(
                meal_slot_position=position,
                message=(
                    f"Mahlzeit {position} Variante {variant} ({dish.name}): "
                    f"Skalierungsfaktor {scale:.2f}× ist unrealistisch."
                ),
            )
        )

    result: list[PlanDishIngredient] = []
    for di in dish.dish_ingredients:
        amount = di.base_amount_g * scale
        macros = di.food_item.macros_for(amount)
        result.append(
            PlanDishIngredient(
                meal_slot_id=meal_slot_id,
                variant=variant,
                food_item_id=di.food_item_id,
                amount_g=round(amount, 1),
                kcal=macros["kcal"],
                protein_g=macros["protein_g"],
                carbs_g=macros["carbs_g"],
                fat_g=macros["fat_g"],
            )
        )
    return result


def generate_plan(
    plan: MealPlan,
    slots_data: list[dict],
) -> GenerationResult:
    """Generiert alle MealSlots inkl. skalierter Zutaten für einen Plan.

    Args:
        plan: Der bereits in der DB gespeicherte MealPlan.
        slots_data: Liste von Dicts mit keys: guidelines_text (optional).

    Returns:
        GenerationResult mit dem aktualisierten Plan und Warnungen.
    """
    warnings: list[ValidationWarning] = []
    client = plan.client

    for slot in plan.meal_slots:
        db.session.delete(slot)
    db.session.flush()

    kcal_targets = _slot_kcal_targets(float(plan.kcal_target), slots_data)

    used_dish_ids: set[int] = set()
    tolerance_pct = float(AppSettings.get("macro_tolerance_pct", 5))

    target_macros = calculate_macros(
        float(plan.kcal_target), plan.goal, plan.client.weight_kg,
        overrides=resolve_macro_overrides(plan),
    )
    if plan.kcal_target > 0:
        kcal_f = float(plan.kcal_target)
        target_macro_ratios: tuple[float, float, float] | None = (
            (target_macros.protein_g * 4.0) / kcal_f,
            (target_macros.carbs_g * 4.0) / kcal_f,
            (target_macros.fat_g * 9.0) / kcal_f,
        )
    else:
        target_macro_ratios = None

    total_actual_kcal = 0.0

    for i, (sd, slot_kcal) in enumerate(zip(slots_data, kcal_targets), start=1):
        guidelines = sd.get("guidelines_text") or ""
        label = sd.get("label") or f"Mahlzeit {i}"

        dish_a, dish_b = select_dish_variants(
            position=i,
            n_meals=plan.n_meals,
            guidelines=guidelines,
            client=client,
            used_dish_ids=used_dish_ids,
            target_macro_ratios=target_macro_ratios,
        )

        if dish_a is not None:
            used_dish_ids.add(dish_a.id)
        if dish_b is not None and dish_b.id != (dish_a.id if dish_a else None):
            used_dish_ids.add(dish_b.id)

        slot = MealSlot(
            plan_id=plan.id,
            position=i,
            label=label,
            kcal_target=round(slot_kcal, 1),
            guidelines_text=guidelines,
            variant_a_dish_id=dish_a.id if dish_a else None,
            variant_b_dish_id=dish_b.id if dish_b else None,
        )
        db.session.add(slot)
        db.session.flush()

        if dish_a:
            for ing in _scale_dish(dish_a, slot_kcal, "A", slot.id, warnings, i):
                db.session.add(ing)
                total_actual_kcal += ing.kcal

        if dish_b and dish_b != dish_a:
            for ing in _scale_dish(dish_b, slot_kcal, "B", slot.id, warnings, i):
                db.session.add(ing)

    _validate_daily_macros(plan, warnings, tolerance_pct)

    db.session.commit()
    return GenerationResult(plan=plan, warnings=warnings)


def _validate_daily_macros(
    plan: MealPlan,
    warnings: list[ValidationWarning],
    tolerance_pct: float,
) -> None:
    """Prüft ob die Tages-Kalorien und Makros innerhalb der Toleranz liegen."""
    target_macros = calculate_macros(
        float(plan.kcal_target), plan.goal, plan.client.weight_kg,
        overrides=resolve_macro_overrides(plan),
    )

    slots = MealSlot.query.filter_by(plan_id=plan.id).all()
    ings_a = [
        ing
        for slot in slots
        for ing in slot.scaled_ingredients
        if ing.variant == "A"
    ]
    actual_kcal = sum(i.kcal for i in ings_a)
    actual_protein = sum(i.protein_g for i in ings_a)
    actual_fat = sum(i.fat_g for i in ings_a)

    target_kcal = float(plan.kcal_target)
    if target_kcal > 0:
        deviation_pct = abs(actual_kcal - target_kcal) / target_kcal * 100
        if deviation_pct > tolerance_pct * 2:
            warnings.append(
                ValidationWarning(
                    meal_slot_position=None,
                    message=(
                        f"Tages-Kalorien: Ziel {target_kcal:.0f} kcal, "
                        f"tatsächlich {actual_kcal:.0f} kcal "
                        f"(Abweichung {deviation_pct:.1f} %)."
                    ),
                )
            )

    if target_macros.protein_g > 0:
        prot_dev = abs(actual_protein - target_macros.protein_g) / target_macros.protein_g * 100
        if prot_dev > tolerance_pct * 2:
            warnings.append(
                ValidationWarning(
                    meal_slot_position=None,
                    message=(
                        f"Protein: Ziel {target_macros.protein_g:.0f} g, "
                        f"tatsächlich {actual_protein:.0f} g "
                        f"(Abweichung {prot_dev:.1f} %)."
                    ),
                )
            )

    if target_macros.fat_g > 0:
        fat_dev = abs(actual_fat - target_macros.fat_g) / target_macros.fat_g * 100
        if fat_dev > tolerance_pct * 2:
            warnings.append(
                ValidationWarning(
                    meal_slot_position=None,
                    message=(
                        f"Fett: Ziel {target_macros.fat_g:.0f} g, "
                        f"tatsächlich {actual_fat:.0f} g "
                        f"(Abweichung {fat_dev:.1f} %)."
                    ),
                )
            )


def get_slot_macros(slot: MealSlot, variant: str) -> MacroSplit:
    """Summiert die skalierten Makros eines MealSlots für eine Variante."""
    ings = [i for i in slot.scaled_ingredients if i.variant == variant]
    return MacroSplit(
        kcal=round(sum(i.kcal for i in ings), 1),
        protein_g=round(sum(i.protein_g for i in ings), 1),
        carbs_g=round(sum(i.carbs_g for i in ings), 1),
        fat_g=round(sum(i.fat_g for i in ings), 1),
    )


def get_plan_total_macros(plan: MealPlan, variant: str = "A") -> MacroSplit:
    """Summiert alle Makros eines Plans für eine Variante."""
    totals = MacroSplit(kcal=0.0, protein_g=0.0, carbs_g=0.0, fat_g=0.0)
    for slot in plan.meal_slots:
        m = get_slot_macros(slot, variant)
        totals.kcal += m.kcal
        totals.protein_g += m.protein_g
        totals.carbs_g += m.carbs_g
        totals.fat_g += m.fat_g
    totals.kcal = round(totals.kcal, 1)
    totals.protein_g = round(totals.protein_g, 1)
    totals.carbs_g = round(totals.carbs_g, 1)
    totals.fat_g = round(totals.fat_g, 1)
    return totals


def get_shopping_list(plan: MealPlan, variant: str) -> list[dict]:
    """Erstellt eine alphabetisch sortierte Einkaufsliste für eine Variante."""
    aggregated: dict[str, dict] = {}
    for slot in plan.meal_slots:
        for ing in slot.scaled_ingredients:
            if ing.variant != variant:
                continue
            name = ing.food_item.name
            if name not in aggregated:
                aggregated[name] = {
                    "name": name,
                    "amount_g": 0.0,
                    "unit": "g",
                }
            aggregated[name]["amount_g"] += ing.amount_g

    result = sorted(aggregated.values(), key=lambda x: x["name"])
    for item in result:
        item["amount_g"] = round(item["amount_g"], 0)
    return result


def swap_variant(slot: MealSlot, variant: str, new_dish_id: int) -> None:
    """Tauscht das Gericht einer Variante aus und skaliert neu.

    Args:
        slot: Der MealSlot der geändert werden soll.
        variant: "A" oder "B".
        new_dish_id: ID des neuen Gerichts.
    """
    new_dish = Dish.query.get(new_dish_id)
    if new_dish is None:
        raise ValueError(f"Gericht {new_dish_id} nicht gefunden.")

    for ing in list(slot.scaled_ingredients):
        if ing.variant == variant:
            db.session.delete(ing)
    db.session.flush()

    if variant == "A":
        slot.variant_a_dish_id = new_dish_id
    else:
        slot.variant_b_dish_id = new_dish_id

    warnings: list[ValidationWarning] = []
    for ing in _scale_dish(
        new_dish, float(slot.kcal_target), variant, slot.id, warnings, slot.position
    ):
        db.session.add(ing)

    db.session.commit()
