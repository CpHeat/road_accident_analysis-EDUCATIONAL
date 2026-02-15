"""Modèle de données du formulaire."""

import re
from dataclasses import dataclass
from typing import Any


def format_heure(heure: str) -> str:
    """Formate l'heure au format HH:MM."""
    match = re.match(r"(\d{1,2})[h:](\d{1,2})", heure.strip())
    if match:
        h, m = int(match.group(1)), int(match.group(2))
        return f"{h:02d}:{m:02d}"
    return heure


@dataclass
class FormData:
    """Données du formulaire."""

    date: str
    heure: str
    departement: str
    agg: bool
    vma: int
    impl_vehicule_leger: bool
    impl_poids_lourd: bool
    impl_pieton: bool

    def to_payload(self) -> dict[str, Any]:
        """Convertit en payload pour l'API."""
        return {
            "date": self.date,
            "heure": format_heure(self.heure),
            "departement": self.departement,
            "agg": self.agg,
            "vma": self.vma,
            "impl_vehicule_leger": self.impl_vehicule_leger,
            "impl_poids_lourd": self.impl_poids_lourd,
            "impl_pieton": self.impl_pieton,
        }

    def is_valid(self) -> bool:
        """Vérifie si le formulaire est valide."""
        return bool(self.departement)
