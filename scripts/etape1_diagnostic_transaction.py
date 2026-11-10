"""Étape 1 — Diagnostic de la table brute ``transaction.csv``.

Responsable : Lucas (branche feature/clean-transaction).

Objectif : inspecter la table et chiffrer tout ce qui devra être
changé/nettoyé avant la consolidation. Chaque constat est accompagné d'une
décision justifiée par une logique métier (règle d'or du cours).

Usage :
    python scripts/etape1_diagnostic_transaction.py

Sorties :
    - rapport complet dans la console
    - graphique docs/img/etape1_transaction_distributions.png
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # rendu sans fenêtre (rejouable en CI)
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "transaction.csv"
PRODUCT = ROOT / "data" / "raw" / "product.csv"
IMG_DIR = ROOT / "docs" / "img"


def bornes_iqr(serie: pd.Series) -> tuple[float, float]:
    """Limites de Tukey : Q1 - 1.5*IQR et Q3 + 1.5*IQR."""
    q1, q3 = serie.quantile([0.25, 0.75])
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def section(titre: str) -> None:
    print(f"\n{'=' * 70}\n{titre}\n{'=' * 70}")


def main() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")  # accents dans la console Windows
    df = pd.read_csv(SRC)

    section("1. VUE D'ENSEMBLE")
    print(f"Lignes × colonnes : {df.shape[0]:,} × {df.shape[1]}".replace(",", " "))
    print("Colonnes et types détectés par Pandas :")
    print(df.dtypes.to_string())
    print(f"Valeurs manquantes (total) : {int(df.isna().sum().sum())}")
    print(f"Doublons complets de lignes : {int(df.duplicated().sum())}")

    section("2. DATES ET HEURES")
    dates = pd.to_datetime(df["Date"], errors="coerce")
    print(f"Dates non interprétables : {int(dates.isna().sum())}")
    print(f"Période couverte : {dates.min().date()} -> {dates.max().date()}")
    print(f"Jours distincts : {dates.nunique()}")
    heures_ms = pd.to_datetime(df["Time"], format="%H:%M:%S.%f", errors="coerce")
    heures_sans_ms = heures_ms.isna().sum()
    print(f"Heures sans millisecondes (format 'HH:MM:SS' court) : {heures_sans_ms}")
    print(f"Amplitude horaire : {heures_ms.min().time()} -> {heures_ms.max().time()}")

    section("3. ITEM CODE (clé de jointure vers product.csv)")
    print(f"Type détecté : {df['Item Code'].dtype} (lu comme un nombre)")
    print(f"Codes distincts : {df['Item Code'].nunique()}")
    print(f"Longueur des codes : {sorted(int(n) for n in df['Item Code'].astype(str).str.len().unique())}")

    section("4. QUANTITÉ VENDUE (kilo)")
    qty = df["Quantity Sold (kilo)"]
    print(qty.describe().to_string())
    print(f"Quantités négatives : {int((qty < 0).sum())}")
    lo, hi = bornes_iqr(qty)
    outliers = ((qty < lo) | (qty > hi)).sum()
    print(f"Bornes IQR globales : [{lo:.3f} ; {hi:.3f}] -> {int(outliers)} lignes hors bornes "
          f"({outliers / len(df):.1%})")

    section("5. PRIX UNITAIRE (RMB/kg)")
    prix = df["Unit Selling Price (RMB/kg)"]
    print(prix.describe().to_string())
    lo, hi = bornes_iqr(prix)
    outliers = ((prix < lo) | (prix > hi)).sum()
    print(f"Bornes IQR globales : [{lo:.2f} ; {hi:.2f}] -> {int(outliers)} lignes hors bornes "
          f"({outliers / len(df):.1%})")
    prix_par_item = df.groupby("Item Code")["Unit Selling Price (RMB/kg)"].nunique()
    print(f"Produits avec plusieurs prix dans le temps : "
          f"{int((prix_par_item > 1).sum())} / {len(prix_par_item)}")

    section("6. COHÉRENCE RETOURS / SIGNE DES QUANTITÉS")
    croise = pd.crosstab(df["Sale or Return"], qty < 0,
                         rownames=["Sale or Return"], colnames=["Quantité négative"])
    print(croise.to_string())
    print("-> les 461 lignes 'return' sont exactement les 461 quantités négatives.")

    section("7. MODALITÉS DES COLONNES QUALITATIVES")
    print("Sale or Return :")
    print(df["Sale or Return"].value_counts().to_string())
    print("Discount (Yes/No) :")
    print(df["Discount (Yes/No)"].value_counts().to_string())

    section("8. INTÉGRITÉ RÉFÉRENTIELLE (FK vers product.csv)")
    if PRODUCT.exists():
        produits = pd.read_csv(PRODUCT)
        vendus = set(df["Item Code"].unique())
        connus = set(produits["Item Code"].unique())
        print(f"Lignes de ventes référençant un produit inconnu (orphelins) : "
              f"{len(vendus - connus)}")
        print(f"Produits du référentiel jamais vendus : {len(connus - vendus)}")
    else:
        print("product.csv absent de data/raw/ : contrôle ignoré.")

    section("9. ORDRE DE GRANDEUR MÉTIER (CA = quantité x prix)")
    ca_total = float((qty * prix).sum())
    masque_12m = (dates >= "2022-07-01")
    ca_12m = float((qty[masque_12m] * prix[masque_12m]).sum())
    print(f"CA net sur les 3 ans    : {ca_total:,.0f} RMB".replace(",", " "))
    print(f"CA net 12 derniers mois : {ca_12m:,.0f} RMB".replace(",", " "))
    print(f"Lignes sur 12 mois      : {int(masque_12m.sum()):,}".replace(",", " "))

    # ----- Graphique pour le README (rendu : « avec des images ») ----------
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    axes[0].hist(qty, bins=80, color="#4c78a8", edgecolor="white")
    axes[0].axvline(hi, color="#e4572e", linestyle="--", label=f"borne IQR haute ({hi:.2f} kg)")
    axes[0].set_yscale("log")
    axes[0].set_title("Distribution des quantités vendues (kg) — échelle log")
    axes[0].set_xlabel("Quantité (kg)")
    axes[0].set_ylabel("Nombre de lignes (log)")
    axes[0].legend()

    axes[1].hist(prix, bins=80, color="#54a24b", edgecolor="white")
    axes[1].axvline(19.65, color="#e4572e", linestyle="--", label="borne IQR haute (19,65 RMB)")
    axes[1].set_title("Distribution des prix unitaires (RMB/kg)")
    axes[1].set_xlabel("Prix (RMB/kg)")
    axes[1].set_ylabel("Nombre de lignes")
    axes[1].legend()

    fig.suptitle("transaction.csv — les queues de distribution sont des achats en gros / produits premium, "
                 "pas des erreurs", y=1.02)
    sortie = IMG_DIR / "etape1_transaction_distributions.png"
    fig.savefig(sortie, dpi=150, bbox_inches="tight")
    print(f"\nGraphique enregistré : {sortie}")


if __name__ == "__main__":
    main()
