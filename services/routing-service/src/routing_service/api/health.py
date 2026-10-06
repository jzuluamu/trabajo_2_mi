from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Estado del servicio (público)")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "routing-service"}
