"""Étape 2 — Génération de l'image du schéma en étoile.

Usage :
    python scripts/etape2_star_schema.py

Sortie : docs/img/etape2_star_schema.png (référencée par le README et par
docs/etape2_modele_donnees.md).

Représentation volontairement minimale : nom des tables, leur rôle (table de
faits / dimension) et les clés primaires / étrangères uniquement. Le détail
complet des colonnes reste dans docs/etape2_modele_donnees.md.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SORTIE = ROOT / "docs" / "img" / "etape2_star_schema.png"

COULEUR_FAITS = "#f2c14e"   # jaune : table de faits
COULEUR_DIM = "#4c78a8"     # bleu : dimensions
COULEUR_TEXTE = "#1f2933"


def boite(ax, x, y, w, h, titre, role, lignes, couleur, epaisseur=2):
    """Dessine une table : en-tête (nom + rôle) puis une ligne par clé."""
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor="white",
                               edgecolor=couleur, linewidth=epaisseur))
    ax.add_patch(plt.Rectangle((x, y + h - 0.62), w, 0.62, facecolor=couleur,
                               edgecolor=couleur, linewidth=epaisseur))
    ax.text(x + w / 2, y + h - 0.21, titre, ha="center", va="center",
            fontsize=12.5, fontweight="bold", color="white")
    ax.text(x + w / 2, y + h - 0.46, role, ha="center", va="center",
            fontsize=9, style="italic", color="white")
    for i, ligne in enumerate(lignes):
        ax.text(x + 0.18, y + h - 0.85 - i * 0.32, ligne, ha="left",
                va="center", fontsize=10, family="monospace",
                color=COULEUR_TEXTE)


def main() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.set_xlim(0, 12)
    ax.set_ylim(1.9, 6.8)
    ax.axis("off")

    titre = ax.text(6, 6.45, "Schéma en étoile", ha="center", va="center",
                    fontsize=17, fontweight="bold", color=COULEUR_TEXTE)

    # Table de faits au centre, dimensions autour (liaisons N..1).
    boite(ax, 4.6, 2.35, 3.2, 1.65, "FACT_SALES", "Table de faits", [
        "FK  item_code",
        "FK  date",
    ], COULEUR_FAITS, epaisseur=3)

    boite(ax, 0.7, 2.60, 2.9, 1.15, "DIM_PRODUCT", "Dimension", [
        "PK  item_code",
    ], COULEUR_DIM)

    boite(ax, 8.4, 2.60, 2.9, 1.15, "DIM_DATE", "Dimension", [
        "PK  date",
    ], COULEUR_DIM)

    # Liaisons faits -> dimensions (N faits pour 1 dimension).
    for x1, x2 in [(4.6, 3.6), (7.8, 8.4)]:
        ax.annotate("", xy=(x2, 3.175), xytext=(x1, 3.175),
                    arrowprops=dict(arrowstyle="-", color="#6b7280", lw=2))
    ax.text(4.1, 3.33, "N..1", fontsize=9, color="#6b7280", ha="center")
    ax.text(8.1, 3.33, "N..1", fontsize=9, color="#6b7280", ha="center")

    # Contrôle anti-superposition : le titre ne doit chevaucher aucune table.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    bb_titre = titre.get_window_extent(renderer)
    for patch in ax.patches:
        if bb_titre.overlaps(patch.get_window_extent(renderer)):
            raise AssertionError("le titre chevauche une table !")

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(SORTIE, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"Image enregistrée : {SORTIE}")


if __name__ == "__main__":
    main()
