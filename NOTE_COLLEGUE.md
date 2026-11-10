# Note pour le responsable de `price.csv` et `loss_rate.csv`

Salut ! Voici le point sur ce qui a été fait, et ta to-do pour qu'on
assemble le pipeline sans se marcher dessus.

## Ce qui a été fait (Lucas)

- **Repo Git** avec la structure demandée par le cours (slide 38) :
  `main` = production (on n'y touche pas), `develop` = intégration, et une
  branche `feature/clean-<fichier>` par fichier CSV.
- **`transaction.csv` et `product.csv` traités de bout en bout** :
  - Étape 1 : diagnostics chiffrés → `docs/etape1_diagnostic_transaction.md`
    et `docs/etape1_diagnostic_product.md` (scripts rejouables inclus) ;
  - Étape 2 : modèle relationnel + schéma en étoile →
    `docs/etape2_modele_donnees.md` (avec le contrat d'équipe, section 4) ;
  - Étape 3 : nettoyages → `scripts/etape3_clean_transaction.py` et
    `scripts/etape3_clean_product.py`, et la consolidation prête →
    `scripts/etape3_consolidate.py` (elle assemble `fact_sales`,
    `dim_product`, `dim_date` et **elle t'attend**).
- Les CSV bruts ne sont **pas** dans le repo (trop lourds) : chacun les pose
  dans `data/raw/` en local, les sorties vont dans `data/clean/`. Tout est
  rejouable avec les scripts.

## Ta to-do, dans l'ordre

1. **Accepte l'invitation** GitHub (reçue par mail), puis clone :
   ```bash
   git clone https://github.com/Lucas-F-93/Data-Viz-Exo.git
   ```
2. Pose `price.csv` et `loss_rate.csv` dans `data/raw/` (en local).
3. Installe les dépendances : `pip install pandas matplotlib`.
4. Part d'un `develop` à jour et crée tes branches :
   ```bash
   git checkout develop && git pull
   git checkout -b feature/clean-price     # puis feature/clean-loss-rate
   ```
5. **Étape 1 — tes diagnostics** : inspire-toi de
   `scripts/etape1_diagnostic_product.py` (copie-le et adapte-le) et rends
   `docs/etape1_diagnostic_price.md` + `docs/etape1_diagnostic_loss_rate.md` :
   chaque problème **chiffré** + décision de nettoyage **justifiée métier**
   (règle d'or du cours). Pistes à vérifier : doublons `(Item Code, Date)`
   dans price.csv, valeurs manquantes, bornes aberrantes des taux de perte,
   produits couverts vs les 246 vendus.
6. **Étape 3 — tes nettoyages** : produis dans `data/clean/` exactement les
   fichiers du contrat d'équipe (`docs/etape2_modele_donnees.md`, section 4) :
   - `price_clean.csv` : colonnes `Date`, `Item Code`,
     `Wholesale Price (RMB/kg)` ;
   - `loss_rate_clean.csv` : colonnes `Item Code`, `Loss Rate (%)` ;
   - `Item Code` en **texte** dans les deux (c'est une clé de jointure,
     pas un nombre).
7. Commit et pousse **ta branche** puis fusionne dans `develop` :
   ```bash
   git push -u origin feature/clean-price
   git checkout develop && git pull && git merge feature/clean-price
   git push
   ```
   (ou passe par une Pull Request sur GitHub si tu préfères).
8. Relance la consolidation : `python scripts/etape3_consolidate.py`.
   Si tout va bien tu vois `[i] prix d'achat rattaches : couverture 100.0%
   des ventes` et les contrôles OK : ta marge brute et tes taux de perte
   sont intégrés au schéma en étoile.

## Règles Git pour ne rien écraser

- Jamais de commit direct sur `main`, jamais de `git push --force`.
- Toujours repartir d'un `develop` à jour avant de créer une branche.
- Un conflit au merge = on en parle ensemble, on ne « gagne » pas.

## Ce que la consolidation vérifie déjà pour toi

- le nombre de lignes de ventes est conservé (878 503) ;
- les 6 catégories restent propres (le piège des espaces insécables) ;
- `price_clean.csv` sans doublon `(Item Code, Date)`, sinon message explicite ;
- toute perte de lignes au merge = erreur immédiate (`assert`).
