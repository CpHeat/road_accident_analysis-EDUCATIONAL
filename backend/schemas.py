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
    gravite: int = Field(..., ge=0, le=1)
    probabilite_grave: float = Field(..., ge=0.0, le=1.0)
    label: str