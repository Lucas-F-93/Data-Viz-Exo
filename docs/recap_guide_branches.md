# Guide de passation — ce qu'on a fait, étape par étape

> Objectif de ce document : pouvoir **expliquer chaque étape** du projet et
> **manipuler les branches Git** sans aide. Chaque commande listée est celle
> réellement exécutée dans ce repo, avec son effet.

---

## 0. Rappel du besoin métier (pour l'oral)

Le Comex trouve que **les ventes de produits frais sous-performent sur
certaines catégories** et veut savoir où agir. Nous sommes 4 Data
Analysts/Engineers : chacun traite **un seul CSV** (spécialisation des rôles),
l'objectif final est un dashboard sur les 12 derniers mois (juil. 2022 →
juin 2023) avec CA, marge brute, volumes.

Répartition : Lucas → `transaction.csv` + `product.csv`, le collègue →
`price.csv` + `loss_rate.csv`.

---

## 1. La logique Git en 3 phrases

- **Un commit** = une photo du projet à un instant T, avec un message.
- **Une branche** = une étiquette qui pointe sur un commit, et avance quand
  on committe. Créer une branche ne copie rien : chacun avance dans son
  couloir sans toucher aux autres.
- **Un merge** = ramener le travail d'une branche dans une autre. Git
  fusionne automatiquement ; il ne demande de l'aide que si **deux personnes
  ont modifié exactement les mêmes lignes** (conflit).

Le schéma de la slide 38 (celui qu'on a appliqué) :

```
main      production — on n'y touche JAMAIS directement
└── develop    intégration — on y fusionne les branches validées
    ├── feature/clean-transaction   (Lucas)
    ├── feature/clean-product       (Lucas)
    ├── feature/clean-price         (collègue)
    └── feature/clean-loss-rate     (collègue)
```

**Pourquoi pas de conflit ?** Parce qu'une branche = une personne = un
fichier CSV. Des fichiers différents modifiés par des personnes différentes
dans des branches différentes = fusions automatiques.

---

## 2. Chronologie complète, étape par étape

### Étape A — Créer le repo local

```bash
git init -b main          # créer le repo, la branche de départ s'appelle main
git add -A                # indexer TOUS les fichiers respectant .gitignore
git commit -m "chore: initialisation du repo (structure, README, gitignore)"
```

**Points importants :**

- Le `.gitignore` exclut **les CSV bruts** (`data/raw/*`) : 52 Mo, trop lourd
  pour GitHub, et la donnée brute n'est pas du code. Chacun les pose en local.
- Le rendu du cours = un **README** qui explique les étapes 1 à 3 avec des
  images → d'où la structure `docs/`, `scripts/`, `data/`.

### Étape B — Créer les branches d'équipe

```bash
git checkout -b develop                  # branche d'intégration commune
git checkout -b feature/clean-transaction # ma branche pour transaction.csv
```

`checkout -b` = « crée la branche **et** va dessus ». Elle part de l'état
exact de la branche courante (même commit, mêmes fichiers).

### Étape C — Étape 1 du cours : le diagnostic (sur SA branche)

Sur `feature/clean-transaction` uniquement :

1. J'ai inspecté `transaction.csv` avec Pandas (script
   `scripts/etape1_diagnostic_transaction.py`) : 878 503 lignes, 0 valeur
   manquante, 0 doublon, 461 retours en quantités négatives, 2 formats
   d'heures, codes produits sur 15 chiffres...
2. Chaque constat → une décision **justifiée par la logique métier** (règle
   d'or du cours). Exemples :
   - les 461 retours → **conservés** + colonne `is_return` (le KPI « quantité
     vendue » les exclut, mais le CA net en a besoin) ;
   - les grosses quantités (jusqu'à 160 kg) → **conservées** : marché de
     gros, ce sont des clients professionnels ;
   - `Item Code` → **converti en texte** : c'est une clé de jointure, pas un
     nombre à additionner.
3. Constat piégeux de `product.csv` : un **espace insécable invisible**
   (`\xa0`) dans `Flower/Leaf\xa0Vegetables` → sans correction, la catégorie
   apparaîtrait en **double** dans les filtres du dashboard.

Puis :

```bash
git add -A
git commit -m "feat(transaction): diagnostic etape 1 de transaction.csv"
git push -u origin feature/clean-transaction
```

Même chose sur `feature/clean-product` pour `product.csv`.

### Étape D — Relier GitHub et pousser tout le monde

Le repo GitHub avait été créé avec un « Initial commit » (README auto-généré
par GitHub), sans lien avec notre historique local :

```bash
git remote add origin https://github.com/Lucas-F-93/Data-Viz-Exo.git
git fetch origin                          # lire ce qui existe déjà sur GitHub
git checkout main
git merge origin/main --allow-unrelated-histories -X ours
                                          # réconcilier SANS écraser : on garde
                                          # notre README détaillé
git checkout develop && git merge --ff-only main   # develop suit main
git push -u origin main develop feature/clean-transaction feature/clean-product
```

`-u` (upstream) = « retiens que cette branche locale suit cette branche
distant » → les `git push` suivants n'ont plus besoin d'argument.

### Étape E — Intégrer les branches dans develop (le cœur de la slide 38)

```bash
git checkout develop          # aller sur la branche d'intégration
git pull                      # récupérer ce que les autres ont pu pousser
git merge --no-ff feature/clean-transaction -m "merge: integre feature/clean-transaction"
git merge --no-ff feature/clean-product     -m "merge: integre feature/clean-product"
git push
```

- `--no-ff` = garder visible dans l'historique **le fait** qu'une branche a
  été fusionnée (le graphe montre la ramification puis la fusion) ;
- 0 conflit : les deux branches touchaient des fichiers différents.

L'historique qui en résulte (visible sur GitHub → Insights → Network) :

```
*   035a06b docs(schema): schema en etoile des 4 CSV          ← develop
|\
* | 653b9fe fix(schema): titre + roles + cles uniquement
* | f39d94a docs(note): note de passation collegue
* | 4681919 feat(consolidation): etape 3 - assemblage
* \  a361668 merge: integre feature/clean-product
|\ \
* \ \ aa4cd82 merge: integre feature/clean-transaction
* 075c180 feat(modele): etape 2 - modele + contrat d'equipe
* 26b6da1 merge: integre le commit initial GitHub
* 0955b27 chore: initialisation du repo
```

### Étape F — Étape 2 du cours : le modèle de données

Fait directement sur `develop` (travail d'équipe, pas d'un seul fichier) :

- `docs/etape2_modele_donnees.md` : modèle relationnel des 4 tables autour
  de `Item Code`, puis **schéma en étoile** : `transaction.csv` = **table de
  faits** centrale, `product.csv` / `price.csv` / `loss_rate.csv` =
  **dimensions** ;
- l'image `docs/img/etape2_star_schema.png` est générée par un script
  (`scripts/etape2_star_schema.py`) — donc rejouable et versionnée ;
- **contrat d'équipe** (section 4) : le nom exact des fichiers que chacun
  doit produire dans `data/clean/` (`price_clean.csv`,
  `loss_rate_clean.csv`...) pour que la consolidation de tout le monde
  s'assemble sans friction.

### Étape G — Étape 3 du cours : nettoyage et consolidation

Sur chaque branche feature, puis fusion dans `develop` :

- `scripts/etape3_clean_transaction.py` : dates → datetime, heures en format
  unique, `Item Code` en texte, `is_return`, `sales_amount` = qté × prix.
  **878 503 lignes en entrée = 878 503 en sortie** ;
- `scripts/etape3_clean_product.py` : `\xa0` normalisés, libellés nettoyés,
  251 lignes, 6 catégories propres ;
- `scripts/etape3_consolidate.py` : assemble le schéma en étoile
  (`fact_sales`, `dim_product`, `dim_date`) et **attend les tables du
  collègue** : dès que `price_clean.csv` et `loss_rate_clean.csv` sont posés
  dans `data/clean/`, la marge brute et les taux de perte s'intègrent
  automatiquement.

Chaque script contient des **contrôles** (`assert`) : nombre de lignes
conservé, clés uniques, catégories non dupliquées. Si une règle métier est
violée, le pipeline **échoue** au lieu de produire une donnée fausse.

### Étape H — Ce qui reste à faire

1. Le collègue accepte l'invitation, clone, suit `NOTE_COLLEGUE.md` ;
2. il pousse `feature/clean-price` et `feature/clean-loss-rate`, les fusionne
   dans `develop` ;
3. on relance `python scripts/etape3_consolidate.py` ;
4. validation finale → **production** :

```bash
git checkout main
git merge develop
git push
```

---

## 3. Lexique des commandes utilisées

| Commande | Effet en une phrase |
|---|---|
| `git init -b main` | Créer un repo dont la branche de départ est `main` |
| `git status` | Voir où j'en suis (branche courante, fichiers modifiés) |
| `git add -A` | Indexer toutes mes modifications pour le prochain commit |
| `git commit -m "..."` | Prendre la photo, avec un message explicatif |
| `git checkout <branche>` | Se déplacer sur une branche existante |
| `git checkout -b <nouvelle>` | Créer une branche ET aller dessus |
| `git branch -a` | Lister les branches (locales + distantes) |
| `git remote add origin <url>` | Relier ce repo local à GitHub |
| `git fetch` | Télécharger l'état de GitHub **sans** y toucher |
| `git pull` | `fetch` + intégrer dans ma branche courante |
| `git push -u origin <branche>` | Envoyer ma branche sur GitHub (et la lier) |
| `git merge <branche>` | Ramener le travail d'une branche dans la courante |
| `git merge --no-ff <branche>` | Idem, en gardant la trace visible de la fusion |
| `git merge --ff-only` | Fusionner uniquement si c'est un avancement simple |
| `git log --oneline --graph --all` | Voir l'historique en arbre, toutes branches |
| `git ls-remote origin` | Lister les branches qui existent sur GitHub |

Messages de commit : préfixe `feat:` (nouvelle fonctionnalité), `fix:`
(correction), `docs:` (documentation), `chore:` (outillage), puis un tiret et
le contenu. Convention lisible, appréciée en entreprise.

---

## 4. Les 5 gestes à savoir refaire les yeux fermés

1. **Commencer une tâche** :
   `git checkout develop && git pull && git checkout -b feature/clean-xxx`
2. **Sauvegarder mon travail** :
   `git add -A && git commit -m "feat(xxx): ..."`
3. **Envoyer ma branche** : `git push -u origin feature/clean-xxx`
4. **Intégrer mon travail dans develop** :
   `git checkout develop && git pull && git merge feature/clean-xxx && git push`
5. **Récupérer le travail du collègue** :
   `git checkout develop && git pull` (puis relancer la consolidation)

**En cas de conflit** (deux personnes ont modifié les mêmes lignes) : Git
marque le fichier avec `<<<<<<<`, on discute avec l'auteur, on garde les
bonnes lignes, puis `git add <fichier> && git commit`. On ne « gagne » jamais
un conflit en écrasant l'autre : jamais de `git push --force`.

---

## 5. Auto-quiz avant de présenter (réponses en dessous)

1. Pourquoi une branche par fichier CSV plutôt que tout le monde sur `develop` ?
2. Qu'est-ce qu'un commit, concrètement ?
3. Pourquoi n'a-t-on pas eu de conflit ?
4. Quelle est la différence entre `fetch` et `pull` ?
5. Pourquoi les CSV ne sont-ils pas dans le repo GitHub ?
6. Dans le schéma en étoile, pourquoi `transaction.csv` est la table de faits
   et pas `product.csv` ?
7. Que fait `git merge --no-ff` de plus que `git merge` ?
8. Pourquoi garder les 461 retours au lieu de les supprimer ?

**Réponses**

1. Un seul rédacteur par périmètre : personne ne peut écraser le travail
   d'un autre, et les fusions sont automatiques.
2. Une photo immuable du projet à un instant T, référencée par un message —
   on peut toujours revenir en arrière.
3. Les branches modifiées des fichiers différents : Git sait fusionner sans
   intervention quand les zones touchées ne se recouvrent pas.
4. `fetch` télécharge l'état distant sans rien modifier ; `pull` = `fetch` +
   fusion dans la branche courante.
5. 52 Mo, GitHub les refuserait ou les rendrait pénibles ; et la donnée
   brute n'est pas du code — le pipeline est rejouable depuis `data/raw/`.
6. La table de faits porte les **mesures** (quantités, prix, CA) avec un
   grain fin (1 ligne de caisse) ; `product` décrit les objets (noms,
   catégories) — c'est une dimension.
7. Il force un commit de fusion même quand Git pourrait « avancer
   simplement » : l'historique garde la trace de l'existence de la branche.
8. Le KPI « quantité vendue » les exclut (filtre `is_return = 0`), mais le
   CA net et l'analyse des pertes en ont besoin ; les supprimer fausserait
   les chiffres métier.

---

## 6. Chiffres à connaître pour l'oral

| Chiffre | Valeur |
|---|---|
| Lignes de ventes traitées | 878 503 (aucune supprimée) |
| Période couverte | 07/2020 → 06/2023 |
| Produits / catégories | 251 produits, 6 catégories |
| Retours | 461 (quantités négatives, marqués `is_return`) |
| CA net 12 derniers mois | ≈ 1,15 M RMB |
| Quantité vendue sans retours (3 ans) | ≈ 471 t |
| Marge brute 12 mois (avec les prix du collègue) | ≈ 447 k RMB (≈ 38,7 %) |
