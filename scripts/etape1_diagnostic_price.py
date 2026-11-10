"""Étape 1 — Diagnostic de la table brute ``price.csv``.

Responsable : collègue (branche feature/clean-price).

Objectif : inspecter les prix d'achat (wholesale) journaliers et chiffrer
tout ce qui devra être nettoyé avant la consolidation. Chaque constat est
accompagné d'une décision justifiée par une logique métier (règle d'or du
cours).

Usage :
    python scripts/etape1_diagnostic_price.py

Sorties :
    - rapport complet dans la console
    - graphique docs/img/etape1_price_anomalies.png
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # rendu sans fenêtre (rejouable en CI)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "price.csv"
TRANSACTION = ROOT / "data" / "raw" / "transaction.csv"
IMG_DIR = ROOT / "docs" / "img"
PRIX = "Wholesale Price (RMB/kg)"
SEUIL_PRIX_MIN = 0.05  # en dessous : prix d'achat physiquement impossible


def section(titre: str) -> None:
    print(f"\n{'=' * 70}\n{titre}\n{'=' * 70}")


def main() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    df = pd.read_csv(SRC, dtype={"Item Code": str})

    section("1. VUE D'ENSEMBLE")
    print(f"Lignes × colonnes : {df.shape[0]} × {df.shape[1]}")
    print("Colonnes et types détectés par Pandas :")
    print(df.dtypes.to_string())
    print(f"Valeurs manquantes (total) : {int(df.isna().sum().sum())}")
    print(f"Doublons complets de lignes : {int(df.duplicated().sum())}")

    section("2. CLÉ COMPOSITE (Item Code, Date)")
    print(f"Doublons (Item Code, Date) : {int(df.duplicated(['Item Code', 'Date']).sum())}")
    print(f"Produits distincts : {df['Item Code'].nunique()}")
    df["Date"] = pd.to_datetime(df["Date"], errors="raise")
    print(f"Période : {df['Date'].min():%Y-%m-%d} -> {df['Date'].max():%Y-%m-%d}")
    calendrier = pd.date_range(df["Date"].min(), df["Date"].max())
    manquants = calendrier.difference(df["Date"].unique())
    print(f"Jours du calendrier sans aucun prix : {len(manquants)} "
          f"({', '.join(manquants.strftime('%Y-%m-%d'))})")
    par_produit = df.groupby("Item Code").size()
    print(f"Lignes de prix par produit : médiane {par_produit.median():.0f}, "
          f"min {par_produit.min()}, max {par_produit.max()}")
    print(f"Produits avec moins de 30 jours de prix : {int((par_produit < 30).sum())}")

    section("3. PRIX D'ACHAT — BORNES ET ABERRATIONS")
    print(df[PRIX].describe().round(2).to_string())
    print(f"Prix <= 0 : {int((df[PRIX] <= 0).sum())}")
    bas = df[df[PRIX] < SEUIL_PRIX_MIN]
    print(f"Prix < {SEUIL_PRIX_MIN} RMB/kg : {len(bas)} lignes, "
          f"{bas['Item Code'].nunique()} produits "
          f"({bas['Date'].min():%Y-%m-%d} -> {bas['Date'].max():%Y-%m-%d})")
    print(f"  dont exactement 0.01 : {int((df[PRIX] == 0.01).sum())}")
    print(f"Prix > 50 RMB/kg : {int((df[PRIX] > 50).sum())} lignes "
          f"({df.loc[df[PRIX] > 50, 'Item Code'].nunique()} produits)")
    print(f"Prix maximum : {df[PRIX].max()} "
          f"(produit {df.loc[df[PRIX].idxmax(), 'Item Code']})")

    section("4. COUVERTURE VS LES VENTES (transaction.csv)")
    if TRANSACTION.exists():
        ventes = pd.read_csv(TRANSACTION, dtype={"Item Code": str},
                             usecols=["Item Code", "Date"])
        ventes["Date"] = pd.to_datetime(ventes["Date"])
        couples = ventes.drop_duplicates()
        joints = couples.merge(df[["Item Code", "Date"]], on=["Item Code", "Date"])
        print(f"Produits vendus : {ventes['Item Code'].nunique()} "
              f"(dont {ventes['Item Code'].nunique() - len(set(ventes['Item Code']) - set(df['Item Code']))} "
              "avec au moins un prix)")
        print(f"Couples (produit, jour) vendus : {len(couples)} -> "
              f"avec prix d'achat du jour : {len(joints)} "
              f"({len(joints) / len(couples):.1%})")
        sales = ventes.merge(bas[["Item Code", "Date"]], on=["Item Code", "Date"])
        print(f"Lignes de vente touchées par un prix < {SEUIL_PRIX_MIN} : {len(sales)}")
    else:
        print("transaction.csv absent de data/raw/ : contrôle ignoré.")

    # ----- Graphique ------------------------------------------------------
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    ax1.hist(np.log10(df[PRIX]), bins=60, color="#4c78a8")
    ax1.axvline(np.log10(SEUIL_PRIX_MIN), color="#e45756", ls="--",
                label=f"seuil {SEUIL_PRIX_MIN} RMB/kg")
    ax1.set_xlabel("log10(prix d'achat en RMB/kg)")
    ax1.set_ylabel("Nombre de lignes")
    ax1.set_title("Distribution des prix d'achat")
    ax1.legend()
    mensuel = bas.groupby(bas["Date"].dt.to_period("M")).size()
    ax2.bar(mensuel.index.astype(str), mensuel.values, color="#e45756")
    ax2.set_title(f"Prix < {SEUIL_PRIX_MIN} RMB/kg par mois : {len(bas)} lignes")
    ax2.tick_params(axis="x", rotation=60)
    ax2.set_ylabel("Nombre de lignes")
    sortie = IMG_DIR / "etape1_price_anomalies.png"
    fig.savefig(sortie, dpi=150, bbox_inches="tight")
    print(f"\nGraphique enregistré : {sortie}")


if __name__ == "__main__":
    main()
