"""Étape 2 — Génération de l'image du schéma en étoile (les 4 CSV).

Usage :
    python scripts/etape2_star_schema.py

Sortie : docs/img/etape2_star_schema.png (référencée par le README et par
docs/etape2_modele_donnees.md).

Représentation : transaction.csv = table de faits centrale, les 3 autres
CSV = dimensions. Clés primaires / étrangères uniquement, rôle de chaque
table écrit dans l'en-tête.
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


def liaison(ax, x1, y1, x2, y2, etiquette=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-", color="#6b7280", lw=2))
    if etiquette:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.14, etiquette,
                fontsize=9, color="#6b7280", ha="center", va="bottom")


def main() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.set_xlim(0, 12.7)
    ax.set_ylim(1.9, 6.8)
    ax.axis("off")

    titre = ax.text(6.35, 6.55, "Schéma en étoile", ha="center", va="center",
                    fontsize=17, fontweight="bold", color=COULEUR_TEXTE)

    # ---- Table de faits au centre ------------------------------------------
    boite(ax, 4.7, 3.15, 3.4, 1.75, "transaction.csv", "Table de faits", [
        "FK  Item Code",
        "FK  Date",
    ], COULEUR_FAITS, epaisseur=3)

    # ---- Dimensions autour ---------------------------------------------------
    boite(ax, 0.5, 3.45, 3.0, 1.15, "product.csv", "Dimension", [
        "PK  Item Code",
    ], COULEUR_DIM)

    boite(ax, 9.2, 4.55, 3.0, 1.15, "price.csv", "Dimension", [
        "PK  Item Code",
        "PK  Date",
    ], COULEUR_DIM)

    boite(ax, 9.2, 2.45, 3.0, 1.15, "loss_rate.csv", "Dimension", [
        "PK  Item Code",
    ], COULEUR_DIM)

    # ---- Liaisons faits -> dimensions ---------------------------------------
    liaison(ax, 3.5, 4.02, 4.7, 4.02, "Item Code")
    liaison(ax, 8.1, 4.72, 9.2, 5.12, "Item Code + Date")
    liaison(ax, 8.1, 3.55, 9.2, 3.02, "Item Code")

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
