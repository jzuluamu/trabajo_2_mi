"""Endpoint de Feature 2: cobertura de una base (contrato en docs/03-api.md)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from routing_service.api.dependencies import provide_check_coverage
from routing_service.api.errors import to_app_error
from routing_service.api.trace import TraceStepOut, trace_out
from routing_service.application.coverage import CheckCoverage, CoverageReport
from routing_service.core.security import Role, require_roles
from routing_service.domain.errors import DomainError
from routing_service.domain.graph import NodeType

router = APIRouter(prefix="/api/v1", tags=["coverage"])

NODE_ID_PATTERN = r"^[A-Z0-9_-]{1,32}$"


class ReachableNodeOut(BaseModel):
    node_id: str
    type: NodeType
    hops: int


class ZoneCoverageOut(BaseModel):
    id: str
    covered: bool
    hops: int | None
    message: str


class CoverageOut(BaseModel):
    base: str
    reachable: list[ReachableNodeOut]
    unreachable_zones: list[str]
    zone: ZoneCoverageOut | None
    trace: list[TraceStepOut] | None


def _to_response(report: CoverageReport, *, with_trace: bool) -> CoverageOut:
    return CoverageOut(
        base=report.base,
        reachable=[ReachableNodeOut(**vars(item)) for item in report.reachable],
        unreachable_zones=list(report.unreachable_zones),
        zone=ZoneCoverageOut(**vars(report.zone)) if report.zone else None,
        trace=trace_out(report.trace) if with_trace else None,
    )


@router.get(
    "/coverage",
    response_model=CoverageOut,
    summary="Cobertura de una base: zonas alcanzables (BFS)",
)
def get_coverage(
    use_case: Annotated[CheckCoverage, Depends(provide_check_coverage)],
    _role: Annotated[Role, Depends(require_roles(Role.COORDINATOR, Role.OPERATOR))],
    base: Annotated[str, Query(pattern=NODE_ID_PATTERN)],
    zone: Annotated[str | None, Query(pattern=NODE_ID_PATTERN)] = None,
    trace: bool = False,
) -> CoverageOut:
    try:
        report = use_case.execute(base, zone, trace=trace)
    except DomainError as exc:
        raise to_app_error(exc) from exc
    return _to_response(report, with_trace=trace)
