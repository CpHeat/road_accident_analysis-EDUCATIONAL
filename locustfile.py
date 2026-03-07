"""Load testing de l'API de prédiction d'accidents avec Locust."""

import random

from locust import HttpUser, between, task

DEPARTEMENTS = [
    "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "21",
    "22", "23", "24", "25", "26", "27", "28", "29", "30", "31",
    "32", "33", "34", "35", "36", "37", "38", "39", "40", "41",
    "42", "43", "44", "45", "46", "47", "48", "49", "50", "51",
    "52", "53", "54", "55", "56", "57", "58", "59", "60", "61",
    "62", "63", "64", "65", "66", "67", "68", "69", "70", "71",
    "72", "73", "74", "75", "76", "77", "78", "79", "80", "81",
    "82", "83", "84", "85", "86", "87", "88", "89", "90", "91",
    "92", "93", "94", "95",
    "2A", "2B",
    "971", "972", "973", "974", "976",
]

VMA_VALUES = [20, 30, 50, 70, 90, 110, 130]


def random_payload() -> dict:
    """Génère un payload AccidentInput aléatoire mais valide."""
    year = random.randint(2017, 2025)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)

    return {
        "date": f"{year}-{month:02d}-{day:02d}",
        "heure": f"{hour:02d}:{minute:02d}",
        "departement": random.choice(DEPARTEMENTS),
        "agg": random.choice([True, False]),
        "vma": random.choice(VMA_VALUES),
        "impl_vehicule_leger": random.choice([True, False]),
        "impl_poids_lourd": random.choice([True, False]),
        "impl_pieton": random.choice([True, False]),
    }


class APIUser(HttpUser):
    """Simule un utilisateur de l'API de prédiction."""

    host = "http://localhost:8000"
    wait_time = between(1, 3)

    @task(1)
    def health_check(self) -> None:
        """Vérifie que l'API est up."""
        self.client.get("/health")

    @task(5)
    def predict(self) -> None:
        """Envoie une requête de prédiction avec des données aléatoires."""
        self.client.post("/predict", json=random_payload())

    @task(2)
    def prediction_history(self) -> None:
        """Récupère l'historique des prédictions."""
        self.client.get("/predictions", params={"limit": 10})
