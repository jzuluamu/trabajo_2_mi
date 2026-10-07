"""Cliente HTTP base: traduce respuestas y fallos de red a `ApiClientError` legibles."""

from types import TracebackType
from typing import Any, Self

import httpx


class ApiClientError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class HttpServiceClient:
    service_name = "servicio"

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        timeout: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        headers = {"X-API-Key": api_key} if api_key else {}
        self._client = httpx.Client(
            base_url=base_url, headers=headers, timeout=timeout, transport=transport
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._client.close()

    def health(self) -> dict[str, Any]:
        body: dict[str, Any] = self._request("GET", "/health")
        return body

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.TransportError as exc:
            raise ApiClientError(
                "SERVICE_UNAVAILABLE", f"No fue posible contactar {self.service_name}."
            ) from exc
        if response.status_code == httpx.codes.NO_CONTENT:
            return None
        if response.is_success:
            return response.json()
        raise self._to_error(response)

    @staticmethod
    def _to_error(response: httpx.Response) -> ApiClientError:
        try:
            body = response.json()
        except ValueError:
            body = None
        if not isinstance(body, dict):
            body = {}
        return ApiClientError(
            code=str(body.get("code", f"HTTP_{response.status_code}")),
            message=str(body.get("message", "Respuesta inesperada del servicio.")),
            status_code=response.status_code,
            details=body.get("details") if isinstance(body.get("details"), dict) else {},
        )
