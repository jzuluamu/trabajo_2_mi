from typing import Annotated

from fastapi import APIRouter, Depends

from network_service.core.security import Role, require_roles

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/whoami", summary="Rol asociado a la API key enviada")
def whoami(
    role: Annotated[Role, Depends(require_roles(Role.COORDINATOR, Role.OPERATOR, Role.INTERNAL))],
) -> dict[str, str]:
    return {"role": role.value}
