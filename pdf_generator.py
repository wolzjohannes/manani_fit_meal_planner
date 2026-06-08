from __future__ import annotations

import base64
import io
import logging
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")

from models import AppSettings, MealPlan
from planner import get_plan_total_macros, get_shopping_list, get_slot_macros

_LOGGER = logging.getLogger(__name__)

_FONT_URLS = {
    "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap",
    "Montserrat": "https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap",
    "Raleway": "https://fonts.googleapis.com/css2?family=Raleway:wght@400;600;700&display=swap",
    "Open Sans": "https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap",
}


def _settings() -> dict[str, str]:
    keys = [
        "logo_path",
        "primary_color",
        "secondary_color",
        "font_family",
        "coach_name",
        "coach_contact",
        "disclaimer_text",
    ]
    return {k: AppSettings.get(k, "") or "" for k in keys}


def _logo_base64(logo_path: str) -> str | None:
    """Liest das Logo und gibt es als Base64-Data-URL zurück."""
    if not logo_path:
        return None
    path = Path(logo_path)
    if not path.exists():
        return None
    suffix = path.suffix.lower().lstrip(".")
    mime = "jpeg" if suffix in ("jpg", "jpeg") else "png"
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/{mime};base64,{data}"


def _pie_chart_svg(macros) -> str:
    """Erstellt ein Makro-Tortendiagramm als SVG-String."""
    labels = ["Protein", "Kohlenhydrate", "Fett"]
    sizes = [macros.protein_g * 4, macros.carbs_g * 4, macros.fat_g * 9]
    colors = ["#2D6A4F", "#95D5B2", "#D8F3DC"]

    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct="%1.0f%%",
        startangle=90,
        textprops={"fontsize": 9},
    )
    ax.axis("equal")
    fig.patch.set_alpha(0)

    buf = io.BytesIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", transparent=True)
    plt.close(fig)
    buf.seek(0)
    return buf.read().decode("utf-8")


def _render_html(plan: MealPlan, upload_folder: str) -> str:
    """Rendert den vollständigen HTML-String für den PDF-Export."""
    s = _settings()
    font = s["font_family"] or "Inter"
    primary = s["primary_color"] or "#2D6A4F"
    secondary = s["secondary_color"] or "#95D5B2"
    coach_name = s["coach_name"] or "MANANI FIT"
    coach_contact = s["coach_contact"] or ""
    disclaimer = s["disclaimer_text"] or ""

    logo_src = _logo_base64(s["logo_path"])
    logo_html = (
        f'<img class="logo" src="{logo_src}" alt="Logo">'
        if logo_src
        else f'<span class="logo-text">{coach_name}</span>'
    )

    macros_a = get_plan_total_macros(plan, "A")
    pie_svg = _pie_chart_svg(macros_a)

    macros_table = f"""
    <table class="macro-table">
      <tr><th>Makronährstoff</th><th>Gramm</th><th>kcal</th><th>%</th></tr>
      <tr>
        <td>Protein</td>
        <td>{macros_a.protein_g:.0f} g</td>
        <td>{macros_a.protein_g * 4:.0f}</td>
        <td>{macros_a.protein_g * 4 / macros_a.kcal * 100:.0f}%</td>
      </tr>
      <tr>
        <td>Kohlenhydrate</td>
        <td>{macros_a.carbs_g:.0f} g</td>
        <td>{macros_a.carbs_g * 4:.0f}</td>
        <td>{macros_a.carbs_g * 4 / macros_a.kcal * 100:.0f}%</td>
      </tr>
      <tr>
        <td>Fett</td>
        <td>{macros_a.fat_g:.0f} g</td>
        <td>{macros_a.fat_g * 9:.0f}</td>
        <td>{macros_a.fat_g * 9 / macros_a.kcal * 100:.0f}%</td>
      </tr>
      <tr class="total-row">
        <td><strong>Gesamt</strong></td>
        <td></td>
        <td><strong>{macros_a.kcal:.0f} kcal</strong></td>
        <td></td>
      </tr>
    </table>
    """

    meals_html = ""
    for slot in plan.meal_slots:
        macros_slot_a = get_slot_macros(slot, "A")
        macros_slot_b = get_slot_macros(slot, "B")

        def _variant_html(variant_letter: str, dish, macros_slot) -> str:
            if dish is None:
                return f"<p><em>Keine Variante {variant_letter} verfügbar.</em></p>"
            ings = [
                i for i in slot.scaled_ingredients if i.variant == variant_letter
            ]
            rows = "".join(
                f"<tr><td>{i.food_item.name}</td>"
                f"<td class='amount'>{i.amount_g:.0f} g</td>"
                f"<td class='kcal-col'>{i.kcal:.0f} kcal</td></tr>"
                for i in ings
            )
            return f"""
            <div class="variant-block">
              <h4>Variante {variant_letter} — {dish.name}</h4>
              <table class="ingredient-table">
                <tr><th>Zutat</th><th>Menge</th><th>kcal</th></tr>
                {rows}
              </table>
              <p class="slot-macros">
                {macros_slot.kcal:.0f} kcal &nbsp;|&nbsp;
                P: {macros_slot.protein_g:.0f} g &nbsp;
                KH: {macros_slot.carbs_g:.0f} g &nbsp;
                F: {macros_slot.fat_g:.0f} g
              </p>
            </div>
            """

        meals_html += f"""
        <div class="meal-section">
          <h3 class="meal-title">{slot.label or f"Mahlzeit {slot.position}"}
            <span class="meal-kcal">{slot.kcal_target:.0f} kcal</span>
          </h3>
          <div class="variants-grid">
            {_variant_html("A", slot.variant_a_dish, macros_slot_a)}
            {_variant_html("B", slot.variant_b_dish, macros_slot_b)}
          </div>
        </div>
        """

    shopping_a = get_shopping_list(plan, "A")
    shopping_b = get_shopping_list(plan, "B")

    def _shopping_rows(items: list[dict]) -> str:
        return "".join(
            f"<tr><td>{i['name']}</td><td class='amount'>{i['amount_g']:.0f} g</td></tr>"
            for i in items
        )

    shopping_html = f"""
    <div class="shopping-section">
      <h2>Einkaufsliste</h2>
      <div class="shopping-grid">
        <div>
          <h3>Variante A</h3>
          <table class="ingredient-table">
            <tr><th>Lebensmittel</th><th>Menge</th></tr>
            {_shopping_rows(shopping_a)}
          </table>
        </div>
        <div>
          <h3>Variante B</h3>
          <table class="ingredient-table">
            <tr><th>Lebensmittel</th><th>Menge</th></tr>
            {_shopping_rows(shopping_b)}
          </table>
        </div>
      </div>
    </div>
    """

    client = plan.client
    created_str = plan.date_created.strftime("%d.%m.%Y")

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <style>
    @import url('{_FONT_URLS.get(font, _FONT_URLS["Inter"])}');

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: '{font}', sans-serif;
      font-size: 10pt;
      color: #1a1a1a;
      line-height: 1.5;
    }}

    .page {{ padding: 20mm 18mm; }}

    @page {{
      size: A4;
      margin: 0;
    }}

    /* Titelseite */
    .cover {{
      background: {primary};
      color: white;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      padding: 20mm 18mm;
      page-break-after: always;
    }}
    .cover .logo {{ max-height: 60px; max-width: 200px; object-fit: contain; }}
    .logo-text {{ font-size: 24pt; font-weight: 700; letter-spacing: 2px; }}
    .cover-main {{ margin-top: 40mm; }}
    .cover h1 {{ font-size: 28pt; font-weight: 700; margin-bottom: 6mm; }}
    .cover .subtitle {{ font-size: 14pt; opacity: 0.85; }}
    .cover .meta {{ font-size: 11pt; margin-top: 8mm; opacity: 0.75; }}
    .cover-macros {{
      background: rgba(255,255,255,0.15);
      border-radius: 8px;
      padding: 6mm 8mm;
      margin-top: 12mm;
      display: flex;
      gap: 12mm;
    }}
    .cover-macros .macro-item {{ text-align: center; }}
    .cover-macros .macro-value {{ font-size: 18pt; font-weight: 700; }}
    .cover-macros .macro-label {{ font-size: 9pt; opacity: 0.8; margin-top: 1mm; }}
    .cover-footer {{ font-size: 9pt; opacity: 0.6; }}

    /* Makro-Diagramm */
    .macro-section {{
      page-break-after: always;
    }}
    h2 {{
      color: {primary};
      font-size: 16pt;
      font-weight: 700;
      margin-bottom: 6mm;
      border-bottom: 2px solid {secondary};
      padding-bottom: 2mm;
    }}
    .macro-overview {{
      display: flex;
      gap: 10mm;
      align-items: flex-start;
      margin-top: 4mm;
    }}
    .macro-overview svg {{ max-width: 160px; flex-shrink: 0; }}
    .macro-table {{
      border-collapse: collapse;
      width: 100%;
      font-size: 10pt;
    }}
    .macro-table th, .macro-table td {{
      padding: 3mm 4mm;
      text-align: left;
      border-bottom: 1px solid #e0e0e0;
    }}
    .macro-table th {{ background: {secondary}; font-weight: 600; color: {primary}; }}
    .total-row td {{ font-weight: 700; border-top: 2px solid {primary}; }}

    /* Mahlzeiten */
    .meal-section {{
      margin-bottom: 8mm;
      page-break-inside: avoid;
    }}
    .meal-title {{
      font-size: 13pt;
      font-weight: 700;
      color: {primary};
      background: {secondary}30;
      padding: 2mm 4mm;
      border-left: 4px solid {primary};
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .meal-kcal {{
      font-size: 10pt;
      font-weight: 400;
      color: #555;
    }}
    .variants-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 4mm;
      margin-top: 2mm;
    }}
    .variant-block {{
      border: 1px solid #e0e0e0;
      border-radius: 4px;
      padding: 3mm;
    }}
    .variant-block h4 {{
      font-size: 10pt;
      font-weight: 600;
      color: {primary};
      margin-bottom: 2mm;
    }}
    .ingredient-table {{
      border-collapse: collapse;
      width: 100%;
      font-size: 9pt;
    }}
    .ingredient-table th, .ingredient-table td {{
      padding: 1.5mm 2mm;
      text-align: left;
      border-bottom: 1px solid #f0f0f0;
    }}
    .ingredient-table th {{ font-weight: 600; color: #555; }}
    .amount, .kcal-col {{ text-align: right; white-space: nowrap; }}
    .slot-macros {{
      font-size: 8.5pt;
      color: #555;
      margin-top: 2mm;
      text-align: right;
    }}

    /* Einkaufsliste */
    .shopping-section {{ page-break-before: always; }}
    .shopping-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8mm;
      margin-top: 4mm;
    }}

    /* Disclaimer */
    .disclaimer {{
      page-break-before: always;
      font-size: 9pt;
      color: #666;
      line-height: 1.6;
    }}
    .disclaimer h2 {{ font-size: 12pt; margin-bottom: 4mm; }}

    /* Footer */
    .footer {{
      position: fixed;
      bottom: 8mm;
      left: 18mm;
      right: 18mm;
      font-size: 8pt;
      color: #aaa;
      display: flex;
      justify-content: space-between;
      border-top: 1px solid #e0e0e0;
      padding-top: 2mm;
    }}
  </style>
</head>
<body>

<!-- Titelseite -->
<div class="cover">
  {logo_html}
  <div class="cover-main">
    <h1>Ernährungsplan</h1>
    <p class="subtitle">{client.name}</p>
    <p class="meta">Erstellt am {created_str} &nbsp;·&nbsp; Ziel: {plan.goal}</p>
    <div class="cover-macros">
      <div class="macro-item">
        <div class="macro-value">{macros_a.kcal:.0f}</div>
        <div class="macro-label">kcal / Tag</div>
      </div>
      <div class="macro-item">
        <div class="macro-value">{macros_a.protein_g:.0f} g</div>
        <div class="macro-label">Protein</div>
      </div>
      <div class="macro-item">
        <div class="macro-value">{macros_a.carbs_g:.0f} g</div>
        <div class="macro-label">Kohlenhydrate</div>
      </div>
      <div class="macro-item">
        <div class="macro-value">{macros_a.fat_g:.0f} g</div>
        <div class="macro-label">Fett</div>
      </div>
    </div>
  </div>
  <div class="cover-footer">{coach_name} &nbsp;·&nbsp; {coach_contact}</div>
</div>

<!-- Makro-Diagramm -->
<div class="page macro-section">
  <h2>Makro-Übersicht</h2>
  <div class="macro-overview">
    {pie_svg}
    {macros_table}
  </div>
</div>

<!-- Mahlzeiten -->
<div class="page">
  <h2>Mahlzeiten</h2>
  {meals_html}
</div>

<!-- Einkaufsliste -->
<div class="page">
  {shopping_html}
</div>

<!-- Disclaimer -->
<div class="page disclaimer">
  <h2>Hinweis</h2>
  <p>{disclaimer}</p>
</div>

<div class="footer">
  <span>{coach_name} · {coach_contact}</span>
  <span>{client.name} · {created_str}</span>
</div>

</body>
</html>"""


def generate_pdf(plan: MealPlan, upload_folder: str) -> bytes:
    """Generiert das PDF eines Plans und gibt die Bytes zurück."""
    from weasyprint import HTML

    html_str = _render_html(plan, upload_folder)
    return HTML(string=html_str).write_pdf()
