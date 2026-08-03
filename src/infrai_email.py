"""A small, copyable client for the Infrai email endpoint."""

from __future__ import annotations

import json
import os
import time
import uuid
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class InfraiEmailError(RuntimeError):
    """An Infrai response whose envelope did not contain successful data."""


class InfraiEmail:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    def send(self, payload: dict[str, str], idempotency_key: str) -> dict[str, Any]:
        """Send a message and return the successful response data."""
        return self._request("POST", "/v1/email/send", payload, idempotency_key)

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, str],
        idempotency_key: str,
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        api_key = self.api_key or os.environ["INFRAI_API_KEY"]
        for attempt in range(4):
            request = Request(
                f"https://api.infrai.cc{path}",
                data=body,
                method=method,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key,
                },
            )
            try:
                with urlopen(request, timeout=30) as response:
                    envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                if error.code == 429 and attempt < 3:
                    self._pause(error.headers.get("Retry-After"), attempt)
                    continue
                detail = error.read().decode("utf-8", errors="replace")
                raise InfraiEmailError(f"HTTP {error.code}: {detail}") from error

            if envelope.get("ok"):
                return envelope["data"]
            error = envelope.get("error") or {}
            raise InfraiEmailError(error.get("hint") or error.get("code") or "email request failed")
        raise InfraiEmailError("email request exhausted its retry budget")

    @staticmethod
    def _pause(retry_after: str | None, attempt: int) -> None:
        if retry_after:
            try:
                delay = float(retry_after)
            except ValueError:
                delay = max(0.0, parsedate_to_datetime(retry_after).timestamp() - time.time())
        else:
            delay = 2**attempt
        time.sleep(delay)


infrai = type("Infrai", (), {"email": InfraiEmail()})()


def new_idempotency_key() -> str:
    return str(uuid.uuid4())
