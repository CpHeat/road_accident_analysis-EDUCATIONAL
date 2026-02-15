from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
async def root() -> dict:
    return {"message": "API prête à prédire"}


@router.get("/health")
async def health_check() -> dict:
    return {"status": "healthy"}
