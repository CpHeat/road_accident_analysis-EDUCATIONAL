# Road Accident Severity Prediction

Application de prédiction de la gravité des accidents routiers, composée d'une API FastAPI, d'un frontend Streamlit et d'une base PostgreSQL, le tout orchestré via Docker Compose.

```
Utilisateur
    │
    ▼
┌──────────────┐      HTTP REST      ┌──────────────┐      ┌────────────┐
│  Streamlit   │  ──────────────────► │   FastAPI    │ ───► │ PostgreSQL │
│  :8501       │                      │   :8000      │      │ :5432      │
└──────────────┘                      └──────┬───────┘      └────────────┘
                                             │
                                      ┌──────┴───────┐
                                      │  ML Model    │
                                      │  (Joblib)    │
                                      └──────────────┘
```

## Lancement rapide

```bash
docker compose up -d
```

L'application est accessible sur `http://localhost:8501` (front) et `http://localhost:8000` (API).

---

## Backend (FastAPI)

**Stack** : FastAPI, SQLAlchemy (async), asyncpg, CatBoost/XGBoost, UV

### Architecture MVC

```
backend/
├── main.py              # Initialisation FastAPI + lifespan (chargement modèle, création tables)
├── database.py          # Configuration PostgreSQL async
├── controllers/
│   ├── health.py        # GET /health
│   └── prediction.py    # POST /predict, GET /predictions
├── services/
│   ├── ml_service.py    # Chargement et inférence du modèle ML
│   ├── feature_service.py  # Feature engineering (9 features dérivées)
│   └── prediction_service.py  # Opérations BDD (historique des prédictions)
├── models/
│   └── prediction.py    # Modèle SQLAlchemy (table predictions)
├── schemas/
│   └── prediction.py    # Schémas Pydantic (validation entrée/sortie)
├── ml_models/
│   └── model_accident_binary_optimized.joblib
├── tests/
│   ├── test_features.py
│   ├── test_model.py
│   ├── test_routes.py
│   └── test_schemas.py
├── Dockerfile
└── pyproject.toml
```

### Endpoints

| Méthode | Route          | Description                              |
|---------|----------------|------------------------------------------|
| GET     | `/health`      | Health check                             |
| POST    | `/predict`     | Prédiction de gravité d'un accident      |
| GET     | `/predictions` | Historique des prédictions (paginé)      |

### Features ML utilisées

`est_nuit`, `est_heure_pointe`, `jour_semaine`, `est_weekend`, `agg`, `vma`, `impl_vehicule_leger`, `impl_poids_lourd`, `impl_pieton`

### Fonctionnement

1. Au démarrage (`lifespan`), le modèle ML est chargé en mémoire et les tables BDD sont créées
2. Une requête `POST /predict` passe par le **controller** qui valide l'entrée (Pydantic), appelle le **feature_service** pour transformer les données brutes en features, puis le **ml_service** pour l'inférence
3. Le résultat est sauvegardé en BDD via **prediction_service** et retourné au client

---

## Frontend (Streamlit)

**Stack** : Streamlit, Plotly, Requests, UV

### Architecture MVC

```
front/
├── app.py               # Point d'entrée Streamlit
├── controllers/
│   └── prediction.py    # Logique de prédiction (orchestre vues et services)
├── services/
│   └── api_service.py   # Client HTTP vers l'API backend
├── views/
│   ├── form.py          # Formulaire de saisie (date, heure, conditions...)
│   ├── result.py        # Affichage du résultat de prédiction
│   └── charts.py        # Visualisations Plotly
├── models/
│   ├── constants.py     # Constantes du formulaire (listes déroulantes)
│   └── form_data.py     # Dataclass des données du formulaire
├── styles/
│   └── theme.py         # CSS personnalisé
├── Dockerfile
└── pyproject.toml
```

### Fonctionnement

1. L'utilisateur remplit le formulaire (date, heure, type de voie, véhicules impliqués...)
2. Le **controller** récupère les données du formulaire et appelle l'**api_service**
3. L'api_service envoie une requête `POST /predict` au backend
4. Le résultat est affiché via les **views** (résultat textuel + graphiques Plotly)

---

## Déploiement Docker

### Services (docker-compose.yml)

| Service              | Image                          | Port  | Rôle              |
|----------------------|--------------------------------|-------|--------------------|
| `accident-ml-db`     | PostgreSQL 17 Alpine           | 5432  | Base de données    |
| `accident-ml-backend`| Python 3.12 + UV               | 8000  | API FastAPI        |
| `accident-ml-front`  | Python 3.12 + UV               | 8501  | Interface Streamlit|

### Caractéristiques

- **Network bridge** `accident-ml` pour la communication inter-conteneurs
- **Volumes persistants** pour PostgreSQL et le stockage backend
- **Health checks** sur la BDD et le backend
- **Dépendances** : le front attend que le backend soit healthy avant de démarrer
- **Utilisateur non-root** (UID 1001) dans les conteneurs pour la sécurité
- **Variables d'environnement** via fichier `.env`

### Push d'images

```bash
# Les images sont taggées dans docker-compose.yml
docker compose build
docker push cpheat/accident-ml-backend:1.0.3
```

---

## Monitoring

### Stack

| Service        | Image                          | Port | Rôle                                    |
|----------------|--------------------------------|------|-----------------------------------------|
| `prometheus`   | prom/prometheus                | 9090 | Collecte et stockage des métriques      |
| `grafana`      | grafana/grafana                | 3000 | Visualisation et dashboards             |
| `node-exporter`| prom/node-exporter             | 9100 | Métriques système (CPU, RAM, disque)    |
| `cadvisor`     | ghcr.io/google/cadvisor        | 8080 | Métriques par container Docker          |
| `uptime-kuma`  | louislam/uptime-kuma           | 3001 | Surveillance de la disponibilité        |

### Métriques exposées par l'API (`/metrics`)

L'API intègre `prometheus-fastapi-instrumentator` et des métriques custom via `prometheus_client`.

**Métriques HTTP (automatiques) :**
- `http_requests_total` — comptage par method/handler/status
- `http_request_duration_seconds` — latence par endpoint
- `http_requests_in_progress` — requêtes en cours de traitement

**Métriques ML (custom) :**
- `ml_predictions_total` — nombre de prédictions par résultat (grave/non_grave)
- `ml_inference_duration_seconds` — temps d'inférence du modèle
- `ml_prediction_probability` — distribution des probabilités prédites
- `ml_errors_total` — erreurs ML par type

**Métriques pipeline (custom) :**
- `feature_engineering_duration_seconds` — temps du feature engineering
- `db_write_duration_seconds` — temps d'écriture en base de données
- `app_uptime_seconds` — uptime de l'application
- `http_errors_total` — erreurs HTTP par status code et endpoint

### Dashboard Grafana

Le dashboard custom décompose le cycle de vie d'une requête `/predict` en trois étapes :
1. **Feature engineering** (appel API sunrise-sunset)
2. **Inférence ML** (modèle XGBoost)
3. **Écriture DB** (PostgreSQL)

Voir [`monitoring/DASHBOARD_DESIGN.md`](monitoring/DASHBOARD_DESIGN.md) pour le détail des panels et requêtes PromQL.

### Tests de charge (Locust)

```bash
uv run locust -f locustfile.py
```

Interface web sur `http://localhost:8089`. Le fichier `locustfile.py` simule des utilisateurs avec des payloads aléatoires réalistes sur les endpoints `/predict`, `/predictions` et `/health`.

Voir [`monitoring/RAPPORT_STRESS_TEST.md`](monitoring/RAPPORT_STRESS_TEST.md) pour les résultats et pistes d'amélioration.