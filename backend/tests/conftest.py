"""
Fixtures partagées pour les tests pytest.

Architecture MVC:
- Fixtures pour le client HTTP (test des routes/contrôleurs)
- Mocks pour la base de données et le modèle ML
- Données de test réutilisables
"""

from collections.abc import AsyncIterator, Iterator
from datetime import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient


# ---------------------------------------------------------------------------
# Fixtures: Données de test
# ---------------------------------------------------------------------------
@pytest.fixture
def valid_accident_input() -> dict[str, Any]:
    """Données d'entrée valides pour une prédiction."""
    return {
        "date": "2024-06-15",
        "heure": "08:30",
        "departement": "75",
        "agg": True,
        "vma": 50,
        "impl_vehicule_leger": True,
        "impl_poids_lourd": False,
        "impl_pieton": False,
    }


@pytest.fixture
def valid_features() -> dict[str, Any]:
    """Features dérivées valides."""
    return {
        "est_nuit": 0,
        "est_heure_pointe": 1,
        "jour_semaine": 5,
        "est_weekend": 1,
        "agg": 1,
        "vma": 50,
        "impl_vehicule_leger": 1,
        "impl_poids_lourd": 0,
        "impl_pieton": 0,
    }


@pytest.fixture
def mock_prediction_result() -> dict[str, Any]:
    """Résultat de prédiction mocké."""
    return {
        "gravite": 0,
        "probabilite_grave": 0.2345,
        "label": "Non grave",
    }


@pytest.fixture
def mock_sun_times() -> dict[str, time]:
    """Horaires lever/coucher du soleil mockés."""
    return {
        "sunrise": time(6, 30),
        "sunset": time(21, 0),
    }


# ---------------------------------------------------------------------------
# Fixtures: Mocks base de données
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Session de base de données mockée."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


# ---------------------------------------------------------------------------
# Fixtures: Client de test FastAPI
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_model() -> MagicMock:
    """Modèle ML mocké."""
    model = MagicMock()
    model.predict.return_value = [0]
    model.predict_proba.return_value = [[0.7655, 0.2345]]
    return model


@pytest.fixture
def test_client(mock_db_session: AsyncMock, mock_model: MagicMock) -> Iterator[TestClient]:
    """Client de test synchrone avec mocks."""
    with (
        patch.dict("os.environ", {"POSTGRES_USER": "test", "POSTGRES_PASSWORD": "test"}),
        patch("database.create_async_engine"),
        patch("database.async_sessionmaker"),
    ):
        from main import app

        # Override de la dépendance DB
        async def override_get_db() -> AsyncIterator[AsyncMock]:
            yield mock_db_session

        from database import get_db

        app.dependency_overrides[get_db] = override_get_db

        # Mock du modèle
        with (
            patch("services.ml_service._model", mock_model),
            patch("services.ml_service._imputer", None),
            patch("services.ml_service._scaler", None),
        ):
            yield TestClient(app)

        app.dependency_overrides.clear()


@pytest.fixture
async def async_client(mock_db_session: AsyncMock, mock_model: MagicMock) -> AsyncIterator[AsyncClient]:
    """Client de test asynchrone avec mocks."""
    with (
        patch.dict("os.environ", {"POSTGRES_USER": "test", "POSTGRES_PASSWORD": "test"}),
        patch("database.create_async_engine"),
        patch("database.async_sessionmaker"),
    ):
        from main import app

        async def override_get_db() -> AsyncIterator[AsyncMock]:
            yield mock_db_session

        from database import get_db

        app.dependency_overrides[get_db] = override_get_db

        with (
            patch("services.ml_service._model", mock_model),
            patch("services.ml_service._imputer", None),
            patch("services.ml_service._scaler", None),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                yield client

        app.dependency_overrides.clear()
