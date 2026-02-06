"""
Tests du module de prédiction ML.

Ces tests vérifient le chargement du modèle et la logique de prédiction.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from model import FEATURE_ORDER, predict


class TestFeatureOrder:
    """Tests de l'ordre des features."""

    def test_feature_order_count(self) -> None:
        """9 features attendues."""
        assert len(FEATURE_ORDER) == 9

    def test_feature_order_content(self) -> None:
        """Toutes les features sont présentes."""
        expected = [
            "est_nuit",
            "est_heure_pointe",
            "jour_semaine",
            "est_weekend",
            "agg",
            "vma",
            "impl_vehicule_leger",
            "impl_poids_lourd",
            "impl_pieton",
        ]
        assert FEATURE_ORDER == expected


class TestPredict:
    """Tests de la fonction de prédiction."""

    def test_predict_non_grave(self, valid_features: dict[str, Any], mock_model: MagicMock) -> None:
        """Prédiction non grave (classe 0)."""
        mock_model.predict.return_value = [0]
        mock_model.predict_proba.return_value = [[0.75, 0.25]]

        with patch("model._model", mock_model), patch("model._imputer", None), patch("model._scaler", None):
            result = predict(valid_features)

        assert result["gravite"] == 0
        assert result["probabilite_grave"] == 0.25
        assert result["label"] == "Non grave"

    def test_predict_grave(self, valid_features: dict[str, Any], mock_model: MagicMock) -> None:
        """Prédiction grave (classe 1)."""
        mock_model.predict.return_value = [1]
        mock_model.predict_proba.return_value = [[0.20, 0.80]]

        with patch("model._model", mock_model), patch("model._imputer", None), patch("model._scaler", None):
            result = predict(valid_features)

        assert result["gravite"] == 1
        assert result["probabilite_grave"] == 0.80
        assert result["label"] == "Grave"

    def test_predict_probability_rounding(self, valid_features: dict[str, Any], mock_model: MagicMock) -> None:
        """Probabilité arrondie à 4 décimales."""
        mock_model.predict.return_value = [0]
        mock_model.predict_proba.return_value = [[0.765432, 0.234568]]

        with patch("model._model", mock_model), patch("model._imputer", None), patch("model._scaler", None):
            result = predict(valid_features)

        assert result["probabilite_grave"] == 0.2346

    def test_predict_with_preprocessing(self, valid_features: dict[str, Any]) -> None:
        """Prédiction avec imputer et scaler (CatBoost)."""
        import numpy as np

        mock_model = MagicMock()
        mock_model.predict.return_value = [0]
        mock_model.predict_proba.return_value = [[0.70, 0.30]]

        mock_imputer = MagicMock()
        mock_imputer.transform.return_value = np.array([[0, 1, 5, 1, 1, 50, 1, 0, 0]])

        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = np.array([[0.0, 1.0, 0.5, 1.0, 1.0, 0.4, 1.0, 0.0, 0.0]])

        with (
            patch("model._model", mock_model),
            patch("model._imputer", mock_imputer),
            patch("model._scaler", mock_scaler),
        ):
            result = predict(valid_features)

        mock_imputer.transform.assert_called_once()
        mock_scaler.transform.assert_called_once()
        assert result["gravite"] == 0

    def test_predict_without_predict_proba(self, valid_features: dict[str, Any]) -> None:
        """Prédiction sans méthode predict_proba."""
        mock_model = MagicMock()
        mock_model.predict.return_value = [1]
        del mock_model.predict_proba

        with patch("model._model", mock_model), patch("model._imputer", None), patch("model._scaler", None):
            result = predict(valid_features)

        assert result["gravite"] == 1
        assert result["probabilite_grave"] == 1.0
        assert result["label"] == "Grave"

    def test_predict_returns_expected_keys(self, valid_features: dict[str, Any], mock_model: MagicMock) -> None:
        """Résultat contient les clés attendues."""
        mock_model.predict.return_value = [0]
        mock_model.predict_proba.return_value = [[0.70, 0.30]]

        with patch("model._model", mock_model), patch("model._imputer", None), patch("model._scaler", None):
            result = predict(valid_features)

        assert set(result.keys()) == {"gravite", "probabilite_grave", "label"}


class TestLoadModel:
    """Tests du chargement du modèle."""

    def test_load_model_file_not_found(self) -> None:
        """FileNotFoundError si modèle inexistant."""
        from model import load_model

        with patch("model.MODEL_PATH") as mock_path:
            mock_path.exists.return_value = False
            mock_path.__str__ = lambda x: "/fake/path/model.joblib"

            with pytest.raises(FileNotFoundError):
                load_model()

    def test_load_model_success(self) -> None:
        """Chargement réussi du modèle."""
        from model import load_model

        mock_model = MagicMock()
        mock_data = {"model": mock_model, "imputer": None, "scaler": None}

        with patch("model.MODEL_PATH") as mock_path, patch("model.joblib.load", return_value=mock_data):
            mock_path.exists.return_value = True

            load_model()

        # Vérifie que le modèle est chargé (via get_pipeline)
        from model import get_pipeline

        with patch("model._model", mock_model), patch("model._imputer", None), patch("model._scaler", None):
            model, imputer, scaler = get_pipeline()
            assert model is mock_model
