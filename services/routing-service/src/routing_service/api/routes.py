"""Endpoint de ruta de menor costo (contrato en docs/03-api.md)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from routing_service.api.dependencies import provide_find_cheapest_route
from routing_service.api.errors import to_app_error
from routing_service.api.trace import TraceStepOut, trace_out
from routing_service.application.routes import FindCheapestRoute, RouteReport
from routing_service.core.security import Role, require_roles
from routing_service.domain.errors import DomainError

router = APIRouter(prefix="/api/v1", tags=["routes"])

NODE_ID_PATTERN = r"^[A-Z0-9_-]{1,32}$"


class LegOut(BaseModel):
    edge_id: str
    source: str = Field(serialization_alias="from")
    target: str = Field(serialization_alias="to")
    weight: float


class FewestHopsOut(BaseModel):
    path: list[str]
    hops: int
    cost: float


class CheapestRouteOut(BaseModel):
    found: bool
    origin: str
    destination: str
    path: list[str]
    total_cost: float | None
    hops: int | None
    legs: list[LegOut]
    fewest_hops: FewestHopsOut | None
    message: str
    trace: list[TraceStepOut] | None


def _to_response(report: RouteReport, *, with_trace: bool) -> CheapestRouteOut:
    return CheapestRouteOut(
        found=report.found,
        origin=report.origin,
        destination=report.destination,
        path=list(report.path),
        total_cost=report.total_cost,
        hops=report.hops,
        legs=[LegOut(**vars(leg)) for leg in report.legs],
        fewest_hops=(FewestHopsOut(**vars(report.fewest_hops)) if report.fewest_hops else None),
        message=report.message,
        trace=trace_out(report.trace) if with_trace else None,
    )


@router.get(
    "/routes/cheapest",
    response_model=CheapestRouteOut,
    summary="Ruta de menor costo entre dos nodos (Dijkstra)",
)
def get_cheapest_route(
    use_case: Annotated[FindCheapestRoute, Depends(provide_find_cheapest_route)],
    _role: Annotated[Role, Depends(require_roles(Role.COORDINATOR, Role.OPERATOR))],
    origin: Annotated[str, Query(pattern=NODE_ID_PATTERN)],
    destination: Annotated[str, Query(pattern=NODE_ID_PATTERN)],
    trace: bool = False,
) -> CheapestRouteOut:
    try:
        report = use_case.execute(origin, destination, trace=trace)
    except DomainError as exc:
        raise to_app_error(exc) from exc
    return _to_response(report, with_trace=trace)
