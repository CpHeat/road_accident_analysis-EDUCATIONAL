"""
Tests des routes API (contrôleurs).

Ces tests vérifient le comportement des endpoints HTTP
conformément au pattern MVC (Controllers).
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


class TestRootEndpoint:
    """Tests de l'endpoint racine."""

    @pytest.mark.asyncio
    async def test_root_returns_message(self, async_client: AsyncClient) -> None:
        """GET / retourne le message de bienvenue."""
        response = await async_client.get("/")

        assert response.status_code == 200
        assert response.json() == {"message": "API prête à prédire"}


class TestHealthEndpoint:
    """Tests de l'endpoint health check."""

    @pytest.mark.asyncio
    async def test_health_returns_healthy(self, async_client: AsyncClient) -> None:
        """GET /health retourne le statut healthy."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestPredictEndpoint:
    """Tests de l'endpoint de prédiction."""

    @pytest.mark.asyncio
    async def test_predict_success(
        self,
        async_client: AsyncClient,
        valid_accident_input: dict[str, Any],
        mock_db_session: AsyncMock,
    ) -> None:
        """POST /predict avec données valides retourne une prédiction."""
        # Mock de l'ID généré par la BDD
        mock_prediction = MagicMock()
        mock_prediction.id = 42

        async def mock_refresh(obj: Any) -> None:
            obj.id = 42

        mock_db_session.refresh = mock_refresh

        with patch("features._get_sun_times", new_callable=AsyncMock) as mock_sun:
            from datetime import time

            mock_sun.return_value = {"sunrise": time(6, 0), "sunset": time(21, 0)}

            response = await async_client.post("/predict", json=valid_accident_input)

        assert response.status_code == 200
        data = response.json()
        assert "gravite" in data
        assert "probabilite_grave" in data
        assert "label" in data
        assert data["gravite"] in [0, 1]
        assert 0.0 <= data["probabilite_grave"] <= 1.0
        assert data["label"] in ["Grave", "Non grave"]

    @pytest.mark.asyncio
    async def test_predict_invalid_date_format(
        self,
        async_client: AsyncClient,
        valid_accident_input: dict[str, Any],
    ) -> None:
        """POST /predict avec date invalide retourne 422."""
        valid_accident_input["date"] = "15-06-2024"

        response = await async_client.post("/predict", json=valid_accident_input)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_predict_invalid_heure_format(
        self,
        async_client: AsyncClient,
        valid_accident_input: dict[str, Any],
    ) -> None:
        """POST /predict avec heure invalide retourne 422."""
        valid_accident_input["heure"] = "8h30"

        response = await async_client.post("/predict", json=valid_accident_input)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_predict_vma_out_of_range(
        self,
        async_client: AsyncClient,
        valid_accident_input: dict[str, Any],
    ) -> None:
        """POST /predict avec VMA hors bornes retourne 422."""
        valid_accident_input["vma"] = 150

        response = await async_client.post("/predict", json=valid_accident_input)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_predict_missing_field(
        self,
        async_client: AsyncClient,
        valid_accident_input: dict[str, Any],
    ) -> None:
        """POST /predict avec champ manquant retourne 422."""
        del valid_accident_input["departement"]

        response = await async_client.post("/predict", json=valid_accident_input)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_predict_invalid_departement(
        self,
        async_client: AsyncClient,
        valid_accident_input: dict[str, Any],
    ) -> None:
        """POST /predict avec département invalide retourne 400."""
        valid_accident_input["departement"] = "999"

        with patch("features._get_sun_times", new_callable=AsyncMock):
            response = await async_client.post("/predict", json=valid_accident_input)

        assert response.status_code == 400
        assert "Département inconnu" in response.json()["detail"]


class TestPredictionsEndpoint:
    """Tests de l'endpoint d'historique des prédictions."""

    @pytest.mark.asyncio
    async def test_get_predictions_empty(
        self,
        async_client: AsyncClient,
        mock_db_session: AsyncMock,
    ) -> None:
        """GET /predictions sans données retourne liste vide."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        response = await async_client.get("/predictions")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_predictions_with_limit(
        self,
        async_client: AsyncClient,
        mock_db_session: AsyncMock,
    ) -> None:
        """GET /predictions avec limit respecte la pagination."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        response = await async_client.get("/predictions?limit=10&offset=5")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_predictions_limit_validation(
        self,
        async_client: AsyncClient,
    ) -> None:
        """GET /predictions avec limit invalide retourne 422."""
        response = await async_client.get("/predictions?limit=0")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_predictions_limit_max(
        self,
        async_client: AsyncClient,
    ) -> None:
        """GET /predictions avec limit > 1000 retourne 422."""
        response = await async_client.get("/predictions?limit=1001")

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_predictions_negative_offset(
        self,
        async_client: AsyncClient,
    ) -> None:
        """GET /predictions avec offset négatif retourne 422."""
        response = await async_client.get("/predictions?offset=-1")

        assert response.status_code == 422
