# Étape 2 — Modèle de données cible & schéma en étoile

> À compléter par l'équipe une fois les 4 diagnostics terminés.
> Objectif : concevoir la structure **avant** la consolidation.

## 1. Modèle relationnel (tables brutes et liaisons)

Inventaire issu des diagnostics de l'étape 1 (clé de jointure commune :
`Item Code`) :

| Table brute | Lignes | Clé primaire | Rôle |
|---|---|---|---|
| `transaction` | 878 503 | _(pas de PK naturelle : 1 ligne = 1 ligne de caisse)_ | Faits : ventes/retours au poids et au prix unitaire |
| `product` | 251 | `Item Code` | Dimension produit : nom + catégorie |
| `price` | _[à compléter]_ | _[à compléter]_ | Prix d'achat / wholesale par date (marge brute) |
| `loss_rate` | _[à compléter]_ | _[à compléter]_ | Taux de perte / démarque |

Liaisons :

- `transaction.Item Code` → `product.Item Code` (vérifié : 0 orphelin,
  5 produits jamais vendus).

## 2. Schéma en étoile (couche Gold)

_[À compléter : dessiner le modèle — table de faits centrale + dimensions._

 Pistes de réflexion (issues du diagnostic) :

- **Table de faits** : 1 ligne = 1 transaction de caisse (ou agrégée par
  jour × produit ?). Mesures : `Quantity Sold (kilo)`,
  `Unit Selling Price (RMB/kg)`, CA = quantité × prix, retours isolés via
  un indicateur `is_return`.
- **Dimensions candidates** : `dim_product` (Item Code, nom),
  `dim_category` (code, nom), `dim_date` (calendrier : jour, mois, année
  — indispensable pour filtrer juin 2022 → juin 2023 et comparer N-1).
- Attention : conserver le **prix au moment de la vente** dans les faits
  (218/246 produits ont plusieurs prix dans le temps) ; le prix
  d'achat/wholesale reste dans `price` pour la marge brute.]_

![Schéma en étoile](img/etape2_star_schema.png)

## 3. Contraintes de qualité à respecter par le pipeline

- Les espaces insécables (`\xa0`) de `Category Name` doivent être normalisés,
  sinon la catégorie « Flower/Leaf Vegetables » apparaît en double dans les
  filtres du dashboard.
- Les 461 retours ne doivent pas être supprimés : ils sont signés (quantité
  négative) et le KPI « quantité vendue » du dictionnaire de données les
  exclut à l'agrégation.
- `Item Code` est une clé de jointure (texte), pas une mesure numérique.
