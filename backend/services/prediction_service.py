import logging
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Prediction
from schemas import AccidentInput, PredictionResponse
from services.feature_service import derive_all_features
from services.ml_service import predict

logger = logging.getLogger(__name__)


async def create_prediction(data: AccidentInput, db: AsyncSession) -> PredictionResponse:
    """
    Orchestre la création d'une prédiction complète.

    1. Dérive les features depuis les données brutes
    2. Appelle le modèle ML
    3. Persiste le résultat en base de données
    """
    logger.info("=" * 50)
    logger.info("Nouvelle requête de prédiction reçue")
    logger.info(f"Données d'entrée: {data.model_dump()}")

    # Dériver les features
    logger.info("Dérivation des features...")
    features: dict[str, Any] = await derive_all_features(
        date_str=data.date,
        heure_str=data.heure,
        departement=data.departement,
        agg=data.agg,
        vma=data.vma,
        impl_vehicule_leger=data.impl_vehicule_leger,
        impl_poids_lourd=data.impl_poids_lourd,
        impl_pieton=data.impl_pieton,
    )
    logger.info(f"Features dérivées: {features}")

    # Prédiction ML
    logger.info("Appel du modèle de prédiction...")
    result = predict(features)
    logger.info(f"Résultat de la prédiction: {result}")

    # Persistance en base de données
    prediction_record = Prediction(
        input_date=data.date,
        input_heure=data.heure,
        input_departement=data.departement,
        input_agg=data.agg,
        input_vma=data.vma,
        input_impl_vehicule_leger=data.impl_vehicule_leger,
        input_impl_poids_lourd=data.impl_poids_lourd,
        input_impl_pieton=data.impl_pieton,
        features=features,
        gravite=result["gravite"],
        probabilite_grave=result["probabilite_grave"],
        label=result["label"],
    )
    db.add(prediction_record)
    await db.commit()
    await db.refresh(prediction_record)
    logger.info(f"Prédiction sauvegardée avec ID: {prediction_record.id}")
    logger.info("=" * 50)

    return PredictionResponse(id=prediction_record.id, **result)


async def get_prediction_history(db: AsyncSession, limit: int, offset: int) -> Sequence[Prediction]:
    """Récupère l'historique des prédictions avec pagination."""
    query = select(Prediction).order_by(Prediction.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()
