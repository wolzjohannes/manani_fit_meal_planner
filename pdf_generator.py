from __future__ import annotations

import base64
import io
import logging
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")

from models import AppSettings, MealPlan
from planner import (
    DEFAULT_VARIANT_FREEDOM_TEXT,
    get_plan_total_macros,
    get_shopping_list,
    get_slot_macros,
    plan_variant_letters,
)

_LOGGER = logging.getLogger(__name__)

_FONT_URLS = {
    "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap",
    "Montserrat": "https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap",
    "Raleway": "https://fonts.googleapis.com/css2?family=Raleway:wght@400;600;700&display=swap",
    "Open Sans": "https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap",
}


_STATIC_LOGO = Path(__file__).parent / "static" / "uploads" / "manani_fit_logo.png"
_STATIC_HERO_LOGO = Path(__file__).parent / "static" / "uploads" / "become_hp_warrior_logo.png"


def _settings() -> dict[str, str]:
    keys = [
        "primary_color",
        "secondary_color",
        "bg_color",
        "font_family",
        "coach_name",
        "coach_contact",
        "disclaimer_text",
    ]
    result = {k: AppSettings.get(k, "") or "" for k in keys}
    result["variant_freedom_text"] = (
        AppSettings.get("variant_freedom_text", "") or DEFAULT_VARIANT_FREEDOM_TEXT
    )
    return result


def _logo_base64(primary_color: str) -> str | None:
    """Liest das statische MANANI FIT Logo als Base64-Data-URL.

    Cropped den transparenten Außenrand und flattet Alpha-Kanal auf Primary Color,
    um WeasyPrint-Compositing-Probleme mit RGBA-PNGs zu vermeiden.
    """
    if not _STATIC_LOGO.exists():
        _LOGGER.warning("Statisches Logo nicht gefunden: %s", _STATIC_LOGO)
        return None
    from PIL import Image

    img = Image.open(_STATIC_LOGO).convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)

    hex_color = primary_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    bg = Image.new("RGB", img.size, (r, g, b))
    bg.paste(img, mask=img.split()[3])

    buf = io.BytesIO()
    bg.save(buf, format="PNG")
    data = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{data}"


def _hero_logo_base64() -> str | None:
    """Liest das Hero-Logo als Base64-Data-URL."""
    if not _STATIC_HERO_LOGO.exists():
        _LOGGER.warning("Hero-Logo nicht gefunden: %s", _STATIC_HERO_LOGO)
        return None
    data = base64.b64encode(_STATIC_HERO_LOGO.read_bytes()).decode()
    return f"data:image/png;base64,{data}"


def _pie_chart_svg(macros) -> str:
    """Erstellt ein Makro-Tortendiagramm als SVG-String."""
    labels = ["Protein", "Kohlenhydrate", "Fett"]
    sizes = [macros.protein_g * 4, macros.carbs_g * 4, macros.fat_g * 9]
    colors = ["#00D4FF", "#FF6B35", "#FFB000"]

    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct="%1.0f%%",
        startangle=90,
        textprops={"fontsize": 9, "weight": "bold"},
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
    primary = s["primary_color"] or "#00D4FF"
    secondary = s["secondary_color"] or "#FF6B35"
    bg_color = s["bg_color"] or "#FFFFFF"
    coach_name = s["coach_name"] or "MANANI FIT"
    coach_contact = s["coach_contact"] or ""
    disclaimer = s["disclaimer_text"] or ""

    logo_src = _logo_base64(primary)
    hero_logo_src = _hero_logo_base64()
    logo_left = (
        f'<img class="logo" src="{logo_src}" alt="MANANI FIT">'
        if logo_src else ""
    )
    hero_logo_center = (
        f'<img class="hero-logo" src="{hero_logo_src}" alt="Hero">'
        if hero_logo_src else ""
    )
    logo_html = (
        f'<div style="text-align:center; padding-top:12mm; margin-bottom:8mm">'
        f'<img class="logo" src="{logo_src}" alt="MANANI FIT">'
        f'</div>'
        if logo_src else ""
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

    def _variant_html(slot, variant_letter: str, dish, macros_slot) -> str:
        if dish is None:
            return f"<p><em>Keine Variante {variant_letter} verfügbar.</em></p>"
        ings = [i for i in slot.scaled_ingredients if i.variant == variant_letter]
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

    max_variants_per_page = 4
    slot_htmls = []
    for slot in plan.meal_slots:
        variants = list(slot.variants)
        for start in range(0, len(variants), max_variants_per_page):
            chunk = variants[start : start + max_variants_per_page]
            variant_blocks = "".join(
                _variant_html(slot, v.variant, v.dish, get_slot_macros(slot, v.variant))
                for v in chunk
            )
            section_class = (
                "meal-section meal-section--continued" if start > 0 else "meal-section"
            )
            slot_htmls.append(f"""
            <div class="{section_class}">
              <h3 class="meal-title">{slot.label or f"Mahlzeit {slot.position}"}
                <span class="meal-kcal">{slot.kcal_target:.0f} kcal</span>
              </h3>
              <div class="variants-grid">
                {variant_blocks}
              </div>
            </div>
            """)

    freedom_box = (
        f'<p class="variant-freedom">{s["variant_freedom_text"]}</p>'
        if s["variant_freedom_text"] else ""
    )
    meals_pages_html = (
        f'<div class="page"><h2>Mahlzeiten</h2>{freedom_box}{"".join(slot_htmls)}</div>'
    )

    variant_letters = plan_variant_letters(plan)

    def _shopping_rows(items: list[dict]) -> str:
        return "".join(
            f"<tr><td>{i['name']}</td><td class='amount'>{i['amount_g']:.0f} g</td></tr>"
            for i in items
        )

    shopping_cols_per_page = 3
    shopping_sections = []
    for start in range(0, len(variant_letters), shopping_cols_per_page):
        letters = variant_letters[start : start + shopping_cols_per_page]
        cols = "".join(
            f"""<td class="shopping-col">
            <h3>Variante {letter}</h3>
            <table class="ingredient-table">
              <tr><th>Lebensmittel</th><th>Menge</th></tr>
              {_shopping_rows(get_shopping_list(plan, letter))}
            </table>
          </td>"""
            for letter in letters
        )
        shopping_sections.append(
            f'<div class="shopping-section"><h2>Einkaufsliste</h2>'
            f'<table class="shopping-table"><tr>{cols}</tr></table></div>'
        )
    shopping_html = "".join(shopping_sections)

    supplement_html = ""
    if plan.include_supplements and plan.supplements:
        rows = "".join(
            f"<tr>"
            f"<td>{ps.supplement.name}</td>"
            f"<td class='supp-amount'>{ps.amount or '—'} {ps.unit_override or ps.supplement.unit if ps.amount else ''}</td>"
            f"<td class='supp-note'>{ps.note or '—'}</td>"
            f"</tr>"
            for ps in plan.supplements
        )
        supplement_html = f"""
    <div class="supplement-block">
      <h2>Supplements</h2>
      <table class="supplement-table">
        <tr><th>Supplement</th><th>Menge</th><th>Notiz</th></tr>
        {rows}
      </table>
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
      color: #ddd;
      background-color: {bg_color};
      line-height: 1.6;
    }}

    .page {{ page: content; }}

    @page {{
      size: A4;
      margin: 0;
    }}

    @page content {{
      size: A4;
      margin: 20mm 18mm 16mm 18mm;
      background-color: {bg_color};

      @bottom-left {{
        content: "{coach_name} · {coach_contact}";
        width: 50%;
        text-align: left;
        font-size: 8pt;
        color: #999;
        border-top: 1px solid #e0e0e0;
        padding-top: 3mm;
        vertical-align: top;
      }}
      @bottom-right {{
        content: "{client.name} · {created_str}";
        width: 50%;
        text-align: right;
        font-size: 8pt;
        color: #999;
        border-top: 1px solid #e0e0e0;
        padding-top: 3mm;
        vertical-align: top;
      }}
    }}

    /* Titelseite */
    .cover {{
      background: linear-gradient(135deg, {primary}CC, {secondary}CC), url('static/uploads/bg_training.png');
      background-size: cover;
      background-position: center;
      color: white;
      padding: 12mm 18mm 8mm;
      page-break-after: always;
      min-height: 297mm;
    }}
    .cover .logo {{ max-height: 300px; max-width: 300px; object-fit: contain; }}
    .cover .hero-logo {{ max-height: 300px; max-width: 300px; object-fit: contain; }}
    .logo-text {{ font-size: 28pt; font-weight: 700; letter-spacing: 3px; }}
    .cover-main {{ margin-top: 15mm; }}
    .cover h1 {{ font-size: 32pt; font-weight: 700; margin-bottom: 8mm; }}
    .cover .subtitle {{ font-size: 16pt; opacity: 0.9; font-weight: 500; }}
    .cover .meta {{ font-size: 11pt; margin-top: 8mm; opacity: 0.8; }}
    .cover-macros {{
      background: rgba(255,255,255,0.12);
      border-radius: 12px;
      padding: 8mm 10mm;
      margin-top: 8mm;
      display: flex;
      border: 1px solid rgba(255,255,255,0.2);
    }}
    .cover-macros .macro-item {{ text-align: center; display: inline-block; margin-right: 14mm; }}
    .cover-macros .macro-item:last-child {{ margin-right: 0; }}
    .cover-macros .macro-value {{ font-size: 20pt; font-weight: 700; }}
    .cover-macros .macro-label {{ font-size: 9pt; opacity: 0.85; margin-top: 2mm; }}

    /* Makro-Diagramm */
    .macro-section {{
      page-break-after: always;
    }}
    h2 {{
      color: {primary};
      font-size: 18pt;
      font-weight: 700;
      margin-bottom: 8mm;
      border-bottom: 3px solid {secondary};
      padding-bottom: 3mm;
      display: inline-block;
    }}
    .macro-overview {{ margin-top: 30mm; }}
    .macro-overview svg {{ max-width: 140px; }}
    .macro-table {{
      border-collapse: collapse;
      width: 100%;
      font-size: 10pt;
    }}
    .macro-table th, .macro-table td {{
      padding: 4mm 5mm;
      text-align: left;
      border-bottom: 1px solid rgba(255,255,255,0.2);
    }}
    .macro-table th {{ background: rgba(255,255,255,0.15); font-weight: 700; color: white; }}
    .macro-table td {{ color: white; }}
    .total-row td {{ font-weight: 700; background: rgba(255,255,255,0.05); border-top: 2px solid {primary}; color: white; }}

    .macro-explanation {{
      margin-top: 10mm;
      font-size: 9pt;
      color: #ccc;
      line-height: 1.7;
    }}
    .macro-explanation h3 {{
      color: {primary};
      font-size: 12pt;
      font-weight: 700;
      margin-bottom: 3mm;
    }}
    .macro-explanation ul {{ margin: 2mm 0 0 5mm; }}

    .variant-freedom {{
      background: {secondary}22;
      border-left: 4px solid {primary};
      padding: 4mm 5mm;
      margin-bottom: 6mm;
      font-size: 9.5pt;
      color: white;
      border-radius: 4px;
      line-height: 1.6;
    }}

    /* Mahlzeiten */
    .meal-section {{
      margin-bottom: 10mm;
      page-break-inside: avoid;
    }}
    .meal-section--continued {{ page-break-before: always; }}
    .meal-title {{
      font-size: 13pt;
      font-weight: 700;
      color: white;
      background: linear-gradient(90deg, {primary}, {secondary});
      padding: 3mm 5mm;
      border-radius: 4px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .meal-kcal {{
      font-size: 10pt;
      font-weight: 500;
      opacity: 0.9;
    }}
    .variants-grid {{
      margin-top: 3mm;
      font-size: 0;
    }}
    .variants-grid .variant-block {{
      display: inline-block;
      width: 48%;
      vertical-align: top;
      font-size: 10pt;
      margin: 0 4% 4mm 0;
    }}
    .variants-grid .variant-block:nth-child(2n) {{
      margin-right: 0;
    }}
    .variant-block {{
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 6px;
      padding: 4mm;
      background: rgba(255,255,255,0.08);
    }}
    .variant-block h4 {{
      font-size: 11pt;
      font-weight: 700;
      color: {primary};
      margin-bottom: 2mm;
    }}
    .ingredient-table {{
      border-collapse: collapse;
      width: 100%;
      font-size: 9pt;
    }}
    .ingredient-table th, .ingredient-table td {{
      padding: 2mm 3mm;
      text-align: left;
      border-bottom: 1px solid rgba(255,255,255,0.1);
    }}
    .ingredient-table th {{ font-weight: 700; color: #ddd; background: rgba(255,255,255,0.1); }}
    .shopping-col .ingredient-table th {{ color: white; background: linear-gradient(90deg, {primary}, {secondary}); }}
    .shopping-col .ingredient-table td {{ color: #ddd; }}
    .amount, .kcal-col {{ text-align: right; white-space: nowrap; }}
    .slot-macros {{
      font-size: 9pt;
      color: {primary};
      margin-top: 2mm;
      text-align: right;
      font-weight: 500;
    }}

    /* Einkaufsliste */
    .shopping-section {{ page-break-before: always; }}
    .shopping-table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 6mm;
      table-layout: fixed;
    }}
    .shopping-table td {{
      vertical-align: top;
      padding-right: 10mm;
    }}
    .shopping-table td:last-child {{
      padding-right: 0;
    }}
    .shopping-col h3 {{
      font-size: 12pt;
      font-weight: 700;
      color: {primary};
      margin-bottom: 3mm;
    }}

    /* Supplements */
    .supplement-block {{ margin-bottom: 10mm; }}
    .supplement-table {{
      border-collapse: collapse;
      width: 100%;
      max-width: 120mm;
      font-size: 10pt;
    }}
    .supplement-table th, .supplement-table td {{
      padding: 3mm 4mm;
      text-align: left;
      border-bottom: 1px solid rgba(255,255,255,0.15);
    }}
    .supplement-table th {{ background: rgba(255,255,255,0.12); font-weight:700; color:white; }}
    .supplement-table td {{ color:#ddd; }}
    .supp-amount {{ font-weight: 600; }}
    .supp-note {{ color:#aaa; font-style:italic; }}

    /* Disclaimer */
    .disclaimer {{
      page-break-before: always;
      font-size: 9pt;
      color: #ccc;
      line-height: 1.7;
    }}
    .disclaimer h2 {{ font-size: 14pt; margin-bottom: 6mm; }}
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
</div>

<!-- Makro-Diagramm -->
<div class="page macro-section">
  <h2>Makro-Übersicht</h2>
  <div style="text-align:center; margin-bottom:8mm">{pie_svg}</div>
  {macros_table}
  <div class="macro-explanation">
    <h3>Was bedeuten Kalorien und Makros?</h3>
    <p>
      <strong>Kalorien (kcal)</strong> sind die Energie, die dein Körper aus der
      Nahrung gewinnt. Über den Tag bestimmt die Kalorienbilanz, ob du Gewicht
      auf- oder abbaust. <strong>Makronährstoffe</strong> („Makros") sind die drei
      energieliefernden Bausteine deiner Ernährung:
    </p>
    <ul>
      <li><strong>Protein</strong> (4 kcal/g) — Baustoff für Muskeln, sättigt stark.</li>
      <li><strong>Kohlenhydrate</strong> (4 kcal/g) — Hauptenergiequelle für Training und Alltag.</li>
      <li><strong>Fett</strong> (9 kcal/g) — wichtig für Hormone und Vitaminaufnahme.</li>
    </ul>
    <p>
      Das Tortendiagramm zeigt, wie sich deine Tageskalorien auf diese drei Makros
      verteilen. Wenn du dich an die angegebenen Gramm-Mengen hältst, erreichst du
      automatisch dein Kalorien- und Makroziel.
    </p>
  </div>
</div>

<!-- Mahlzeiten -->
{meals_pages_html}

<!-- Einkaufsliste -->
<div class="page">
  {shopping_html}
</div>

<!-- Letzte Seite: Supplements + Hinweis -->
<div class="page disclaimer">
  {supplement_html}
  <h2>Hinweis</h2>
  <p>{disclaimer}</p>
</div>

</body>
</html>"""


def generate_pdf(plan: MealPlan, upload_folder: str) -> bytes:
    """Generiert das PDF eines Plans und gibt die Bytes zurück."""
    from weasyprint import HTML

    html_str = _render_html(plan, upload_folder)
    return HTML(string=html_str, base_url=str(Path(__file__).parent)).write_pdf()
