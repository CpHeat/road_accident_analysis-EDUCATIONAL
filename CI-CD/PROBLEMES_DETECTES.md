# Problemes detectes - Audit qualite du projet

## 1. Securite

### Credentials base de donnees en dur

**Fichier :** `backend/database.py:8`

Le fallback contient un identifiant et un mot de passe en clair. Si la variable d'environnement n'est pas definie, l'application utilise des credentials par defaut.

**Fichier :** `docker-compose.yml:15-17, 43`

Les credentials sont en clair dans le fichier docker-compose, qui est versionne dans git.

---

### Mot de passe trivial

Le mot de passe PostgreSQL est `example`. Meme en environnement de developpement, cela peut poser probleme si le port 5432 est expose.

---

### Exception silencieuse masquant des erreurs

**Fichier :** `backend/features.py:167-168`

Toute erreur lors de l'appel a l'API sunrise-sunset est avalee silencieusement : erreurs reseau, erreurs de parsing JSON, erreurs d'authentification. Aucune trace dans les logs.

---

### Pas de rate limiting sur les endpoints

**Fichier :** `backend/main.py`

L'endpoint `/predict` fait un appel a une API externe (sunrise-sunset.org) et une ecriture en base a chaque requete. Sans rate limiting, un abus peut provoquer un deni de service.

---

### `unsafe_allow_html=True` dans Streamlit

**Fichier :** `front/app.py:29, 71`

L'utilisation de `unsafe_allow_html=True` ouvre une surface d'attaque XSS si du contenu dynamique non assaini est injecte dans le futur.

---

### Cache memoire non borne

**Fichier :** `backend/features.py:115`

Le cache croit indefiniment en memoire. En production avec des requetes variees, cela peut mener a un epuisement de memoire (memory leak).

---

### Pas de `.dockerignore` dans les sous-dossiers de build

Le fichier `.dockerignore` est a la racine, mais les contextes de build Docker sont `./backend` et `./front`. Le `.dockerignore` racine n'est pas pris en compte lors du build des sous-dossiers. Des fichiers sensibles (`.env`, `.git`, `__pycache__`) pourraient se retrouver dans l'image.

---

## 2. Formatage

### Logging avec f-strings au lieu de lazy formatting (G004)

**Fichier :** `backend/main.py` (9 occurrences), `backend/model.py` (7 occurrences)

L'utilisation de f-strings dans les appels de logging evalue toujours l'expression, meme si le niveau de log est desactive.

---

## 3. Imports

### Blocs d'imports non tries (I001)

**Fichiers concernes :**

| Fichier | Probleme |
|---|---|
| `backend/database.py` | stdlib et third-party melanges |
| `backend/features.py` | Ordre alphabetique non respecte |
| `backend/main.py` | Ordre non respecte |
| `backend/model.py` | Ordre non respecte |
| `backend/models_db.py` | Ordre non respecte |
| `front/app.py` | `import requests` avant `import os` |
| `front/components/__init__.py` | Non trie |
| `front/styles/__init__.py` | Non trie |

---

### Re-exports implicites dans `__init__.py` (F401)

**Fichier :** `front/components/__init__.py:3-5`

**Fichier :** `front/styles/__init__.py:3`

Ces imports sont utilises comme re-exports pour les consommateurs du package, mais ruff les considere comme inutilises car ils ne sont pas explicitement re-exportes.

---

### Imports deprecies de `typing` (UP035)

**Fichier :** `ML/functions/model_selection.py:3`

**Fichier :** `ML/functions/hyperopt_tuning.py:20`

**Fichier :** `ML/functions/display_metrics.py:28`

Depuis Python 3.9+, il faut utiliser `dict`, `list`, `tuple` directement au lieu de `Dict`, `List`, `Tuple`.

---

### Import `Union` inutilise

**Fichier :** `ML/functions/display_metrics.py:28`

`Union` est importe mais jamais utilise dans le fichier.

---

## 4. Types

### Type de retour incorrect pour `get_db()`

**Fichier :** `backend/database.py:21`

**Erreur mypy :** `The return type of an async generator function should be "AsyncGenerator" or one of its supertypes`

La fonction utilise `yield` donc c'est un generateur asynchrone, pas une coroutine retournant une `AsyncSession`.

---

### Variables globales sans annotation de type

**Fichier :** `backend/model.py:21-23`

Pas d'annotations de type. Mypy les infere comme `None` uniquement.

---

### Parametres non types dans `save_best_model()`

**Fichier :** `ML/functions/model_selection.py:43-46`

---

### Type de retour manquant pour `init_db()`

**Fichier :** `backend/database.py:27`

---

### Type de retour manquant pour endpoints simples

**Fichier :** `backend/main.py:72, 77`

---

### `class Config` deprecie pour Pydantic v2

**Fichier :** `backend/schemas.py:41-42`
---

### Stubs manquants pour `requests`

**Fichier :** `front/app.py:3`

Mypy signale : `Library stubs not installed for "requests"`.

---

### `ml_config.py` sans aucune annotation

**Fichier :** `ML/ml_config.py:1-3`

Aucune annotation de type, pas de docstring, format non conventionnel (pas de constantes en majuscules).

---

## 5. Documentation

### Modules sans docstring (D100)

| Fichier |
|---|
| `backend/database.py` |
| `backend/features.py` |
| `backend/main.py` |
| `backend/model.py` |
| `backend/models_db.py` |
| `backend/schemas.py` |

---

### Classes sans docstring (D101)

| Fichier | Classe |
|---|---|
| `backend/database.py:17` | `Base` |
| `backend/schemas.py:6` | `AccidentInput` |
| `backend/schemas.py:17` | `PredictionResponse` |
| `backend/schemas.py:41` | `Config` (D106) |

---

### Docstring multi-ligne mal formatee (D205/D212)

**Fichier :** `backend/features.py:129-134`

La docstring de `_get_sun_times()` n'a pas de ligne vide entre le resume et la description, et le resume ne commence pas a la premiere ligne.

---

### Absence de docstrings dans le module ML

**Fichier :** `ML/ml_config.py` - Aucune documentation sur les constantes ni leur usage.

---

## 6. Code mort et code smells

### Fichier `main.py` racine inutile

**Fichier :** `main.py`

Ce fichier ne sert a rien. Il a ete genere automatiquement par `uv init` et n'est utilise nulle part.

---

### `GaugeConfig` partiellement inutilise

**Fichier :** `front/styles/theme.py:22-28`

Les constantes `GaugeConfig.STEPS`, `GaugeConfig.THRESHOLD_VALUE` et `GaugeConfig.BAR_THICKNESS` sont definies mais jamais utilisees. Le fichier `charts.py` duplique ces valeurs en dur dans `create_gauge()`.

---

### Import `Union` inutilise

**Fichier :** `ML/functions/display_metrics.py:28`

`Union` est importe mais jamais utilise.

---

### Import `create_gauge` re-exporte mais inutile

**Fichier :** `front/components/__init__.py:3`

`create_gauge` est re-exporte depuis le package `components` mais aucun module externe ne l'importe directement depuis `components`. Il est utilise uniquement en interne par `result.py`.

---

### Etat global mutable avec `global`

**Fichier :** `backend/model.py:26-28`

L'utilisation de `global` pour stocker l'etat du modele est un anti-pattern :
- Non thread-safe
- Difficile a tester (pas d'injection de dependances)
- Couplage fort

---

### Attributs mutables de classe sans `ClassVar`

**Fichier :** `front/styles/theme.py:22, 36`

---

### `dict()` au lieu de `{}`

**Fichier :** `front/styles/theme.py:36`

---

### `str(e)` dans f-string au lieu d'un flag de conversion

**Fichier :** `front/app.py:61`

---

## 7. Architecture et Docker

### Versions Python incompatibles

| Composant | Version requise |
|---|---|
| Racine (`pyproject.toml`) | `>=3.14` |
| Backend (`backend/pyproject.toml`) | `==3.12.*` |
| Frontend (`front/pyproject.toml`) | `>=3.11` |
| Dockerfiles | Python 3.12 (image `uv:python3.12`) |

La racine exige Python 3.14+ alors que le backend est strictement 3.12. Ces versions sont contradictoires.

---

### Dockerfile frontend - commande Streamlit incorrecte

**Fichier :** `front/Dockerfile:18`

`0.0.0.0` est passe comme argument positionnel a Streamlit, pas comme `--server.address`.

---

### `uv.lock` non copie dans les Dockerfiles

**Fichier :** `backend/Dockerfile:10`, `front/Dockerfile:8`

Sans copier `uv.lock`, les builds ne sont pas reproductibles. Les versions des dependances peuvent varier entre les builds.

---

### Pas de healthcheck pour le frontend

**Fichier :** `docker-compose.yml`

Le backend et la base de donnees ont des healthchecks, mais le service frontend n'en a pas.

---

### Port PostgreSQL expose en production

**Fichier :** `docker-compose.yml:12-13`

Le port de la base de donnees est expose sur la machine hote. En production, seuls les services internes au reseau Docker devraient y acceder.

---

### Volume partage inutilement

**Fichier :** `docker-compose.yml:42, 68`

Le volume `backend_storage` est monte a la fois sur le backend et le frontend. Le frontend n'a probablement pas besoin d'acceder au stockage du backend.

---

### Pas de tests

Aucun fichier de test (`test_*.py`, `*_test.py`, `conftest.py`) n'existe dans le projet. La commande `pytest` n'a rien a executer.

---

## Reponses aux questions de reflexion

### Le code est-il maintenable ?

**Partiellement.** La structure en composants (backend/front/ML) est claire, mais :
- L'absence de tests rend toute modification risquee
- L'etat global dans `model.py` complique les tests unitaires
- Les credentials en dur rendent le deploiement fragile
- Les versions Python incompatibles entre composants sont un piege
- l'architecture n'est pas adaptée à la maintenabilité du projet

### Le code est-il securise ?

**Non.** Les credentials en clair dans le code source et le docker-compose sont le probleme principal. L'exception silencieuse dans `features.py` et le cache non borne sont des risques supplementaires.

### Le code est-il bien documente ?

**Partiellement.** Les fonctions metier principales ont des docstrings, mais 6 modules sur 6 dans le backend n'ont pas de docstring de module. Plusieurs classes publiques (schemas Pydantic) n'ont pas de docstring.

### Comment detecter ces problemes automatiquement ?

| Outil | Problemes detectes |
|---|---|
| `ruff` | Formatage, imports, conventions, code mort |
| `mypy` | Erreurs de typage, annotations manquantes |
| `bandit` | Vulnerabilites de securite (credentials en dur) |
| `pytest` + `coverage` | Absence de tests, code non couvert |
| `hadolint` | Problemes dans les Dockerfiles |
| `trivy` / `grype` | Vulnerabilites dans les images Docker |

### A quel moment les executer ?

1. **En local** : pre-commit hooks (`ruff`, `mypy`)
2. **En CI/CD** : a chaque push/PR (`ruff`, `mypy`, `pytest`, `bandit`)
3. **Avant le merge** : gate quality obligatoire
4. **En continu** : scan de securite des images Docker

### Comment empecher ces problemes a l'avenir ?

1. **Pre-commit hooks** : Installer `pre-commit` avec ruff + mypy
2. **CI pipeline** : Bloquer les PR qui ne passent pas le linting
3. **Configuration ruff/mypy** : Ajouter `[tool.ruff]` et `[tool.mypy]` dans `pyproject.toml`
4. **Templates `.env.example`** : Documenter les variables d'environnement sans exposer les valeurs
5. **Tests obligatoires** : Couverture minimale de 80% en gate CI
6. **Dependabot / Renovate** : Mises a jour automatiques des dependances
