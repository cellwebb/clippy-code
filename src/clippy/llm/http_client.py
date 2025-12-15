"""Shared HTTP client with retry logic."""

from __future__ import annotations

import json as _json
import logging
from collections.abc import Iterator
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# Timeout configuration
DEFAULT_TIMEOUT = httpx.Timeout(
    connect=10.0,
    read=120.0,  # LLM responses can be slow
    write=10.0,
    pool=10.0,
)

# Status codes that should trigger a retry
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class RetryableHTTPError(Exception):
    """Raised for retryable HTTP errors."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(message)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=60),
    retry=retry_if_exception_type((RetryableHTTPError, httpx.ConnectError, httpx.ReadTimeout)),
    reraise=True,
)
def post_with_retry(
    client: httpx.Client,
    url: str,
    json: dict[str, Any],
    headers: dict[str, str],
) -> httpx.Response:
    """POST with automatic retry for transient failures.

    Args:
        client: httpx Client instance
        url: URL to POST to
        json: JSON payload
        headers: HTTP headers

    Returns:
        httpx Response object

    Raises:
        RetryableHTTPError: For retryable status codes (will be retried)
        httpx.HTTPStatusError: For non-retryable errors
    """
    response = client.post(url, json=json, headers=headers)

    if response.status_code in RETRYABLE_STATUS_CODES:
        logger.warning(f"Retryable error {response.status_code} from {url}: {response.text[:200]}")
        raise RetryableHTTPError(response.status_code, response.text)

    return response


def stream_with_retry(
    client: httpx.Client,
    url: str,
    json: dict[str, Any],
    headers: dict[str, str],
) -> Iterator[dict[str, Any]]:
    """POST with streaming response for SSE.

    Args:
        client: httpx Client instance
        url: URL to POST to
        json: JSON payload
        headers: HTTP headers

    Yields:
        Parsed SSE data chunks

    Raises:
        RetryableHTTPError: For retryable status codes
        httpx.HTTPStatusError: For non-retryable errors
    """
    try:
        with client.stream(
            "POST",
            url,
            json=json,
            headers=headers,
        ) as response:
            if response.status_code in RETRYABLE_STATUS_CODES:
                logger.warning(f"Retryable error {response.status_code} from {url}")
                raise RetryableHTTPError(response.status_code, "Retryable status code")

            response.raise_for_status()

            # Parse SSE (Server-Sent Events) stream
            for line in response.iter_lines():
                if line.strip() == "":
                    continue  # Skip empty lines
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    if data.strip() == "[DONE]":
                        break
                    try:
                        parsed = _json.loads(data)
                        yield parsed
                    except _json.JSONDecodeError:
                        logger.warning(f"Failed to parse SSE data: {data}")
                        continue

    except httpx.HTTPStatusError as e:
        if e.response.status_code in RETRYABLE_STATUS_CODES:
            raise RetryableHTTPError(e.response.status_code, e.response.text)
        raise


def create_client(timeout: httpx.Timeout | None = None) -> httpx.Client:
    """Create a configured httpx client.

    Args:
        timeout: Optional custom timeout configuration

    Returns:
        Configured httpx.Client instance
    """
    return httpx.Client(
        timeout=timeout or DEFAULT_TIMEOUT,
        follow_redirects=True,
    )
