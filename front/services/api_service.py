"""Service de communication avec l'API backend."""

import os
from typing import Any

import requests

API_URL = os.getenv("API_URL", "http://localhost:8000")


def predict(payload: dict[str, Any]) -> dict[str, Any]:
    """Envoie une prédiction à l'API et retourne le résultat."""
    response = requests.post(f"{API_URL}/predict", json=payload, timeout=10)
    response.raise_for_status()
    return response.json()
