"""Étape 2 — Génération de l'image du schéma en étoile.

Usage :
    python scripts/etape2_star_schema.py

Sortie : docs/img/etape2_star_schema.png (référencée par le README et par
docs/etape2_modele_donnees.md).
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SORTIE = ROOT / "docs" / "img" / "etape2_star_schema.png"

COULEUR_FAITS = "#f2c14e"      # jaune : mesures
COULEUR_DIM = "#4c78a8"        # bleu : dimensions
COULEUR_TITRE = "#1f2933"


def boite(ax, x, y, w, h, titre, lignes, couleur):
    """Dessine une table (en-tête + une ligne par champ)."""
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor="white",
                                edgecolor=couleur, linewidth=2))
    ax.add_patch(plt.Rectangle((x, y + h - 0.34), w, 0.34, facecolor=couleur,
                                edgecolor=couleur, linewidth=2))
    ax.text(x + w / 2, y + h - 0.17, titre, ha="center", va="center",
            fontsize=12, fontweight="bold", color="white")
    for i, ligne in enumerate(lignes):
        ax.text(x + 0.15, y + h - 0.62 - i * 0.30, ligne, ha="left",
                va="center", fontsize=9.5,
                family="monospace", color=COULEUR_TITRE)


def fleche(ax, x1, y1, x2, y2, etiquette=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-", color="#6b7280", lw=2))
    if etiquette:
        ax.text((x1 + x2) / 2 + 0.03, (y1 + y2) / 2, etiquette,
                fontsize=9, color="#6b7280", ha="left", va="center")


def main() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    fig, ax = plt.subplots(figsize=(13, 7.5))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 7.5)
    ax.axis("off")

    # ---- Table de faits au centre -----------------------------------------
    boite(ax, 4.55, 2.45, 3.9, 4.35, "FACT_SALES  (faits)", [
        "PK  (ligne de caisse)",
        "FK  item_code          → DIM_PRODUCT",
        "FK  date               → DIM_DATE",
        "    hour",
        "M   quantity_kilo  (signée)",
        "M   unit_selling_price",
        "M   sales_amount = qté × prix",
        "F   is_return / is_discount",
        "M   wholesale_price*  (marge)",
    ], COULEUR_FAITS)

    # ---- Dimensions --------------------------------------------------------
    boite(ax, 0.6, 4.6, 3.3, 2.75, "DIM_PRODUCT", [
        "PK  item_code",
        "    item_name",
        "    category_code",
        "    category_name",
        "    loss_rate_pct",
    ], COULEUR_DIM)

    boite(ax, 0.6, 0.6, 3.3, 3.0, "DIM_DATE", [
        "PK  date",
        "    year / quarter / month",
        "    month_name",
        "    day / day_name / dow",
        "    week_of_year",
        "F   is_last_12m (07/22→06/23)",
    ], COULEUR_DIM)

    boite(ax, 9.1, 4.6, 3.3, 2.75, "DIM_CATEGORY*", [
        "PK  category_code",
        "    category_name",
        "(variante « flocon » :",
        " sortie de la catégorie",
        " si attributs riches)",
    ], "#9aa5b1")

    # ---- Liaisons ----------------------------------------------------------
    fleche(ax, 3.9, 5.95, 4.55, 5.60, "N..1")
    fleche(ax, 3.9, 2.10, 4.55, 3.10, "N..1")
    ax.annotate("", xy=(10.75, 4.60), xytext=(10.75, 5.30),
                arrowprops=dict(arrowstyle="-", color="#9aa5b1", lw=1.5,
                                linestyle="dashed"))

    ax.text(6.5, 7.15, "Schéma en étoile (couche Gold) — ventes de produits frais",
            ha="center", fontsize=15, fontweight="bold", color=COULEUR_TITRE)
    ax.text(6.5, 0.35, "M = mesure   F = filtre / indicateur   *wholesale_price : rattaché à la vente via (item_code, date) — "
                       "218/246 produits changent de prix dans le temps",
            ha="center", fontsize=9, color="#6b7280")

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(SORTIE, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"Image enregistrée : {SORTIE}")


if __name__ == "__main__":
    main()
