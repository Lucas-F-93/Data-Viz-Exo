"""Étape 3 — Nettoyage de ``product.csv`` (branche feature/clean-product).

Applique les décisions prises au diagnostic (docs/etape1_diagnostic_product.md,
section 3) :
  1. espaces insécables (\\xa0) de Category Name remplacés par des espaces ;
  2. Item Name nettoyé (trim) ;
  3. Item Code et Category Code convertis en texte (clés de jointure) ;
  4. aucune ligne supprimée (251 en entrée = 251 en sortie) ;
  5. doublons de noms (ex: 2 Broccoli) conservés : Item Code reste la clé.

Usage :
    python scripts/etape3_clean_product.py

Sortie : data/clean/product_clean.csv (ignorée par Git, comme la donnée
brute — le pipeline est rejouable).
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "product.csv"
SORTIE = ROOT / "data" / "clean" / "product_clean.csv"


def nettoyer(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne la table nettoyée. Fonction pure : réutilisable par la
    consolidation et testable."""
    df = df.copy()

    # 1. Le piège du diagnostic : espace insécable dans 'Flower/Leaf\xa0Vegetables'
    #    (100 lignes) -> la catégorie apparaitrait en double dans le dashboard.
    df["Category Name"] = (df["Category Name"]
                           .str.replace("\xa0", " ", regex=False)
                           .str.strip())
    df["Category Name"] = pd.Categorical(df["Category Name"])

    # 2. Espaces parasites des libellés produits (4 lignes au diagnostic).
    df["Item Name"] = df["Item Name"].str.strip()

    # 3. Identifiants -> texte (on ne calcule pas dessus).
    df["Item Code"] = df["Item Code"].astype(str)
    df["Category Code"] = df["Category Code"].astype(str)
    return df


def verifier(brut: pd.DataFrame, propre: pd.DataFrame) -> None:
    """Contrôles de sortie : chaque règle du diagnostic est vérifiée."""
    assert len(brut) == len(propre) == 251, "des lignes ont été perdues !"
    assert propre["Item Code"].is_unique, "Item Code n'est plus une clé unique"
    assert propre["Category Name"].str.contains("\xa0").sum() == 0, \
        "il reste des espaces insécables"
    assert propre["Category Name"].nunique() == 6, "catégories en double"
    assert not (propre["Item Name"] != propre["Item Name"].str.strip()).any(), \
        "espaces parasites résiduels"
    assert propre.isna().sum().sum() == 0, "valeurs manquantes en sortie"
    print("Controles OK : 251 lignes conservees, cles uniques, 6 categories "
          "apres normalisation, plus d'espace inseparable.")


def main() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    brut = pd.read_csv(SRC)
    propre = nettoyer(brut)
    verifier(brut, propre)

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    propre.to_csv(SORTIE, index=False)
    print(f"Table nettoyee ecrite : {SORTIE}")


if __name__ == "__main__":
    main()
