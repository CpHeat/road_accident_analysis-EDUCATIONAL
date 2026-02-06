"""
Tests des schémas Pydantic (validation des données).

Ces tests vérifient la couche de validation des entrées/sorties
conformément au pattern MVC (Models).
"""

from typing import Any

import pytest
from pydantic import ValidationError


class TestAccidentInputSchema:
    """Tests de validation du schéma AccidentInput."""

    def test_valid_input(self, valid_accident_input: dict[str, Any]) -> None:
        """Entrée valide acceptée."""
        from schemas import AccidentInput

        accident = AccidentInput(**valid_accident_input)

        assert accident.date == "2024-06-15"
        assert accident.heure == "08:30"
        assert accident.departement == "75"
        assert accident.agg is True
        assert accident.vma == 50

    def test_invalid_date_format(self, valid_accident_input: dict[str, Any]) -> None:
        """Format de date invalide rejeté."""
        from schemas import AccidentInput

        valid_accident_input["date"] = "15/06/2024"

        with pytest.raises(ValidationError) as exc_info:
            AccidentInput(**valid_accident_input)

        assert "date" in str(exc_info.value)

    def test_invalid_heure_format(self, valid_accident_input: dict[str, Any]) -> None:
        """Format d'heure invalide rejeté."""
        from schemas import AccidentInput

        valid_accident_input["heure"] = "8:30"

        with pytest.raises(ValidationError) as exc_info:
            AccidentInput(**valid_accident_input)

        assert "heure" in str(exc_info.value)

    def test_vma_below_minimum(self, valid_accident_input: dict[str, Any]) -> None:
        """VMA inférieure au minimum rejetée."""
        from schemas import AccidentInput

        valid_accident_input["vma"] = 10

        with pytest.raises(ValidationError) as exc_info:
            AccidentInput(**valid_accident_input)

        assert "vma" in str(exc_info.value)

    def test_vma_above_maximum(self, valid_accident_input: dict[str, Any]) -> None:
        """VMA supérieure au maximum rejetée."""
        from schemas import AccidentInput

        valid_accident_input["vma"] = 200

        with pytest.raises(ValidationError) as exc_info:
            AccidentInput(**valid_accident_input)

        assert "vma" in str(exc_info.value)

    def test_missing_required_field(self, valid_accident_input: dict[str, Any]) -> None:
        """Champ requis manquant rejeté."""
        from schemas import AccidentInput

        del valid_accident_input["departement"]

        with pytest.raises(ValidationError) as exc_info:
            AccidentInput(**valid_accident_input)

        assert "departement" in str(exc_info.value)


class TestPredictionResponseSchema:
    """Tests de validation du schéma PredictionResponse."""

    def test_valid_response(self) -> None:
        """Réponse valide acceptée."""
        from schemas import PredictionResponse

        response = PredictionResponse(id=1, gravite=0, probabilite_grave=0.2345, label="Non grave")

        assert response.id == 1
        assert response.gravite == 0
        assert response.probabilite_grave == 0.2345
        assert response.label == "Non grave"

    def test_response_without_id(self) -> None:
        """Réponse sans ID (optionnel) acceptée."""
        from schemas import PredictionResponse

        response = PredictionResponse(gravite=1, probabilite_grave=0.8765, label="Grave")

        assert response.id is None
        assert response.gravite == 1

    def test_invalid_gravite_value(self) -> None:
        """Gravité hors bornes rejetée."""
        from schemas import PredictionResponse

        with pytest.raises(ValidationError) as exc_info:
            PredictionResponse(gravite=2, probabilite_grave=0.5, label="Test")

        assert "gravite" in str(exc_info.value)

    def test_invalid_probabilite_value(self) -> None:
        """Probabilité hors bornes rejetée."""
        from schemas import PredictionResponse

        with pytest.raises(ValidationError) as exc_info:
            PredictionResponse(gravite=0, probabilite_grave=1.5, label="Test")

        assert "probabilite_grave" in str(exc_info.value)


class TestPredictionHistorySchema:
    """Tests de validation du schéma PredictionHistory."""

    def test_valid_history(self) -> None:
        """Historique valide accepté."""
        from datetime import datetime

        from schemas import PredictionHistory

        history = PredictionHistory(
            id=1,
            created_at=datetime.now(),
            input_date="2024-06-15",
            input_heure="08:30",
            input_departement="75",
            input_agg=True,
            input_vma=50,
            input_impl_vehicule_leger=True,
            input_impl_poids_lourd=False,
            input_impl_pieton=False,
            features={"est_nuit": 0, "vma": 50},
            gravite=0,
            probabilite_grave=0.2345,
            label="Non grave",
        )

        assert history.id == 1
        assert history.input_departement == "75"
        assert history.features["vma"] == 50
