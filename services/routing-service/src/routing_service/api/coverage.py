"""Endpoint de Feature 2: cobertura de una base (contrato en docs/03-api.md)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from routing_service.api.dependencies import provide_check_coverage
from routing_service.application.coverage import CheckCoverage, CoverageReport
from routing_service.core.errors import AppError
from routing_service.core.security import Role, require_roles
from routing_service.domain.errors import DomainError
from routing_service.domain.graph import NodeType
from routing_service.domain.results import TraceStep

router = APIRouter(prefix="/api/v1", tags=["coverage"])

NODE_ID_PATTERN = r"^[A-Z0-9_-]{1,32}$"

_STATUS_BY_CODE = {
    "ORIGIN_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "ZONE_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "INVALID_ORIGIN": status.HTTP_422_UNPROCESSABLE_CONTENT,
}


class ReachableNodeOut(BaseModel):
    node_id: str
    type: NodeType
    hops: int


class ZoneCoverageOut(BaseModel):
    id: str
    covered: bool
    hops: int | None
    message: str


class TraceStepOut(BaseModel):
    step: int
    action: str
    node: str | None
    data: dict[str, Any]


class CoverageOut(BaseModel):
    base: str
    reachable: list[ReachableNodeOut]
    unreachable_zones: list[str]
    zone: ZoneCoverageOut | None
    trace: list[TraceStepOut] | None


def _trace_out(steps: tuple[TraceStep, ...]) -> list[TraceStepOut]:
    return [TraceStepOut(step=s.step, action=s.action, node=s.node, data=s.data) for s in steps]


def _to_response(report: CoverageReport, *, with_trace: bool) -> CoverageOut:
    return CoverageOut(
        base=report.base,
        reachable=[ReachableNodeOut(**vars(item)) for item in report.reachable],
        unreachable_zones=list(report.unreachable_zones),
        zone=ZoneCoverageOut(**vars(report.zone)) if report.zone else None,
        trace=_trace_out(report.trace) if with_trace else None,
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
        raise AppError(
            exc.code,
            exc.message,
            _STATUS_BY_CODE.get(exc.code, status.HTTP_400_BAD_REQUEST),
            exc.details,
        ) from exc
    return _to_response(report, with_trace=trace)
