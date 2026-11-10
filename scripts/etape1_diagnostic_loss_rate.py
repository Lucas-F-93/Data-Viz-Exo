"""Étape 1 — Diagnostic de la table brute ``loss_rate.csv``.

Responsable : collègue (branche feature/clean-loss-rate).

Objectif : inspecter les taux de perte par produit et chiffrer tout ce qui
devra être nettoyé avant la consolidation. Chaque constat est accompagné
d'une décision justifiée par une logique métier (règle d'or du cours).

Usage :
    python scripts/etape1_diagnostic_loss_rate.py

Sorties :
    - rapport complet dans la console
    - graphique docs/img/etape1_loss_rate_distribution.png
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # rendu sans fenêtre (rejouable en CI)
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "loss_rate.csv"
PRODUCT = ROOT / "data" / "raw" / "product.csv"
TRANSACTION = ROOT / "data" / "raw" / "transaction.csv"
IMG_DIR = ROOT / "docs" / "img"
TAUX = "Loss Rate (%)"


def section(titre: str) -> None:
    print(f"\n{'=' * 70}\n{titre}\n{'=' * 70}")


def main() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    df = pd.read_csv(SRC, dtype={"Item Code": str})

    section("1. VUE D'ENSEMBLE")
    print(f"Lignes × colonnes : {df.shape[0]} × {df.shape[1]}")
    print(df.dtypes.to_string())
    print(f"Valeurs manquantes (total) : {int(df.isna().sum().sum())}")
    print(f"Doublons complets : {int(df.duplicated().sum())}")
    print(f"Item Code dupliqués : {int(df['Item Code'].duplicated().sum())}")
    noms = df["Item Name"]
    print(f"Noms avec espaces parasites : {int((noms != noms.str.strip()).sum())}")

    section("2. TAUX DE PERTE — BORNES ET VALEURS SUSPECTES")
    print(df[TAUX].describe().round(2).to_string())
    print(f"Hors de [0 ; 100] : {int(((df[TAUX] < 0) | (df[TAUX] > 100)).sum())}")
    print(f"Taux = 0 : {int((df[TAUX] == 0).sum())}")
    moyenne = round(df[TAUX].mean(), 2)
    n_moy = int((df[TAUX] == moyenne).sum())
    print(f"Taux moyen de la table : {moyenne} ; produits exactement à cette "
          f"valeur : {n_moy} ({n_moy / len(df):.1%})")
    print("Valeurs les plus fréquentes :")
    print(df[TAUX].round(2).value_counts().head(5).to_string())
    print(f"Taux > 25 % : {int((df[TAUX] > 25).sum())}")

    section("3. INTÉGRITÉ AVEC LES AUTRES TABLES")
    produits = pd.read_csv(PRODUCT, dtype={"Item Code": str})
    print(f"Codes loss_rate absents de product : "
          f"{len(set(df['Item Code']) - set(produits['Item Code']))}")
    print(f"Codes product absents de loss_rate : "
          f"{len(set(produits['Item Code']) - set(df['Item Code']))}")
    ca = None
    if TRANSACTION.exists():
        v = pd.read_csv(TRANSACTION, dtype={"Item Code": str},
                        usecols=["Item Code", "Quantity Sold (kilo)",
                                 "Unit Selling Price (RMB/kg)"])
        v["ca"] = v["Quantity Sold (kilo)"] * v["Unit Selling Price (RMB/kg)"]
        ca = v.groupby("Item Code")["ca"].sum()
        vendus = set(ca.index)
        print(f"Produits vendus : {len(vendus)} ; couverts par loss_rate : "
              f"{len(vendus & set(df['Item Code']))}")
        print(f"Produits de loss_rate jamais vendus : "
              f"{len(set(df['Item Code']) - vendus)}")
        d = df.merge(ca.rename("ca"), left_on="Item Code", right_index=True, how="left")
        d["ca"] = d["ca"].fillna(0)
        for nom, masque in [(f"= {moyenne}", d[TAUX] == moyenne), ("= 0", d[TAUX] == 0)]:
            print(f"Part du CA des produits à {nom} : "
                  f"{d.loc[masque, 'ca'].sum() / d['ca'].sum():.1%}")
    else:
        print("transaction.csv absent de data/raw/ : contrôle ignoré.")

    # ----- Graphique ------------------------------------------------------
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.hist(df[TAUX], bins=60, color="#4c78a8")
    ax.annotate(f"{n_moy} produits à {moyenne} %\n(= moyenne : valeur imputée ?)",
                xy=(moyenne, n_moy), xytext=(15, n_moy * 0.8),
                arrowprops=dict(arrowstyle="->"))
    ax.annotate(f"{int((df[TAUX] == 0).sum())} produits à 0 %",
                xy=(0, int((df[TAUX] == 0).sum())), xytext=(3, n_moy * 0.45),
                arrowprops=dict(arrowstyle="->"))
    ax.set_xlabel("Taux de perte (%)")
    ax.set_ylabel("Nombre de produits")
    ax.set_title("loss_rate.csv — distribution des taux de perte (251 produits)")
    sortie = IMG_DIR / "etape1_loss_rate_distribution.png"
    fig.savefig(sortie, dpi=150, bbox_inches="tight")
    print(f"\nGraphique enregistré : {sortie}")


if __name__ == "__main__":
    main()
