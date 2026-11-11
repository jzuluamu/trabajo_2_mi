"""Endpoint para elegir la base disponible de menor costo."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from routing_service.api.dependencies import provide_find_best_attention
from routing_service.api.errors import to_app_error
from routing_service.api.trace import TraceStepOut, trace_out
from routing_service.application.attention import AttentionReport, FindBestAttention
from routing_service.core.security import Role, require_roles
from routing_service.domain.errors import DomainError

router = APIRouter(prefix="/api/v1", tags=["attention"])

NODE_ID_PATTERN = r"^[A-Z0-9_-]{1,32}$"


class TechnicianOut(BaseModel):
    id: str
    name: str


class BestBaseOut(BaseModel):
    base: str
    technicians: list[TechnicianOut]
    path: list[str]
    total_cost: float
    hops: int


class AlternativeBaseOut(BaseModel):
    base: str
    total_cost: float
    hops: int


class BestAttentionOut(BaseModel):
    zone: str
    found: bool
    best: BestBaseOut | None
    alternatives: list[AlternativeBaseOut]
    message: str
    trace: list[TraceStepOut] | None


def _to_response(report: AttentionReport, *, with_trace: bool) -> BestAttentionOut:
    best = report.best
    return BestAttentionOut(
        zone=report.zone,
        found=report.found,
        best=(
            BestBaseOut(
                base=best.base,
                technicians=[TechnicianOut(**vars(item)) for item in best.technicians],
                path=list(best.path),
                total_cost=best.total_cost,
                hops=best.hops,
            )
            if best
            else None
        ),
        alternatives=[AlternativeBaseOut(**vars(item)) for item in report.alternatives],
        message=report.message,
        trace=trace_out(report.trace) if with_trace else None,
    )


@router.get(
    "/attention/best",
    response_model=BestAttentionOut,
    summary="Mejor base disponible para atender una zona",
)
def get_best_attention(
    use_case: Annotated[FindBestAttention, Depends(provide_find_best_attention)],
    _role: Annotated[Role, Depends(require_roles(Role.COORDINATOR, Role.OPERATOR))],
    zone: Annotated[str, Query(pattern=NODE_ID_PATTERN)],
    trace: bool = False,
) -> BestAttentionOut:
    try:
        report = use_case.execute(zone, trace=trace)
    except DomainError as exc:
        raise to_app_error(exc) from exc
    return _to_response(report, with_trace=trace)
