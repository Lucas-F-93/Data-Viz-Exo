"""Étape 3 — Nettoyage de ``price.csv`` (branche feature/clean-price).

Applique les décisions prises au diagnostic (docs/etape1_diagnostic_price.md,
section 3) :
  1. Date -> datetime puis re-écrite au format ISO AAAA-MM-JJ ;
  2. Item Code -> texte (clé de jointure) ;
  3. prix < 0.05 RMB/kg (36 lignes, valeur saisie 0.01 / 0.04) = aberrations :
     remplacés par la médiane locale des prix valides du même produit ;
  4. aucune ligne supprimée (55 982 en entrée = 55 982 en sortie) ;
  5. clé (Item Code, Date) unique, tri par produit puis date ;
  6. colonnes exactement celles du contrat d'équipe.

Usage :
    python scripts/etape3_clean_price.py

Sortie : data/clean/price_clean.csv (ignorée par Git, comme la donnée
brute — le pipeline est rejouable).
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "price.csv"
SORTIE = ROOT / "data" / "clean" / "price_clean.csv"

PRIX = "Wholesale Price (RMB/kg)"
SEUIL_PRIX_MIN = 0.05   # RMB/kg : en dessous, prix d'achat impossible
FENETRE = 7             # nb de jours de prix voisins pour la médiane locale
COLONNES = ["Date", "Item Code", PRIX]  # contrat d'équipe (étape 2, §4)


def nettoyer(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne la table nettoyée. Fonction pure : réutilisable par la
    consolidation et testable."""
    df = df.copy()

    # 1. Date -> datetime (0 rejet constaté au diagnostic).
    df["Date"] = pd.to_datetime(df["Date"], errors="raise")

    # 2. Item Code : identifiant, pas une mesure -> texte.
    df["Item Code"] = df["Item Code"].astype(str).str.strip()

    # 3. Prix aberrants : marqués absents puis remplacés par la médiane des
    #    prix valides voisins (même produit, fenêtre centrée), à défaut par
    #    la médiane du produit. On ne supprime pas la ligne : la clé
    #    (Item Code, Date) doit rester jointe aux ventes.
    df = df.sort_values(["Item Code", "Date"]).reset_index(drop=True)
    aberrant = df[PRIX] < SEUIL_PRIX_MIN
    df.loc[aberrant, PRIX] = float("nan")
    locale = df.groupby("Item Code")[PRIX].transform(
        lambda s: s.rolling(FENETRE, center=True, min_periods=1).median())
    produit = df.groupby("Item Code")[PRIX].transform("median")
    df.loc[aberrant, PRIX] = locale[aberrant].fillna(produit[aberrant])
    df[PRIX] = df[PRIX].round(2)

    # 4. Format de sortie ISO (le consolidate joint sur le texte AAAA-MM-JJ).
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")
    return df[COLONNES]


def verifier(brut: pd.DataFrame, propre: pd.DataFrame) -> None:
    """Contrôles de sortie : chaque règle du diagnostic est vérifiée."""
    assert len(brut) == len(propre) == 55_982, "des lignes ont été perdues !"
    assert not propre.duplicated(["Item Code", "Date"]).any(), \
        "doublons (Item Code, Date) en sortie"
    assert propre.isna().sum().sum() == 0, "valeurs manquantes en sortie"
    assert (propre[PRIX] >= SEUIL_PRIX_MIN).all(), "prix aberrants résiduels"
    assert list(propre.columns) == COLONNES, "colonnes hors contrat d'équipe"
    assert propre["Item Code"].map(type).eq(str).all(), "Item Code pas en texte"
    assert propre["Item Code"].nunique() == 251
    corriges = int((brut[PRIX] < SEUIL_PRIX_MIN).sum())
    print(f"Controles OK : 55 982 lignes conservees, cle (Item Code, Date) "
          f"unique, {corriges} prix aberrants corriges, aucun manquant.")


def main() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    brut = pd.read_csv(SRC, dtype={"Item Code": str})
    propre = nettoyer(brut)
    verifier(brut, propre)

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    propre.to_csv(SORTIE, index=False)
    print(f"Table nettoyee ecrite : {SORTIE}")


if __name__ == "__main__":
    main()
