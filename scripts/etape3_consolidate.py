"""Étape 3 — Consolidation : assemblage du schéma en étoile (couche Gold).

Assemble les tables nettoyées de ``data/clean/`` selon le modèle défini à
l'étape 2 (docs/etape2_modele_donnees.md) :

  FACT_SALES   : 1 ligne = 1 ligne de caisse (transaction + infos produit)
  DIM_PRODUCT  : référentiel produit (product + loss_rate si disponible)
  DIM_DATE     : calendrier couvrant la période des ventes

Le script attend les tables de l'équipe (contrat d'équipe, étape 2 §4) :
  data/clean/transaction_clean.csv   (Lucas)
  data/clean/product_clean.csv       (Lucas)
  data/clean/price_clean.csv         (collègue — optionnel pour l'instant)
  data/clean/loss_rate_clean.csv     (collègue — optionnel pour l'instant)

Les tables du collègue sont prises en compte automatiquement dès qu'elles
sont posées dans data/clean/ : le wholesale price complète la marge brute,
le loss rate complète DIM_PRODUCT.

Usage :
    python scripts/etape3_consolidate.py

Sorties (ignorées par Git, rejouables) :
    data/clean/dim_date.csv
    data/clean/dim_product.csv
    data/clean/fact_sales.csv
    data/clean/consolidated_sales.csv   (vue plate : faits + dimensions)
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"

# Colonnes clés toujours lues en texte (contrat d'équipe : identifiants).
DTYPES_CLES = {"Item Code": str, "Category Code": str}


def charger(nom: str, requis: bool = True) -> pd.DataFrame | None:
    chemin = CLEAN / nom
    if not chemin.exists():
        if requis:
            raise FileNotFoundError(
                f"{nom} manquant dans {CLEAN} — lance d'abord les scripts "
                "de nettoyage des responsables concernés.")
        print(f"[i] {nom} absent : table du collègue pas encore fusionnée, "
              "on continue sans.")
        return None
    return pd.read_csv(chemin, dtype=DTYPES_CLES)


def construire_dim_date(faits: pd.DataFrame) -> pd.DataFrame:
    """Calendrier couvrant exactement les dates de ventes présentes."""
    dates = pd.Series(sorted(faits["date"].unique()), name="date")
    dim = pd.DataFrame({
        "date": pd.to_datetime(dates),
    })
    dim["year"] = dim["date"].dt.year
    dim["quarter"] = dim["date"].dt.quarter
    dim["month"] = dim["date"].dt.month
    dim["month_name"] = dim["date"].dt.strftime("%B")
    dim["day"] = dim["date"].dt.day
    dim["day_name"] = dim["date"].dt.strftime("%A")
    dim["day_of_week"] = dim["date"].dt.day_of_week
    dim["week_of_year"] = dim["date"].dt.isocalendar().week.astype(int)
    # Indicateur métier : période cible du Comex (12 derniers mois).
    dim["is_last_12m"] = dim["date"].between("2022-07-01", "2023-06-30").astype(int)
    return dim


def main() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    faits = charger("transaction_clean.csv")
    produits = charger("product_clean.csv")
    prix = charger("price_clean.csv", requis=False)
    pertes = charger("loss_rate_clean.csv", requis=False)

    # ---- DIM_PRODUCT : référentiel + loss rate (si fourni) ----------------
    dim_product = produits.rename(columns={
        "Item Code": "item_code",
        "Item Name": "item_name",
        "Category Code": "category_code",
        "Category Name": "category_name",
    }).copy()
    if pertes is not None:
        pertes = pertes.rename(columns={
            "Item Code": "item_code",
            "Loss Rate (%)": "loss_rate_pct",
        })[["item_code", "loss_rate_pct"]]
        avant = len(dim_product)
        dim_product = dim_product.merge(pertes, on="item_code", how="left")
        assert len(dim_product) == avant, "le merge loss_rate a dupliqué des lignes"
    else:
        dim_product["loss_rate_pct"] = pd.NA

    # ---- FACT_SALES : faits + jointure produit (N..1) ---------------------
    faits = faits.rename(columns={
        "Item Code": "item_code",
        "Date": "date",
        "Quantity Sold (kilo)": "quantity_kilo",
        "Unit Selling Price (RMB/kg)": "unit_selling_price",
        "Sale or Return": "sale_or_return",
        "Discount (Yes/No)": "discount",
    })
    avant = len(faits)
    fact_sales = faits.merge(
        dim_product[["item_code", "category_code", "category_name"]],
        on="item_code", how="left", validate="many_to_one")
    assert len(fact_sales) == avant, "le merge produit a dupliqué des lignes"
    assert fact_sales["category_name"].notna().all(), \
        "ventes orphelines : produit inconnu dans le référentiel"

    # ---- Marge brute : wholesale price du jour (si fourni) ------------------
    if prix is not None:
        prix = prix.rename(columns={
            "Item Code": "item_code",
            "Date": "date",
            "Wholesale Price (RMB/kg)": "wholesale_price",
        })
        if not prix.duplicated(["item_code", "date"]).any():
            fact_sales = fact_sales.merge(
                prix, on=["item_code", "date"], how="left", validate="many_to_one")
            fact_sales["margin_amount"] = (
                fact_sales["sales_amount"]
                - fact_sales["quantity_kilo"] * fact_sales["wholesale_price"]
            ).round(2)
            couverture = fact_sales["wholesale_price"].notna().mean()
            print(f"[i] prix d'achat rattaches : couverture {couverture:.1%} des ventes")
        else:
            print("[!] price_clean a des doublons (item_code, date) : "
                  "a corriger par le responsable avant integration.")
            fact_sales["wholesale_price"] = pd.NA
            fact_sales["margin_amount"] = pd.NA
    else:
        fact_sales["wholesale_price"] = pd.NA
        fact_sales["margin_amount"] = pd.NA

    # ---- DIM_DATE ----------------------------------------------------------
    dim_date = construire_dim_date(fact_sales)

    # ---- Vue consolidée plate (pour le dashboard) --------------------------
    # On ne fusionne que les colonnes encore absentes des faits (item_name,
    # loss_rate_pct...) pour éviter les suffixes _x/_y.
    complement = [c for c in ["item_name", "loss_rate_pct", "category_code",
                              "category_name"]
                  if c in dim_product.columns and c not in fact_sales.columns]
    consolidated = fact_sales.merge(dim_product[["item_code"] + complement],
                                     on="item_code", how="left",
                                     validate="many_to_one")
    assert len(consolidated) == len(fact_sales), "doublons au merge final"
    consolidated["date"] = pd.to_datetime(consolidated["date"])

    # ---- Contrôles finaux ---------------------------------------------------
    assert len(consolidated) == 878_503, \
        f"lignes perdues en cours de route : {len(consolidated)}"
    assert consolidated["category_name"].nunique() == 6, \
        "les categories se sont re-dupliquees (verifier les \\xa0)"
    assert consolidated["item_name"].notna().all()

    dim_product.to_csv(CLEAN / "dim_product.csv", index=False)
    dim_date.to_csv(CLEAN / "dim_date.csv", index=False)
    fact_sales.to_csv(CLEAN / "fact_sales.csv", index=False)
    consolidated.to_csv(CLEAN / "consolidated_sales.csv", index=False)

    # Ordre de grandeur métier : CA de la période cible du Comex.
    ca_12m = consolidated.loc[
        (consolidated["date"] >= "2022-07-01")
        & (consolidated["date"] <= "2023-06-30"), "sales_amount"].sum()
    ventes_sans_retours = consolidated.loc[
        consolidated["is_return"] == 0, "quantity_kilo"].sum()
    print("Controles OK : 878 503 lignes conservees, 6 categories propres, "
          "jointures produit/date sans perte.")
    print(f"CA net 12 derniers mois (07/2022-06/2023) : {ca_12m:,.0f} RMB"
          .replace(",", " "))
    print(f"Quantite vendue sans retours (3 ans) : "
          f"{ventes_sans_retours:,.0f} kg".replace(",", " "))
    print(f"Tables ecrites dans {CLEAN}: dim_date, dim_product, fact_sales, "
          "consolidated_sales")


if __name__ == "__main__":
    main()
