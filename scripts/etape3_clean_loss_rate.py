"""Étape 3 — Nettoyage de ``loss_rate.csv`` (branche feature/clean-loss-rate).

Applique les décisions prises au diagnostic
(docs/etape1_diagnostic_loss_rate.md, section 3) :
  1. Item Code -> texte (clé de jointure) ;
  2. colonne Item Name retirée : le nom vit dans product_clean (une seule
     source de vérité), le contrat d'équipe n'attend que Item Code + taux ;
  3. taux contrôlés dans [0 ; 100] (aucune valeur hors bornes constatée) ;
  4. taux à 0 % et taux à la moyenne (9.43 %) CONSERVÉS tels quels :
     décision de ne pas inventer de donnée, limite documentée au diagnostic ;
  5. aucune ligne supprimée (251 en entrée = 251 en sortie).

Usage :
    python scripts/etape3_clean_loss_rate.py

Sortie : data/clean/loss_rate_clean.csv (ignorée par Git, comme la donnée
brute — le pipeline est rejouable).
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "loss_rate.csv"
SORTIE = ROOT / "data" / "clean" / "loss_rate_clean.csv"

TAUX = "Loss Rate (%)"
COLONNES = ["Item Code", TAUX]  # contrat d'équipe (étape 2, §4)


def nettoyer(df: pd.DataFrame) -> pd.DataFrame:
    """Retourne la table nettoyée. Fonction pure : réutilisable par la
    consolidation et testable."""
    df = df.copy()
    df["Item Code"] = df["Item Code"].astype(str).str.strip()
    df[TAUX] = df[TAUX].astype(float).round(2)
    return df[COLONNES]


def verifier(brut: pd.DataFrame, propre: pd.DataFrame) -> None:
    """Contrôles de sortie : chaque règle du diagnostic est vérifiée."""
    assert len(brut) == len(propre) == 251, "des lignes ont été perdues !"
    assert propre["Item Code"].is_unique, "Item Code n'est plus une clé unique"
    assert propre.isna().sum().sum() == 0, "valeurs manquantes en sortie"
    assert propre[TAUX].between(0, 100).all(), "taux hors de [0 ; 100]"
    assert list(propre.columns) == COLONNES, "colonnes hors contrat d'équipe"
    assert propre["Item Code"].map(type).eq(str).all(), "Item Code pas en texte"
    print("Controles OK : 251 lignes conservees, cles uniques, taux dans "
          "[0 ; 100], colonnes conformes au contrat.")


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
