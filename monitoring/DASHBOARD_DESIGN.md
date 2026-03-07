# Design de mon Dashboard

## Objectif

Superviser les performances et le comportement de l'API de prédiction d'accidents en temps réel.
Le dashboard permet de détecter les dégradations de performance, de suivre la répartition des prédictions
et de comprendre où le temps est consommé dans le cycle de vie complet d'une requête.

## Public cible

L'équipe de développement et d'opérations (DevOps/MLOps) responsable du maintien de l'API en production.

## Métriques clés à afficher

1. **Temps d'inférence ML** (`ml_inference_duration_seconds`) - Pourquoi : identifier les ralentissements du modèle ML, qui est le coeur de l'API
2. **Taux de prédictions graves** (`ml_predictions_total{result="grave"}` / `ml_predictions_total`) - Pourquoi : détecter une dérive du modèle si le ratio grave/non-grave change anormalement
3. **Cycle de vie d'une requête** (`http_request_duration_seconds` vs `ml_inference_duration_seconds`) - Pourquoi : identifier les goulots d'étranglement entre le feature engineering, l'inférence ML et la persistance en base de données
4. **Prédictions (30 min)** (`ml_predictions_total`) - Pourquoi : suivre l'activité récente de l'API et détecter les pics ou chutes de trafic

## Disposition prévue

```
┌─────────────────────────────────────────────────────────────┐
│                    Prédiction - Performance                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│              Durée de prédiction (moyenne)                  │
│              Type : Stat                                    │
│                                                             │
├─────────────────────────┬───────────────────────────────────┤
│                         │                                   │
│   Prédictions (30 min)  │   Taux de prédictions graves (%)  │
│                         │                                   │
│   Type : Stat           │   Type : Stat                     │
│                         │                                   │
├─────────────────────────┴───────────────────────────────────┤
│                                                             │
│   Cycle de vie d'une requête /predict                       │
│   Type : Time series (stacked)                              │
│                                                             │
│   ┌──────────┬───────────────┬──────────┐                   │
│   │ Feature  │  Inférence ML │    DB    │                   │
│   │ eng.     │               │  write   │                   │
│   └──────────┴───────────────┴──────────┘                   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Temps d'inférence ML                                      │
│   Type : Time series                                        │
│   - P50, P95, P99                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Panel 1 : Durée de prédiction

- **Type** : Stat
- **Requête** :
  - `rate(http_request_duration_seconds_sum{handler="/predict"}[5m]) / rate(http_request_duration_seconds_count{handler="/predict"}[5m])`
- **Unité** : secondes
- **Objectif** : vision immédiate du temps moyen d'une prédiction

### Panel 2 : Prédictions (30 min)

- **Type** : Stat
- **Requête** :
  - `sum(increase(ml_predictions_total[30m]))`
- **Unité** : nombre
- **Objectif** : suivre l'activité récente de l'API et détecter les pics ou chutes de trafic

### Panel 3 : Taux de prédictions graves

- **Type** : Stat
- **Requête** :
  - `sum(rate(ml_predictions_total{result="grave"}[5m])) / sum(rate(ml_predictions_total[5m])) * 100`
- **Unité** : pourcentage
- **Seuils d'alerte** : warning si ratio s'écarte de > 20% de la baseline historique

### Panel 4 : Cycle de vie d'une requête /predict

- **Type** : Time series (stacked)
- **Requêtes** :
  - Inférence ML : `rate(ml_inference_duration_seconds_sum[5m]) / rate(ml_inference_duration_seconds_count[5m])`
  - Overhead (feature eng. + DB) : `scalar(rate(http_request_duration_seconds_sum{handler="/predict"}[5m]) / rate(http_request_duration_seconds_count{handler="/predict"}[5m])) - scalar(rate(ml_inference_duration_seconds_sum[5m]) / rate(ml_inference_duration_seconds_count[5m]))`
- **Unité** : secondes
- **Objectif** : visualiser la décomposition du temps par étape pour identifier quel composant (feature engineering via API sunrise-sunset, modèle ML, écriture PostgreSQL) ralentit la requête

### Panel 5 : Temps d'inférence ML

- **Type** : Time series
- **Requêtes** :
  - `histogram_quantile(0.5, rate(ml_inference_duration_seconds_bucket[5m]))` — P50
  - `histogram_quantile(0.95, rate(ml_inference_duration_seconds_bucket[5m]))` — P95
  - `histogram_quantile(0.99, rate(ml_inference_duration_seconds_bucket[5m]))` — P99
- **Unité** : secondes
- **Seuils d'alerte** : warning > 0.5s, critical > 1s
