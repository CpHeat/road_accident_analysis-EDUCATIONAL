"""
Tests du module de feature engineering.

Ces tests vérifient la logique métier de dérivation des features
à partir des données brutes.
"""

from datetime import date, time
from unittest.mock import AsyncMock, patch

import pytest

from features import (
    DEPARTEMENTS,
    _get_day_of_week,
    _get_departement_coords,
    _is_night,
    _is_rush_hour,
    _is_weekend,
    derive_all_features,
)


class TestDepartementCoords:
    """Tests de récupération des coordonnées départementales."""

    def test_valid_metropolitan_departement(self) -> None:
        """Département métropolitain valide."""
        lat, lon = _get_departement_coords("75")

        assert lat == 48.9
        assert lon == 2.3

    def test_valid_corse_departement(self) -> None:
        """Département corse valide."""
        lat, lon = _get_departement_coords("2A")

        assert lat == 41.9
        assert lon == 8.7

    def test_valid_dom_departement(self) -> None:
        """Département DOM valide."""
        lat, lon = _get_departement_coords("971")

        assert lat == 16.2
        assert lon == -61.5

    def test_invalid_departement(self) -> None:
        """Département invalide lève une erreur."""
        with pytest.raises(ValueError, match="Département inconnu"):
            _get_departement_coords("999")

    def test_all_departements_have_coords(self) -> None:
        """Tous les départements ont des coordonnées valides."""
        for _, coords in DEPARTEMENTS.items():
            assert "lat" in coords
            assert "lon" in coords
            assert -90 <= coords["lat"] <= 90
            assert -180 <= coords["lon"] <= 180


class TestIsNight:
    """Tests de détection de la nuit."""

    def test_daytime(self) -> None:
        """En journée (entre lever et coucher)."""
        result = _is_night(hour=12, minute=0, sunrise=time(6, 0), sunset=time(21, 0))

        assert result == 0

    def test_nighttime_before_sunrise(self) -> None:
        """Nuit avant le lever du soleil."""
        result = _is_night(hour=5, minute=30, sunrise=time(6, 0), sunset=time(21, 0))

        assert result == 1

    def test_nighttime_after_sunset(self) -> None:
        """Nuit après le coucher du soleil."""
        result = _is_night(hour=22, minute=0, sunrise=time(6, 0), sunset=time(21, 0))

        assert result == 1

    def test_exactly_at_sunrise(self) -> None:
        """Exactement au lever du soleil (jour)."""
        result = _is_night(hour=6, minute=0, sunrise=time(6, 0), sunset=time(21, 0))

        assert result == 0

    def test_exactly_at_sunset(self) -> None:
        """Exactement au coucher du soleil (nuit)."""
        result = _is_night(hour=21, minute=0, sunrise=time(6, 0), sunset=time(21, 0))

        assert result == 1


class TestIsRushHour:
    """Tests de détection des heures de pointe."""

    @pytest.mark.parametrize("hour", [7, 8])
    def test_morning_rush_hour(self, hour: int) -> None:
        """Heure de pointe du matin (7h-9h)."""
        assert _is_rush_hour(hour) == 1

    @pytest.mark.parametrize("hour", [17, 18])
    def test_evening_rush_hour(self, hour: int) -> None:
        """Heure de pointe du soir (17h-19h)."""
        assert _is_rush_hour(hour) == 1

    @pytest.mark.parametrize("hour", [6, 9, 12, 16, 19, 23])
    def test_not_rush_hour(self, hour: int) -> None:
        """Hors heures de pointe."""
        assert _is_rush_hour(hour) == 0


class TestDayOfWeek:
    """Tests de calcul du jour de la semaine."""

    def test_monday(self) -> None:
        """Lundi = 0."""
        assert _get_day_of_week(date(2024, 6, 10)) == 0

    def test_sunday(self) -> None:
        """Dimanche = 6."""
        assert _get_day_of_week(date(2024, 6, 16)) == 6

    def test_saturday(self) -> None:
        """Samedi = 5."""
        assert _get_day_of_week(date(2024, 6, 15)) == 5


class TestIsWeekend:
    """Tests de détection du weekend."""

    @pytest.mark.parametrize(
        "date_obj",
        [
            date(2024, 6, 15),  # Samedi
            date(2024, 6, 16),  # Dimanche
        ],
    )
    def test_weekend(self, date_obj: date) -> None:
        """Samedi et dimanche sont le weekend."""
        assert _is_weekend(date_obj) == 1

    @pytest.mark.parametrize(
        "date_obj",
        [
            date(2024, 6, 10),  # Lundi
            date(2024, 6, 12),  # Mercredi
            date(2024, 6, 14),  # Vendredi
        ],
    )
    def test_weekday(self, date_obj: date) -> None:
        """Du lundi au vendredi n'est pas le weekend."""
        assert _is_weekend(date_obj) == 0


class TestDeriveAllFeatures:
    """Tests de la fonction principale de dérivation des features."""

    @pytest.mark.asyncio
    async def test_derive_features_complete(self, mock_sun_times: dict[str, time]) -> None:
        """Dérivation complète des features."""
        with patch("features._get_sun_times", new_callable=AsyncMock, return_value=mock_sun_times):
            features = await derive_all_features(
                date_str="2024-06-15",
                heure_str="08:30",
                departement="75",
                agg=True,
                vma=50,
                impl_vehicule_leger=True,
                impl_poids_lourd=False,
                impl_pieton=True,
            )

        assert features["est_nuit"] == 0
        assert features["est_heure_pointe"] == 1
        assert features["jour_semaine"] == 5
        assert features["est_weekend"] == 1
        assert features["agg"] == 1
        assert features["vma"] == 50
        assert features["impl_vehicule_leger"] == 1
        assert features["impl_poids_lourd"] == 0
        assert features["impl_pieton"] == 1

    @pytest.mark.asyncio
    async def test_derive_features_night(self, mock_sun_times: dict[str, time]) -> None:
        """Dérivation avec heure de nuit."""
        with patch("features._get_sun_times", new_callable=AsyncMock, return_value=mock_sun_times):
            features = await derive_all_features(
                date_str="2024-06-15",
                heure_str="23:00",
                departement="75",
                agg=False,
                vma=130,
                impl_vehicule_leger=False,
                impl_poids_lourd=True,
                impl_pieton=False,
            )

        assert features["est_nuit"] == 1
        assert features["est_heure_pointe"] == 0
        assert features["agg"] == 0
        assert features["vma"] == 130

    @pytest.mark.asyncio
    async def test_derive_features_invalid_departement(self) -> None:
        """Département invalide lève une erreur."""
        with pytest.raises(ValueError, match="Département inconnu"):
            await derive_all_features(
                date_str="2024-06-15",
                heure_str="08:30",
                departement="999",
                agg=True,
                vma=50,
                impl_vehicule_leger=True,
                impl_poids_lourd=False,
                impl_pieton=False,
            )

    @pytest.mark.asyncio
    async def test_feature_keys_order(self, mock_sun_times: dict[str, time]) -> None:
        """Toutes les features attendues sont présentes."""
        expected_keys = {
            "est_nuit",
            "est_heure_pointe",
            "jour_semaine",
            "est_weekend",
            "agg",
            "vma",
            "impl_vehicule_leger",
            "impl_poids_lourd",
            "impl_pieton",
        }

        with patch("features._get_sun_times", new_callable=AsyncMock, return_value=mock_sun_times):
            features = await derive_all_features(
                date_str="2024-06-15",
                heure_str="12:00",
                departement="75",
                agg=True,
                vma=50,
                impl_vehicule_leger=True,
                impl_poids_lourd=False,
                impl_pieton=False,
            )

        assert set(features.keys()) == expected_keys
