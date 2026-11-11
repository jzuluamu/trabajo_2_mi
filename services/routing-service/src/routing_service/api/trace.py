"""Esquema de salida y conversión común de pasos de traza."""

from typing import Any

from pydantic import BaseModel

from routing_service.domain.results import TraceStep


class TraceStepOut(BaseModel):
    step: int
    action: str
    node: str | None
    data: dict[str, Any]


def trace_out(steps: tuple[TraceStep, ...]) -> list[TraceStepOut]:
    return [
        TraceStepOut(step=item.step, action=item.action, node=item.node, data=item.data)
        for item in steps
    ]
