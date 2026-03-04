# Rapport de Stress Test

## Contexte

Test de charge réalisé avec **Locust** sur l'API de prédiction d'accidents, monitoré en temps réel via le dashboard Grafana (Prometheus + métriques custom).

**Configuration du test :**
- 200 utilisateurs simultanés
- Débit observé : ~10 requêtes/s
- Endpoints testés : `POST /predict` (principal), `GET /predictions`, `GET /health`

## Résultats

| Métrique | Valeur observée |
|---|---|
| Temps de réponse moyen `/predict` | **~60s** |
| Feature engineering (API sunrise-sunset) | **>8s / requête** |
| Écriture DB (PostgreSQL) | **jusqu'à 3.5s** |
| Inférence ML | **<50ms** |

## Analyse des goulots d'étranglement

Le dashboard "Cycle de vie d'une requête" montre clairement la décomposition :

1. **Feature engineering (~8s)** — Le principal goulot. L'appel HTTP synchrone à l'API externe `sunrise-sunset.org` pour déterminer si l'accident a lieu de nuit bloque chaque requête. Sous charge, les timeouts (5s) et la latence réseau s'accumulent.

2. **Écriture DB (~3.5s)** — PostgreSQL sature sous la charge concurrente. Les `commit` + `refresh` séquentiels créent de la contention sur les connexions.

3. **Inférence ML (<50ms)** — Le modèle XGBoost est performant et ne pose aucun problème.

## Résultats après correction (remplacement sunrise-sunset.org par `astral`)

| Métrique | Avant | Après |
|---|---|---|
| Temps de réponse P50 `/predict` | ~60s | **150ms** |
| Temps de réponse P95 `/predict` | >60s | **900ms** |
| Feature engineering | >8s | **<5ms** |

Le remplacement de l'appel API externe par un calcul local a réduit le temps de réponse de **60s à moins d'1s**, soit une amélioration d'un facteur ~60x.

Le test a ensuite été poussé à **300 utilisateurs simultanés / 120 req/s** :

| Métrique | Valeur |
|---|---|
| Temps de réponse P50 | **~500ms** |
| Temps de réponse P95 | **<2000ms** |
| Débit soutenu | **120 req/s** |

L'API reste stable et performante sous une charge 12x supérieure au test initial.

## Pistes d'amélioration

### 1. Remplacer l'API sunrise-sunset par la librairie `astral`

Le goulot principal est l'appel HTTP externe à `sunrise-sunset.org` qui ajoute >8s par requête sous charge. La librairie Python `astral` calcule les horaires de lever/coucher du soleil localement à partir des coordonnées GPS et de la date, sans aucun appel réseau. Cela réduirait le feature engineering de **8s → <10ms**.

### 2. Rate limiting

Protéger l'API contre la surcharge en limitant le nombre de requêtes concurrentes par client (ex: via `slowapi` ou un middleware custom). Cela empêcherait la saturation des ressources (connexions DB, threads) et garantirait un temps de réponse stable pour les requêtes acceptées, au lieu d'une dégradation progressive pour tout le monde.

### 3. Scaling horizontal

Déployer plusieurs instances du backend derrière un load balancer (ex: Nginx ou Traefik) pour répartir la charge. Avec Docker Compose, cela se fait via `docker compose up --scale accident-ml-backend=N`. Combiné aux deux premières optimisations, cela permettrait de supporter un trafic bien supérieur à 10 req/s.
