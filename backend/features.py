from datetime import datetime, date, time
from typing import Any

import httpx

# Table des centroïdes des départements français
DEPARTEMENTS: dict[str, dict[str, float]] = {
    # Métropole
    "01": {"lat": 46.0, "lon": 5.3},      # Ain
    "02": {"lat": 49.5, "lon": 3.6},      # Aisne
    "03": {"lat": 46.4, "lon": 3.2},      # Allier
    "04": {"lat": 44.1, "lon": 6.2},      # Alpes-de-Haute-Provence
    "05": {"lat": 44.7, "lon": 6.3},      # Hautes-Alpes
    "06": {"lat": 43.9, "lon": 7.2},      # Alpes-Maritimes
    "07": {"lat": 44.7, "lon": 4.4},      # Ardèche
    "08": {"lat": 49.6, "lon": 4.6},      # Ardennes
    "09": {"lat": 42.9, "lon": 1.5},      # Ariège
    "10": {"lat": 48.3, "lon": 4.1},      # Aube
    "11": {"lat": 43.2, "lon": 2.4},      # Aude
    "12": {"lat": 44.3, "lon": 2.6},      # Aveyron
    "13": {"lat": 43.5, "lon": 5.1},      # Bouches-du-Rhône
    "14": {"lat": 49.1, "lon": -0.4},     # Calvados
    "15": {"lat": 45.0, "lon": 2.7},      # Cantal
    "16": {"lat": 45.7, "lon": 0.2},      # Charente
    "17": {"lat": 45.8, "lon": -0.8},     # Charente-Maritime
    "18": {"lat": 47.1, "lon": 2.4},      # Cher
    "19": {"lat": 45.3, "lon": 1.9},      # Corrèze
    "21": {"lat": 47.4, "lon": 4.8},      # Côte-d'Or
    "22": {"lat": 48.4, "lon": -3.0},     # Côtes-d'Armor
    "23": {"lat": 46.1, "lon": 2.0},      # Creuse
    "24": {"lat": 45.1, "lon": 0.7},      # Dordogne
    "25": {"lat": 47.2, "lon": 6.4},      # Doubs
    "26": {"lat": 44.7, "lon": 5.2},      # Drôme
    "27": {"lat": 49.1, "lon": 1.0},      # Eure
    "28": {"lat": 48.3, "lon": 1.3},      # Eure-et-Loir
    "29": {"lat": 48.4, "lon": -4.2},     # Finistère
    "30": {"lat": 44.0, "lon": 4.1},      # Gard
    "31": {"lat": 43.4, "lon": 1.2},      # Haute-Garonne
    "32": {"lat": 43.7, "lon": 0.4},      # Gers
    "33": {"lat": 44.8, "lon": -0.6},     # Gironde
    "34": {"lat": 43.6, "lon": 3.5},      # Hérault
    "35": {"lat": 48.1, "lon": -1.7},     # Ille-et-Vilaine
    "36": {"lat": 46.8, "lon": 1.6},      # Indre
    "37": {"lat": 47.3, "lon": 0.7},      # Indre-et-Loire
    "38": {"lat": 45.3, "lon": 5.6},      # Isère
    "39": {"lat": 46.7, "lon": 5.7},      # Jura
    "40": {"lat": 43.9, "lon": -0.8},     # Landes
    "41": {"lat": 47.6, "lon": 1.3},      # Loir-et-Cher
    "42": {"lat": 45.7, "lon": 4.2},      # Loire
    "43": {"lat": 45.1, "lon": 3.9},      # Haute-Loire
    "44": {"lat": 47.3, "lon": -1.7},     # Loire-Atlantique
    "45": {"lat": 47.9, "lon": 2.3},      # Loiret
    "46": {"lat": 44.6, "lon": 1.6},      # Lot
    "47": {"lat": 44.3, "lon": 0.5},      # Lot-et-Garonne
    "48": {"lat": 44.5, "lon": 3.5},      # Lozère
    "49": {"lat": 47.4, "lon": -0.6},     # Maine-et-Loire
    "50": {"lat": 49.0, "lon": -1.3},     # Manche
    "51": {"lat": 49.0, "lon": 4.2},      # Marne
    "52": {"lat": 48.1, "lon": 5.1},      # Haute-Marne
    "53": {"lat": 48.1, "lon": -0.8},     # Mayenne
    "54": {"lat": 48.8, "lon": 6.2},      # Meurthe-et-Moselle
    "55": {"lat": 49.0, "lon": 5.4},      # Meuse
    "56": {"lat": 47.8, "lon": -2.8},     # Morbihan
    "57": {"lat": 49.0, "lon": 6.6},      # Moselle
    "58": {"lat": 47.1, "lon": 3.5},      # Nièvre
    "59": {"lat": 50.4, "lon": 3.2},      # Nord
    "60": {"lat": 49.4, "lon": 2.5},      # Oise
    "61": {"lat": 48.6, "lon": 0.1},      # Orne
    "62": {"lat": 50.5, "lon": 2.3},      # Pas-de-Calais
    "63": {"lat": 45.7, "lon": 3.1},      # Puy-de-Dôme
    "64": {"lat": 43.3, "lon": -0.8},     # Pyrénées-Atlantiques
    "65": {"lat": 43.1, "lon": 0.1},      # Hautes-Pyrénées
    "66": {"lat": 42.6, "lon": 2.5},      # Pyrénées-Orientales
    "67": {"lat": 48.6, "lon": 7.5},      # Bas-Rhin
    "68": {"lat": 47.9, "lon": 7.2},      # Haut-Rhin
    "69": {"lat": 45.9, "lon": 4.6},      # Rhône
    "70": {"lat": 47.6, "lon": 6.2},      # Haute-Saône
    "71": {"lat": 46.6, "lon": 4.5},      # Saône-et-Loire
    "72": {"lat": 47.9, "lon": 0.2},      # Sarthe
    "73": {"lat": 45.5, "lon": 6.4},      # Savoie
    "74": {"lat": 46.0, "lon": 6.4},      # Haute-Savoie
    "75": {"lat": 48.9, "lon": 2.3},      # Paris
    "76": {"lat": 49.6, "lon": 1.0},      # Seine-Maritime
    "77": {"lat": 48.6, "lon": 2.9},      # Seine-et-Marne
    "78": {"lat": 48.8, "lon": 1.9},      # Yvelines
    "79": {"lat": 46.5, "lon": -0.4},     # Deux-Sèvres
    "80": {"lat": 49.9, "lon": 2.3},      # Somme
    "81": {"lat": 43.8, "lon": 2.2},      # Tarn
    "82": {"lat": 44.0, "lon": 1.3},      # Tarn-et-Garonne
    "83": {"lat": 43.5, "lon": 6.2},      # Var
    "84": {"lat": 44.0, "lon": 5.2},      # Vaucluse
    "85": {"lat": 46.7, "lon": -1.3},     # Vendée
    "86": {"lat": 46.6, "lon": 0.5},      # Vienne
    "87": {"lat": 45.9, "lon": 1.2},      # Haute-Vienne
    "88": {"lat": 48.2, "lon": 6.4},      # Vosges
    "89": {"lat": 47.8, "lon": 3.6},      # Yonne
    "90": {"lat": 47.6, "lon": 6.9},      # Territoire de Belfort
    "91": {"lat": 48.5, "lon": 2.2},      # Essonne
    "92": {"lat": 48.8, "lon": 2.2},      # Hauts-de-Seine
    "93": {"lat": 48.9, "lon": 2.5},      # Seine-Saint-Denis
    "94": {"lat": 48.8, "lon": 2.5},      # Val-de-Marne
    "95": {"lat": 49.1, "lon": 2.2},      # Val-d'Oise
    # CORSE
    "2A": {"lat": 41.9, "lon": 8.7},  # Corse-du-Sud
    "2B": {"lat": 42.4, "lon": 9.2},  # Haute-Corse
    # DOM-TOM
    "971": {"lat": 16.2, "lon": -61.5},   # Guadeloupe
    "972": {"lat": 14.6, "lon": -61.0},   # Martinique
    "973": {"lat": 4.0, "lon": -53.0},    # Guyane
    "974": {"lat": -21.1, "lon": 55.5},   # La Réunion
    "976": {"lat": -12.8, "lon": 45.2},   # Mayotte
}

# Encodage des régions (ordre alphabétique = LabelEncoder)
REGION_ENCODING = {
    "centre": 0,
    "dom_tom": 1,
    "nord": 2,
    "sud": 3,
}

# Cache pour les horaires de lever/coucher du soleil
_sun_times_cache: dict[str, dict[str, time]] = {}


def _get_departement_coords(departement: str) -> tuple[float, float]:
    """Retourne les coordonnées (lat, lon) du centroïde d'un département."""
    if departement not in DEPARTEMENTS:
        raise ValueError(f"Département inconnu: {departement}")
    coords = DEPARTEMENTS[departement]
    return coords["lat"], coords["lon"]


def _convert_departement_code(departement: str) -> int:
    """Convertit le code département en numérique (2A→200, 2B→201)."""
    if departement == "2A":
        return 200
    elif departement == "2B":
        return 201
    else:
        return int(departement)


def get_region_str(latitude: float, longitude: float) -> str:
    """Détermine la région géographique depuis les coordonnées."""
    if longitude < -50 or longitude > 40:
        return "dom_tom"
    elif latitude >= 47:
        return "nord"
    elif latitude >= 44:
        return "centre"
    else:
        return "sud"


def _get_region_encoded(latitude: float, longitude: float) -> int:
    """Retourne la région encodée (compatible LabelEncoder)."""
    region_str = get_region_str(latitude, longitude)
    return REGION_ENCODING[region_str]


async def _get_sun_times(
    date_str: str, latitude: float, longitude: float
) -> dict[str, time]:
    """
    Récupère les heures de lever/coucher du soleil via API externe.
    Utilise un cache en mémoire pour éviter les appels répétés.

    Fallback: 6h-22h si l'API échoue.
    """
    cache_key = f"{date_str}_{latitude:.1f}_{longitude:.1f}"

    if cache_key in _sun_times_cache:
        return _sun_times_cache[cache_key]

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "https://api.sunrise-sunset.org/json",
                params={
                    "lat": latitude,
                    "lng": longitude,
                    "date": date_str,
                    "formatted": 0,
                },
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "OK":
                results = data["results"]
                # Parse ISO format: "2024-01-15T07:30:00+00:00"
                sunrise = datetime.fromisoformat(
                    results["sunrise"].replace("Z", "+00:00")
                ).time()
                sunset = datetime.fromisoformat(
                    results["sunset"].replace("Z", "+00:00")
                ).time()

                sun_times = {"sunrise": sunrise, "sunset": sunset}
                _sun_times_cache[cache_key] = sun_times
                return sun_times
    except Exception:
        pass

    # Fallback: 6h-22h
    fallback = {"sunrise": time(6, 0), "sunset": time(22, 0)}
    _sun_times_cache[cache_key] = fallback
    return fallback


def _is_night(hour: int, minute: int, sunrise: time, sunset: time) -> int:
    """Détermine si c'est la nuit (avant lever ou après coucher du soleil)."""
    current = time(hour, minute)
    if current < sunrise or current >= sunset:
        return 1
    return 0


def _is_rush_hour(hour: int) -> int:
    """Détermine si c'est l'heure de pointe (7-9h ou 17-19h)."""
    if 7 <= hour < 9 or 17 <= hour < 19:
        return 1
    return 0


def _get_day_of_week(date_obj: date) -> int:
    """Retourne le jour de la semaine (0=lundi, 6=dimanche)."""
    return date_obj.weekday()


def _is_weekend(date_obj: date) -> int:
    """Détermine si c'est le weekend (samedi ou dimanche)."""
    return 1 if date_obj.weekday() >= 5 else 0


async def derive_all_features(
    date_str: str,
    heure_str: str,
    departement: str,
    agg: bool,
    vma: int,
    impl_vehicule_leger: bool,
    impl_poids_lourd: bool,
    impl_pieton: bool,
) -> dict[str, Any]:
    """
    Dérive toutes les features à partir des entrées brutes.

    Retourne un dictionnaire avec les 11 features dans l'ordre attendu par le modèle:
    ['est_nuit', 'est_heure_pointe', 'jour_semaine', 'est_weekend',
     'region', 'dep', 'agg', 'vma',
     'impl_vehicule_leger', 'impl_poids_lourd', 'impl_pieton']
    """
    # Parse date et heure
    date_obj = date.fromisoformat(date_str)
    hour, minute = map(int, heure_str.split(":"))

    # Coordonnées du département
    latitude, longitude = _get_departement_coords(departement)

    # Horaires du soleil
    sun_times = await _get_sun_times(date_str, latitude, longitude)

    return {
        "est_nuit": _is_night(hour, minute, sun_times["sunrise"], sun_times["sunset"]),
        "est_heure_pointe": _is_rush_hour(hour),
        "jour_semaine": _get_day_of_week(date_obj),
        "est_weekend": _is_weekend(date_obj),
        "region": _get_region_encoded(latitude, longitude),
        "dep": _convert_departement_code(departement),
        "agg": 1 if agg else 0,
        "vma": vma,
        "impl_vehicule_leger": 1 if impl_vehicule_leger else 0,
        "impl_poids_lourd": 1 if impl_poids_lourd else 0,
        "impl_pieton": 1 if impl_pieton else 0,
    }