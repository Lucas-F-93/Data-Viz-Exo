"""Étape 3 — Nettoyage de ``transaction.csv`` (branche feature/clean-transaction).

Applique les décisions prises au diagnostic (docs/etape1_diagnostic_transaction.md,
section 3) :
  1. Date -> datetime ;
  2. Time parsée en un format unique (132 lignes sans millisecondes) ;
  3. Item Code -> texte (clé de jointure) ;
  4. retours conservés + indicateur is_return ;
  5. aucune ligne supprimée (878 503 en entrée = 878 503 en sortie) ;
  6. colonnes dérivées : sales_amount (CA de la ligne) et hour.

Usage :
    python scripts/etape3_clean_transaction.py

Sortie : data/clean/transaction_clean.csv (ignorée par Git, comme la donnée
brute — le pipeline est rejouable).
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "transaction.csv"
SORTIE = ROOT / "data" / "clean" / "transaction_clean.csv"


def nettoyer(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne la table nettoyée. Fonction pure : réutilisable par la
    consolidation et testable."""
    df = df.copy()

    # 1. Dates : texte ISO -> datetime (0 rejet constaté au diagnostic).
    df["Date"] = pd.to_datetime(df["Date"], errors="raise")

    # 2. Heures : 2 formats coexistent ('HH:MM:SS.mmm' et 'HH:MM:SS').
    #    format='mixed' gère les deux ; on re-rend un format unique.
    heures = pd.to_datetime(df["Time"], format="mixed", errors="raise")
    assert heures.isna().sum() == 0, "heures non parsées détectées"
    df["Time"] = heures.dt.strftime("%H:%M:%S.%f")
    df["hour"] = heures.dt.hour

    # 3. Item Code : identifiant, pas une mesure -> texte.
    df["Item Code"] = df["Item Code"].astype(str)

    # 4. Retours : conservés, marqués par un indicateur (règle d'or métier :
    #    la quantité vendue « sans les retours » s'obtient par filtrage).
    df["is_return"] = (df["Sale or Return"] == "return").astype(int)

    # 5/6. CA de la ligne (signé : négatif pour un retour) + modalités propres.
    df["sales_amount"] = (df["Quantity Sold (kilo)"]
                          * df["Unit Selling Price (RMB/kg)"]).round(2)
    df["Sale or Return"] = pd.Categorical(df["Sale or Return"],
                                          categories=["sale", "return"])
    df["Discount (Yes/No)"] = pd.Categorical(df["Discount (Yes/No)"],
                                             categories=["No", "Yes"])
    return df


def verifier(brut: pd.DataFrame, propre: pd.DataFrame) -> None:
    """Contrôles de sortie : chaque règle du diagnostic est vérifiée."""
    assert len(brut) == len(propre) == 878_503, "des lignes ont été perdues !"
    assert propre.isna().sum().sum() == 0, "valeurs manquantes en sortie"
    assert (propre["is_return"] == 1).sum() == 461, "retours mal marqués"
    assert ((propre["is_return"] == 1)
            == (propre["Quantity Sold (kilo)"] < 0)).all(), \
        "is_return et quantités négatives divergent"
    assert propre["Item Code"].map(len).eq(15).all(), "Item Code altéré"
    print("Controles OK : 878 503 lignes conservees, 461 retours marques, "
          "0 valeur manquante, cles intactes.")


def main() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    brut = pd.read_csv(SRC)
    propre = nettoyer(brut)
    verifier(brut, propre)

    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    propre.to_csv(SORTIE, index=False)
    ca = propre["sales_amount"].sum()
    print(f"CA net sur 3 ans : {ca:,.0f} RMB".replace(",", " "))
    print(f"Table nettoyee ecrite : {SORTIE}")


if __name__ == "__main__":
    main()
