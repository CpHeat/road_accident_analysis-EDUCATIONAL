import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from controllers.health import router as health_router
from controllers.prediction import router as prediction_router
from database import init_db
from services.ml_service import load_model

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Charge le modèle et initialise la BDD au démarrage."""
    load_model()
    await init_db()
    yield


app = FastAPI(
    title="API Prédiction Accidents",
    description="API prédictive pour la gravité des accidents de la route",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(prediction_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
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
        if error.get("input") is not None:
            logger.error(f"    Valeur reçue: {error.get('input')}")

    logger.error("=" * 50)

    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )
