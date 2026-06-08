from __future__ import annotations

import io
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from werkzeug.utils import secure_filename

from database import init_db
from models import (
    AppSettings,
    Client,
    Dish,
    DishIngredient,
    FoodItem,
    MacroTemplate,
    MealPlan,
    MealSlot,
    db,
)
from planner import (
    GenerationResult,
    generate_plan,
    get_plan_total_macros,
    get_shopping_list,
    get_slot_macros,
    swap_variant,
)

_LOGGER = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).parent
_UPLOAD_FOLDER = _BASE_DIR / "static" / "uploads"
_ALLOWED_LOGO_EXTENSIONS = {"png", "jpg", "jpeg"}


def create_app() -> Flask:
    """Erstellt und konfiguriert die Flask-Anwendung."""
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "manani-fit-dev-key-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{_BASE_DIR / 'manani_fit.db'}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = str(_UPLOAD_FOLDER)
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

    db.init_app(app)
    init_db(app)

    _UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

    _register_routes(app)
    return app


def _register_routes(app: Flask) -> None:

    # ------------------------------------------------------------------ #
    # Dashboard                                                            #
    # ------------------------------------------------------------------ #

    @app.route("/")
    def index():
        clients = Client.query.filter_by(is_archived=False).order_by(Client.name).all()
        recent_plans = (
            MealPlan.query.order_by(MealPlan.date_created.desc()).limit(5).all()
        )
        return render_template(
            "index.html", clients=clients, recent_plans=recent_plans
        )

    # ------------------------------------------------------------------ #
    # Clients                                                              #
    # ------------------------------------------------------------------ #

    @app.route("/clients")
    def clients_list():
        show_archived = request.args.get("archived") == "1"
        query = Client.query
        if not show_archived:
            query = query.filter_by(is_archived=False)
        clients = query.order_by(Client.name).all()
        return render_template(
            "clients/list.html", clients=clients, show_archived=show_archived
        )

    @app.route("/clients/new", methods=["GET", "POST"])
    def clients_new():
        if request.method == "POST":
            client = _client_from_form(Client())
            db.session.add(client)
            db.session.commit()
            flash(f'Client „{client.name}“ angelegt.', "success")
            return redirect(url_for("clients_detail", client_id=client.id))
        return render_template("clients/form.html", client=None)

    @app.route("/clients/<int:client_id>")
    def clients_detail(client_id: int):
        client = Client.query.get_or_404(client_id)
        plans = (
            MealPlan.query.filter_by(client_id=client_id)
            .order_by(MealPlan.date_created.desc())
            .all()
        )
        return render_template("clients/detail.html", client=client, plans=plans)

    @app.route("/clients/<int:client_id>/edit", methods=["GET", "POST"])
    def clients_edit(client_id: int):
        client = Client.query.get_or_404(client_id)
        if request.method == "POST":
            _client_from_form(client)
            db.session.commit()
            flash("Client aktualisiert.", "success")
            return redirect(url_for("clients_detail", client_id=client_id))
        return render_template("clients/form.html", client=client)

    @app.route("/clients/<int:client_id>/archive", methods=["POST"])
    def clients_archive(client_id: int):
        client = Client.query.get_or_404(client_id)
        client.is_archived = not client.is_archived
        db.session.commit()
        state = "archiviert" if client.is_archived else "wiederhergestellt"
        flash(f'Client „{client.name}" {state}.', "success")
        return redirect(url_for("clients_list"))

    def _client_from_form(client: Client) -> Client:
        client.name = request.form["name"].strip()
        client.email = request.form.get("email", "").strip() or None
        client.phone = request.form.get("phone", "").strip() or None
        client.gender = request.form.get("gender", "").strip() or None
        client.goal = request.form.get("goal", "Halten")
        client.restrictions_text = (
            request.form.get("restrictions_text", "").strip() or None
        )
        tags_raw = request.form.get("restriction_tags", "").strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        client.set_restriction_tags(tags)

        weight = request.form.get("weight_kg", "").strip()
        height = request.form.get("height_cm", "").strip()
        birthdate = request.form.get("birthdate", "").strip()

        client.weight_kg = float(weight) if weight else None
        client.height_cm = float(height) if height else None
        if birthdate:
            try:
                client.birthdate = datetime.strptime(birthdate, "%Y-%m-%d").date()
            except ValueError:
                client.birthdate = None
        else:
            client.birthdate = None
        return client

    # ------------------------------------------------------------------ #
    # Plans — Erstellen                                                    #
    # ------------------------------------------------------------------ #

    @app.route("/plans/new", methods=["GET", "POST"])
    def plans_new():
        clients = Client.query.filter_by(is_archived=False).order_by(Client.name).all()
        selected_client = None
        client_id = request.args.get("client_id") or request.form.get("client_id")
        if client_id:
            selected_client = Client.query.get(int(client_id))
        return render_template(
            "plans/creator.html", clients=clients, selected_client=selected_client
        )

    @app.route("/plans/generate", methods=["POST"])
    def plans_generate():
        client_id = int(request.form["client_id"])
        client = Client.query.get_or_404(client_id)

        kcal = int(request.form["kcal_target"])
        n_meals = int(request.form["n_meals"])
        goal = request.form.get("goal", client.goal)
        notes = request.form.get("notes", "").strip() or None
        include_supplements = "include_supplements" in request.form
        plan_name = (
            request.form.get("plan_name", "").strip()
            or f"Ernährungsplan {datetime.now().strftime('%d.%m.%Y')}"
        )

        plan = MealPlan(
            client_id=client_id,
            name=plan_name,
            kcal_target=kcal,
            n_meals=n_meals,
            goal=goal,
            notes=notes,
            include_supplements=include_supplements,
            status="draft",
        )
        db.session.add(plan)
        db.session.flush()

        slots_data = []
        for i in range(1, n_meals + 1):
            slots_data.append(
                {
                    "guidelines_text": request.form.get(f"guidelines_{i}", "").strip(),
                    "label": request.form.get(f"label_{i}", "").strip()
                    or f"Mahlzeit {i}",
                }
            )

        result: GenerationResult = generate_plan(plan, slots_data)

        db.session.commit()

        if result.warnings:
            for w in result.warnings:
                flash(w.message, "warning")

        flash("Plan erfolgreich generiert!", "success")
        return redirect(url_for("plans_edit", plan_id=plan.id))

    # ------------------------------------------------------------------ #
    # Plans — Bearbeiten                                                   #
    # ------------------------------------------------------------------ #

    @app.route("/plans/<int:plan_id>/edit")
    def plans_edit(plan_id: int):
        plan = MealPlan.query.get_or_404(plan_id)
        all_dishes = Dish.query.filter_by(is_active=True).order_by(Dish.name).all()
        slot_macros = {
            slot.id: {
                "A": get_slot_macros(slot, "A"),
                "B": get_slot_macros(slot, "B"),
            }
            for slot in plan.meal_slots
        }
        total_macros = get_plan_total_macros(plan, "A")
        return render_template(
            "plans/editor.html",
            plan=plan,
            all_dishes=all_dishes,
            slot_macros=slot_macros,
            total_macros=total_macros,
        )

    @app.route("/plans/<int:plan_id>/swap_variant", methods=["POST"])
    def plans_swap_variant(plan_id: int):
        plan = MealPlan.query.get_or_404(plan_id)
        slot_id = int(request.form["slot_id"])
        variant = request.form["variant"].upper()
        new_dish_id = int(request.form["new_dish_id"])

        slot = MealSlot.query.get_or_404(slot_id)
        if slot.plan_id != plan_id:
            abort(400)

        try:
            swap_variant(slot, variant, new_dish_id)
            flash("Variante erfolgreich getauscht.", "success")
        except ValueError as exc:
            flash(str(exc), "danger")

        return redirect(url_for("plans_edit", plan_id=plan_id))

    @app.route("/plans/<int:plan_id>/finalize", methods=["POST"])
    def plans_finalize(plan_id: int):
        plan = MealPlan.query.get_or_404(plan_id)
        plan.status = "final"
        db.session.commit()
        flash("Plan als final markiert.", "success")
        return redirect(url_for("plans_edit", plan_id=plan_id))

    @app.route("/plans/<int:plan_id>/delete", methods=["POST"])
    def plans_delete(plan_id: int):
        plan = MealPlan.query.get_or_404(plan_id)
        client_id = plan.client_id
        db.session.delete(plan)
        db.session.commit()
        flash("Plan gelöscht.", "success")
        return redirect(url_for("clients_detail", client_id=client_id))

    # ------------------------------------------------------------------ #
    # Plans — PDF-Export                                                   #
    # ------------------------------------------------------------------ #

    @app.route("/plans/<int:plan_id>/pdf")
    def plans_pdf(plan_id: int):
        plan = MealPlan.query.get_or_404(plan_id)
        from pdf_generator import generate_pdf

        try:
            pdf_bytes = generate_pdf(plan, str(_UPLOAD_FOLDER))
        except Exception as exc:
            _LOGGER.exception("PDF-Generierung fehlgeschlagen für Plan %s", plan_id)
            flash(f"PDF-Fehler: {exc}", "danger")
            return redirect(url_for("plans_edit", plan_id=plan_id))

        filename = (
            f"ernaehrungsplan_{plan.client.name.replace(' ', '_')}"
            f"_{plan.date_created.strftime('%Y%m%d')}.pdf"
        )
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    @app.route("/plans/<int:plan_id>/preview")
    def plans_preview(plan_id: int):
        plan = MealPlan.query.get_or_404(plan_id)
        slot_macros = {
            slot.id: {
                "A": get_slot_macros(slot, "A"),
                "B": get_slot_macros(slot, "B"),
            }
            for slot in plan.meal_slots
        }
        total_macros = get_plan_total_macros(plan, "A")
        shopping_a = get_shopping_list(plan, "A")
        shopping_b = get_shopping_list(plan, "B")
        settings = {
            k: AppSettings.get(k, "")
            for k in ["primary_color", "secondary_color", "coach_name", "coach_contact", "disclaimer_text"]
        }
        return render_template(
            "plans/preview.html",
            plan=plan,
            slot_macros=slot_macros,
            total_macros=total_macros,
            shopping_a=shopping_a,
            shopping_b=shopping_b,
            settings=settings,
        )

    # ------------------------------------------------------------------ #
    # Gerichte                                                             #
    # ------------------------------------------------------------------ #

    @app.route("/dishes")
    def dishes_list():
        category = request.args.get("category", "")
        search = request.args.get("search", "").strip()
        query = Dish.query.filter_by(is_active=True)
        if category:
            query = query.filter_by(category=category)
        if search:
            query = query.filter(Dish.name.ilike(f"%{search}%"))
        dishes = query.order_by(Dish.name).all()
        categories = [
            ("breakfast", "Frühstück"),
            ("lunch", "Mittagessen"),
            ("dinner", "Abendessen"),
            ("snack", "Snack"),
            ("supplement", "Supplement"),
        ]
        return render_template(
            "dishes/list.html",
            dishes=dishes,
            categories=categories,
            selected_category=category,
            search=search,
        )

    @app.route("/dishes/new", methods=["GET", "POST"])
    def dishes_new():
        food_items = FoodItem.query.filter_by(is_active=True).order_by(FoodItem.name).all()
        if request.method == "POST":
            dish = _dish_from_form(Dish(), food_items)
            db.session.add(dish)
            db.session.commit()
            flash(f'Gericht „{dish.name}" angelegt.', "success")
            return redirect(url_for("dishes_list"))
        return render_template("dishes/form.html", dish=None, food_items=food_items)

    @app.route("/dishes/<int:dish_id>/edit", methods=["GET", "POST"])
    def dishes_edit(dish_id: int):
        dish = Dish.query.get_or_404(dish_id)
        food_items = FoodItem.query.filter_by(is_active=True).order_by(FoodItem.name).all()
        if request.method == "POST":
            _dish_from_form(dish, food_items)
            db.session.commit()
            flash("Gericht aktualisiert.", "success")
            return redirect(url_for("dishes_list"))
        return render_template("dishes/form.html", dish=dish, food_items=food_items)

    @app.route("/dishes/<int:dish_id>/delete", methods=["POST"])
    def dishes_delete(dish_id: int):
        dish = Dish.query.get_or_404(dish_id)
        dish.is_active = False
        db.session.commit()
        flash(f'Gericht „{dish.name}" gelöscht.', "success")
        return redirect(url_for("dishes_list"))

    def _dish_from_form(dish: Dish, food_items: list[FoodItem]) -> Dish:
        dish.name = request.form["name"].strip()
        dish.category = request.form["category"]
        dish.description = request.form.get("description", "").strip() or None
        tags_raw = request.form.get("tags", "").strip()
        dish.set_tags([t.strip() for t in tags_raw.split(",") if t.strip()])
        dish.is_custom = True

        for di in list(dish.dish_ingredients):
            db.session.delete(di)
        db.session.flush()

        fi_map = {fi.id: fi for fi in food_items}
        fi_ids = request.form.getlist("fi_id[]")
        amounts = request.form.getlist("fi_amount[]")
        for fi_id_str, amount_str in zip(fi_ids, amounts):
            try:
                fi_id = int(fi_id_str)
                amount = float(amount_str)
            except (ValueError, TypeError):
                continue
            if fi_id in fi_map and amount > 0:
                db.session.add(
                    DishIngredient(
                        dish=dish, food_item_id=fi_id, base_amount_g=amount
                    )
                )
        return dish

    # ------------------------------------------------------------------ #
    # Settings                                                             #
    # ------------------------------------------------------------------ #

    @app.route("/settings", methods=["GET", "POST"])
    def settings_view():
        macro_templates = MacroTemplate.query.all()
        if request.method == "POST":
            _save_settings()
            flash("Einstellungen gespeichert.", "success")
            return redirect(url_for("settings_view"))

        settings = {
            k: AppSettings.get(k, "")
            for k in [
                "logo_path",
                "primary_color",
                "secondary_color",
                "font_family",
                "coach_name",
                "coach_contact",
                "disclaimer_text",
                "portion_min_g",
                "portion_max_g",
                "macro_tolerance_pct",
            ]
        }
        return render_template(
            "settings.html", settings=settings, macro_templates=macro_templates
        )

    def _save_settings() -> None:
        text_keys = [
            "primary_color",
            "secondary_color",
            "font_family",
            "coach_name",
            "coach_contact",
            "disclaimer_text",
            "portion_min_g",
            "portion_max_g",
            "macro_tolerance_pct",
        ]
        for key in text_keys:
            if key in request.form:
                AppSettings.set(key, request.form[key])

        logo_file = request.files.get("logo_file")
        if logo_file and logo_file.filename:
            ext = logo_file.filename.rsplit(".", 1)[-1].lower()
            if ext in _ALLOWED_LOGO_EXTENSIONS:
                filename = secure_filename(f"logo.{ext}")
                save_path = _UPLOAD_FOLDER / filename
                logo_file.save(str(save_path))
                AppSettings.set("logo_path", str(save_path))

        for tmpl in MacroTemplate.query.all():
            p = request.form.get(f"protein_{tmpl.goal_name}")
            c = request.form.get(f"carbs_{tmpl.goal_name}")
            f = request.form.get(f"fat_{tmpl.goal_name}")
            if p and c and f:
                tmpl.protein_pct = float(p)
                tmpl.carbs_pct = float(c)
                tmpl.fat_pct = float(f)
        db.session.commit()

    # ------------------------------------------------------------------ #
    # Template-Filter                                                      #
    # ------------------------------------------------------------------ #

    @app.template_filter("category_label")
    def category_label(cat: str) -> str:
        labels = {
            "breakfast": "Frühstück",
            "lunch": "Mittagessen",
            "dinner": "Abendessen",
            "snack": "Snack",
            "supplement": "Supplement",
        }
        return labels.get(cat, cat)

    @app.template_filter("goal_label")
    def goal_label(goal: str) -> str:
        return goal


app = create_app()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, port=5000)
