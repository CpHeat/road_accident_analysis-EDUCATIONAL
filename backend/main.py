import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from features import derive_all_features
from model import load_model, predict
from schemas import AccidentInput, PredictionResponse

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Charge le modèle au démarrage de l'application."""
    load_model()
    yield


app = FastAPI(
    title="API Prédiction Accidents",
    description="API prédictive pour la gravité des accidents de la route",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log les erreurs de validation Pydantic (422)."""
    logger.error("=" * 50)
    logger.error("ERREUR DE VALIDATION (422 Unprocessable Entity)")
    logger.error(f"URL: {request.url}")
    logger.error(f"Méthode: {request.method}")

    # Log du body brut si disponible
    try:
        body = await request.body()
        logger.error(f"Body reçu: {body.decode('utf-8')}")
    except Exception:
        logger.error("Impossible de lire le body")

    # Log des erreurs détaillées
    for error in exc.errors():
        logger.error(f"  - Champ: {error.get('loc')}")
        logger.error(f"    Type: {error.get('type')}")
        logger.error(f"    Message: {error.get('msg')}")
        if error.get('input') is not None:
            logger.error(f"    Valeur reçue: {error.get('input')}")

    logger.error("=" * 50)

    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.get("/")
async def root():
    return {"message": "API prête à prédire"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/predict", response_model=PredictionResponse)
async def predict_accident(data: AccidentInput) -> PredictionResponse:
    """
    Prédit la gravité d'un accident de la route.

    Retourne:
    - gravite: 0 (non grave) ou 1 (grave)
    - probabilite_grave: probabilité entre 0 et 1
    - label: "Non grave" ou "Grave"
    """
    logger.info("=" * 50)
    logger.info("Nouvelle requête de prédiction reçue")
    logger.info(f"Données d'entrée: {data.model_dump()}")

    try:
        # Dériver les features
        logger.info("Dérivation des features...")
        features = await derive_all_features(
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

        # Prédiction
        logger.info("Appel du modèle de prédiction...")
        result = predict(features)
        logger.info(f"Résultat de la prédiction: {result}")
        logger.info("=" * 50)

        return PredictionResponse(**result)

    except ValueError as e:
        logger.error(f"Erreur de validation: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        logger.error(f"Modèle non trouvé: {e}")
        raise HTTPException(status_code=503, detail=str(e))