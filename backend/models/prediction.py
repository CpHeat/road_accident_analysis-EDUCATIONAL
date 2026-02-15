from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base


class Prediction(Base):
    """Table des prédictions effectuées."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Données d'entrée brutes
    input_date: Mapped[str] = mapped_column(String(10), nullable=False)
    input_heure: Mapped[str] = mapped_column(String(5), nullable=False)
    input_departement: Mapped[str] = mapped_column(String(3), nullable=False)
    input_agg: Mapped[bool] = mapped_column(nullable=False)
    input_vma: Mapped[int] = mapped_column(Integer, nullable=False)
    input_impl_vehicule_leger: Mapped[bool] = mapped_column(nullable=False)
    input_impl_poids_lourd: Mapped[bool] = mapped_column(nullable=False)
    input_impl_pieton: Mapped[bool] = mapped_column(nullable=False)

    # Features dérivées (stockées en JSON)
    features: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Résultat de la prédiction
    gravite: Mapped[int] = mapped_column(Integer, nullable=False)
    probabilite_grave: Mapped[float] = mapped_column(Float, nullable=False)
    label: Mapped[str] = mapped_column(String(20), nullable=False)
