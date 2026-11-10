"""Étape 1 — Diagnostic de la table brute ``product.csv``.

Responsable : Lucas (branche feature/clean-product).

Objectif : inspecter le référentiel produits et chiffrer tout ce qui devra
être changé/nettoyé avant la consolidation. Chaque constat est accompagné
d'une décision justifiée par une logique métier (règle d'or du cours).

Usage :
    python scripts/etape1_diagnostic_product.py

Sorties :
    - rapport complet dans la console
    - graphique docs/img/etape1_product_categories.png
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # rendu sans fenêtre (rejouable en CI)
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "product.csv"
TRANSACTION = ROOT / "data" / "raw" / "transaction.csv"
IMG_DIR = ROOT / "docs" / "img"


def section(titre: str) -> None:
    print(f"\n{'=' * 70}\n{titre}\n{'=' * 70}")


def main() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")  # accents dans la console Windows

    df = pd.read_csv(SRC)

    section("1. VUE D'ENSEMBLE")
    print(f"Lignes × colonnes : {df.shape[0]} × {df.shape[1]}")
    print("Colonnes et types détectés par Pandas :")
    print(df.dtypes.to_string())
    print(f"Valeurs manquantes (total) : {int(df.isna().sum().sum())}")
    print(f"Doublons complets de lignes : {int(df.duplicated().sum())}")

    section("2. ITEM CODE — CLÉ PRIMAIRE ?")
    print(f"Codes distincts : {df['Item Code'].nunique()} pour {len(df)} lignes")
    print(f"Codes dupliqués : {int(df['Item Code'].duplicated().sum())}")
    print(f"Type détecté : {df['Item Code'].dtype} (lu comme un nombre)")
    print(f"Longueur des codes : {sorted(int(n) for n in df['Item Code'].astype(str).str.len().unique())}")

    section("3. ITEM NAME — LIBELLÉS PRODUITS")
    noms = df["Item Name"]
    print(f"Noms distincts : {noms.nunique()} pour 251 produits")
    avec_espaces = df[noms != noms.str.strip()]
    print(f"Noms avec espaces parasites (début/fin) : {len(avec_espaces)}")
    print(avec_espaces[["Item Code", "Item Name"]].to_string(index=False))
    doublons = df[noms.duplicated(keep=False)].sort_values("Item Name")
    print(f"\nNoms portés par plusieurs codes différents : {doublons['Item Name'].nunique()}")
    print(doublons[["Item Code", "Item Name", "Category Name"]].to_string(index=False))

    section("4. CATÉGORIES — LE PIÈGE DES ESPACES INSÉCABLES")
    print("Valeurs exactes (repr) de Category Name :")
    for nom in sorted(df["Category Name"].unique()):
        print(f"  {nom!r}")
    nbsp = df["Category Name"].str.contains("\xa0")
    print(f"\nLignes avec espace insécable (\\xa0) : {int(nbsp.sum())} "
          f"({df.loc[nbsp, 'Category Name'].iloc[0]!r})")
    print("Mapping Category Code <-> Category Name :")
    croise = df.groupby("Category Name")["Category Code"].nunique()
    print(f"  noms associés à plusieurs codes : {int((croise > 1).sum())}")
    croise2 = df.groupby("Category Code")["Category Name"].nunique()
    print(f"  codes associés à plusieurs noms : {int((croise2 > 1).sum())}")
    print(f"Codes de catégorie distincts : {df['Category Code'].nunique()}")

    section("5. INTÉGRITÉ AVEC LES VENTES (transaction.csv)")
    if TRANSACTION.exists():
        ventes = pd.read_csv(TRANSACTION, usecols=["Item Code"])
        vendus = set(ventes["Item Code"].unique())
        connus = set(df["Item Code"])
        print(f"Produits jamais vendus sur 3 ans : {len(connus - vendus)}")
        print(f"Ventes référençant un produit inconnu : {len(vendus - connus)}")
    else:
        print("transaction.csv absent de data/raw/ : contrôle ignoré.")

    # ----- Graphique pour le README (rendu : « avec des images ») ----------
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    compte = (df.assign(Cat=df["Category Name"].str.replace("\xa0", " "))
                .groupby("Cat")["Item Code"].nunique()
                .sort_values(ascending=True))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    bars = ax.barh(compte.index, compte.values, color="#4c78a8")
    ax.bar_label(bars, padding=3)
    ax.set_title("product.csv — 251 produits répartis en 6 catégories\n"
                 "(après normalisation de l'espace insécable de « Flower/Leaf Vegetables »)")
    ax.set_xlabel("Nombre de produits")
    ax.set_xlim(0, 115)
    sortie = IMG_DIR / "etape1_product_categories.png"
    fig.savefig(sortie, dpi=150, bbox_inches="tight")
    print(f"\nGraphique enregistré : {sortie}")


if __name__ == "__main__":
    main()
