from datetime import datetime

from pydantic import BaseModel, Field


class AccidentInput(BaseModel):
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", examples=["2024-01-15"])
    heure: str = Field(..., pattern=r"^\d{2}:\d{2}$", examples=["08:30"])
    departement: str = Field(..., examples=["75", "2A", "971"])
    agg: bool = Field(..., description="En agglomération")
    vma: int = Field(..., ge=20, le=130, description="Vitesse maximale autorisée")
    impl_vehicule_leger: bool = Field(..., description="Véhicule léger impliqué")
    impl_poids_lourd: bool = Field(..., description="Poids lourd impliqué")
    impl_pieton: bool = Field(..., description="Piéton impliqué")


class PredictionResponse(BaseModel):
    id: int | None = Field(None, description="ID de la prédiction en base")
    gravite: int = Field(..., ge=0, le=1)
    probabilite_grave: float = Field(..., ge=0.0, le=1.0)
    label: str


class PredictionHistory(BaseModel):
    """Historique complet d'une prédiction."""
    id: int
    created_at: datetime
    input_date: str
    input_heure: str
    input_departement: str
    input_agg: bool
    input_vma: int
    input_impl_vehicule_leger: bool
    input_impl_poids_lourd: bool
    input_impl_pieton: bool
    features: dict
    gravite: int
    probabilite_grave: float
    label: str

    class Config:
        from_attributes = True