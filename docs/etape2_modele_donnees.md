# Étape 2 — Modèle de données cible & schéma en étoile

> Conçu collectivement à partir des diagnostics de l'étape 1, **avant** la
> consolidation (ordre du cours : le modèle d'abord, le code ensuite).

## 1. Modèle relationnel (tables brutes et liaisons)

Les 4 tables brutes et leurs liaisons autour de la clé commune **`Item Code`** :

| Table brute | Lignes | Clé | Rôle |
|---|---|---|---|
| `transaction` | 878 503 | pas de PK naturelle (1 ligne = 1 ligne de caisse) | Faits : ventes et retours au poids et au prix unitaire |
| `product` | 251 | PK `Item Code` | Référentiel : nom du produit + catégorie |
| `price` | 55 982 | PK composite (`Item Code`, `Date`) | Prix d'achat (wholesale) par produit et par jour |
| `loss_rate` | 251 | PK `Item Code` | Taux de perte / démarque par produit |

Vérifications d'intégrité faites au diagnostic (étape 1) :

- `transaction.Item Code` → `product.Item Code` : **0 orphelin**, jointure sûre ;
- `product` : 251 codes uniques (clé primaire parfaite) ;
- 5 produits du référentiel jamais vendus (ils resteront dans la dimension).

```mermaid
erDiagram
    PRODUCT ||--o{ TRANSACTION : "Item Code"
    CATEGORY ||--o{ PRODUCT : "Category Code"
    PRODUCT ||--o{ PRICE : "Item Code"
    PRODUCT ||--|| LOSS_RATE : "Item Code"

    PRODUCT {
        varchar item_code PK
        varchar item_name
        varchar category_code FK
        varchar category_name
    }
    CATEGORY {
        varchar category_code PK
        varchar category_name
    }
    TRANSACTION {
        date date
        time time
        varchar item_code FK
        float quantity_kilo
        float unit_selling_price
        varchar sale_or_return
        varchar discount
    }
    PRICE {
        varchar item_code FK
        date date
        float wholesale_price
    }
    LOSS_RATE {
        varchar item_code PK
        varchar item_name
        float loss_rate_pct
    }
```

## 2. Schéma en étoile (couche Gold)

**Grain de la table de faits : 1 ligne = 1 ligne de caisse.**

- `FACT_SALES` au centre : les mesures (quantité, prix, CA) + les clés vers
  les dimensions ;
- les attributs descriptifs (nom, catégorie, calendrier) partent dans les
  dimensions, **dédupliqués** : 251 lignes de produits au lieu de 878 503.

| Élément | Table | Contenu |
|---|---|---|
| **Table de faits** | `FACT_SALES` | `item_code` (FK), `date` (FK), `quantity_kilo` (signée : négative = retour), `unit_selling_price`, `sales_amount` = qté × prix, `is_return`, `is_discount`, `hour` |
| Dimension | `DIM_PRODUCT` | `item_code` (PK), `item_name`, `category_code`, `category_name` (normalisée : `\xa0` → espace), `loss_rate_pct` |
| Dimension | `DIM_DATE` | `date` (PK), `year`, `quarter`, `month`, `month_name`, `day`, `day_name`, `day_of_week`, `week_of_year`, `is_last_12m` (période cible 07/2022 → 06/2023) |

**Variantes et justifications :**

- `wholesale_price` (de `price.csv`) sera **rattaché à la vente** dans la
  vue consolidée via la jointure (`Item Code`, `Date`) — 218/246 produits ont
  plusieurs prix dans le temps, on ne peut donc pas le figer dans la dimension
  produit. Il sert au calcul de la **marge brute** (prix de vente − prix
  d'achat), KPI demandé par le Comex.
- `loss_rate` est quasi-statique par produit → attribut de `DIM_PRODUCT`.
- Les colonnes `Sale or Return` et `Discount` deviennent des indicateurs
  binaires (`is_return`, `is_discount`) : directement filtrables dans le
  dashboard, et la quantité vendue « sans les retours » (dictionnaire de
  données) s'obtient avec `is_return = 0`.

```mermaid
erDiagram
    DIM_DATE ||--o{ FACT_SALES : "date (N..1)"
    DIM_PRODUCT ||--o{ FACT_SALES : "item_code (N..1)"

    FACT_SALES {
        varchar item_code FK
        date date FK
        int hour
        float quantity_kilo
        float unit_selling_price
        float sales_amount
        int is_return
        int is_discount
    }
    DIM_DATE {
        date date PK
        int year
        int quarter
        int month
        varchar month_name
        int day
        varchar day_name
        int day_of_week
        int week_of_year
        int is_last_12m
    }
    DIM_PRODUCT {
        varchar item_code PK
        varchar item_name
        varchar category_code
        varchar category_name
        float loss_rate_pct
    }
```

![Schéma en étoile](img/etape2_star_schema.png)

## 3. Contraintes de qualité imposées au pipeline (issues du diagnostic)

| Contrainte | Origine (diagnostic) |
|---|---|
| Les `\xa0` de `Category Name` normalisés en espaces | sinon la catégorie « Flower/Leaf Vegetables » apparaît en double dans les filtres |
| `Item Code` traité en **texte** dans toutes les tables | c'est une clé de jointure, pas une mesure |
| Les 461 retours **conservés** et marqués `is_return` | le KPI « quantité vendue » du dictionnaire exclut les retours ; les garder préserve le CA net |
| 878 503 lignes en entrée = 878 503 en sortie | aucune suppression : les « outliers » sont des achats en gros légitimes |
| Heures parsées en un format unique (`format="mixed"`) | 132 lignes sans millisecondes à ne pas perdre |

## 4. Règles de nommage des sorties (contrat d'équipe)

Pour que les branches feature de chacun s'assemblent sans friction dans
`develop`, chaque responsable produit sa table nettoyée dans `data/clean/` :

| Responsable | Fichier attendu | Colonnes clés |
|---|---|---|
| Lucas | `transaction_clean.csv` | `Date`, `Time`, `Item Code`, `Quantity Sold (kilo)`, `Unit Selling Price (RMB/kg)`, `Sale or Return`, `Discount (Yes/No)`, `is_return`, `sales_amount`, `hour` |
| Lucas | `product_clean.csv` | `Item Code`, `Item Name`, `Category Code`, `Category Name` |
| _[collègue]_ | `price_clean.csv` | `Date`, `Item Code`, `Wholesale Price (RMB/kg)` |
| _[collègue]_ | `loss_rate_clean.csv` | `Item Code`, `Loss Rate (%)` |

Le script `scripts/etape3_consolidate.py` assemble ensuite la table de faits
et les dimensions selon le schéma ci-dessus.
