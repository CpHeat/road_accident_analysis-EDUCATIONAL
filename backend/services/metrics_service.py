"""Service de métriques Prometheus pour l'API de prédiction d'accidents."""

import time

from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

# ============================================================================
# Timestamp de démarrage
# ============================================================================
_start_time: float = 0.0

# ============================================================================
# Métriques custom
# ============================================================================

APP_UPTIME = Gauge(
    "app_uptime_seconds",
    "Temps écoulé depuis le démarrage de l'application",
)

ML_PREDICTIONS_TOTAL = Counter(
    "ml_predictions_total",
    "Nombre total de prédictions ML",
    ["result"],
)

ML_PREDICTION_PROBABILITY = Histogram(
    "ml_prediction_probability",
    "Distribution des probabilités de gravité prédites",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

ML_INFERENCE_DURATION = Histogram(
    "ml_inference_duration_seconds",
    "Durée de l'inférence du modèle ML (sans I/O)",
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

ML_ERRORS_TOTAL = Counter(
    "ml_errors_total",
    "Nombre total d'erreurs ML",
    ["error_type"],
)

HTTP_ERRORS_TOTAL = Counter(
    "http_errors_total",
    "Nombre total d'erreurs HTTP",
    ["status_code", "endpoint"],
)


# ============================================================================
# Fonctions helpers
# ============================================================================


def init_uptime() -> None:
    """Enregistre le timestamp de démarrage de l'application."""
    global _start_time
    _start_time = time.time()


def _update_uptime() -> None:
    """Met à jour la gauge d'uptime."""
    if _start_time > 0:
        APP_UPTIME.set(time.time() - _start_time)


def record_prediction(gravite: int, probabilite: float) -> None:
    """Enregistre une prédiction dans les métriques."""
    label = "grave" if gravite == 1 else "non_grave"
    ML_PREDICTIONS_TOTAL.labels(result=label).inc()
    ML_PREDICTION_PROBABILITY.observe(probabilite)


def record_inference_time(duration: float) -> None:
    """Enregistre le temps d'inférence du modèle."""
    ML_INFERENCE_DURATION.observe(duration)


def record_ml_error(error_type: str) -> None:
    """Enregistre une erreur ML."""
    ML_ERRORS_TOTAL.labels(error_type=error_type).inc()


def record_http_error(status_code: int, endpoint: str) -> None:
    """Enregistre une erreur HTTP."""
    HTTP_ERRORS_TOTAL.labels(status_code=str(status_code), endpoint=endpoint).inc()


# ============================================================================
# Instrumentator Prometheus
# ============================================================================


def get_instrumentator() -> Instrumentator:
    """Retourne l'instrumentator Prometheus configuré."""
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        excluded_handlers=["/metrics"],
    )

    # Callback pour mettre à jour l'uptime à chaque scrape
    instrumentator.add(
        lambda info: _update_uptime(),
    )

    return instrumentator
