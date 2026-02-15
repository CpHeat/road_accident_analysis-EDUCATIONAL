import logging
from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Prediction
from schemas import AccidentInput, PredictionHistory, PredictionResponse
from services.prediction_service import create_prediction, get_prediction_history

logger = logging.getLogger(__name__)

router = APIRouter(tags=["predictions"])


@router.post("/predict", response_model=PredictionResponse)
async def predict_accident(data: AccidentInput, db: Annotated[AsyncSession, Depends(get_db)]) -> PredictionResponse:
    """
    Prédit la gravité d'un accident de la route.

    Retourne:
    - id: identifiant de la prédiction en base
    - gravite: 0 (non grave) ou 1 (grave)
    - probabilite_grave: probabilité entre 0 et 1
    - label: "Non grave" ou "Grave"
    """
    try:
        return await create_prediction(data, db)
    except ValueError as e:
        logger.error(f"Erreur de validation: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except FileNotFoundError as e:
        logger.error(f"Modèle non trouvé: {e}")
        raise HTTPException(status_code=503, detail=str(e)) from e


@router.get("/predictions", response_model=list[PredictionHistory])
async def get_predictions(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Sequence[Prediction]:
    """Récupère l'historique des prédictions."""
    return await get_prediction_history(db, limit, offset)
