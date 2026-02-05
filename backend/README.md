# Backend - Prédiction Accidents Routiers

API REST pour prédire la gravité des accidents routiers (grave/non grave).

## Stack

- **FastAPI** + **CatBoost** (classifieur binaire)
- Python 3.12

## Installation

```bash
uv sync
```

## Lancement

```bash
uv run uvicorn main:app --reload
```

API disponible sur `http://localhost:8000/docs`

## Endpoints

| Route | Méthode | Description |
|-------|---------|-------------|
| `/` | GET | Accueil |
| `/health` | GET | Status |
| `/predict` | POST | Prédiction gravité |

## Exemple requête `/predict`

```json
{
  "date": "2024-12-15",
  "heure": "18:30",
  "departement": "75",
  "agglomeration": true,
  "vitesse_max_autorisee": 50,
  "vehicule_leger": true,
  "poids_lourd": false,
  "pieton": false
}
```

## Réponse

```json
{
  "gravite": 0,
  "probabilite": 0.23,
  "label": "Non grave"
}
```