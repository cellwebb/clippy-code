"""Custom exceptions replacing openai.* error types."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


class LLMError(Exception):
    """Base class for LLM errors."""

    pass


class AuthenticationError(LLMError):
    """API key invalid or missing (401)."""

    pass


class RateLimitError(LLMError):
    """Rate limit exceeded (429)."""

    pass


class APIConnectionError(LLMError):
    """Network/connection error."""

    pass


class APITimeoutError(LLMError):
    """Request timed out."""

    pass


class BadRequestError(LLMError):
    """Invalid request (400)."""

    pass


class PermissionDeniedError(LLMError):
    """Permission denied (403)."""

    pass


class NotFoundError(LLMError):
    """Resource not found (404)."""

    pass


class ConflictError(LLMError):
    """Conflict error (409)."""

    pass


class UnprocessableEntityError(LLMError):
    """Unprocessable entity (422)."""

    pass


class InternalServerError(LLMError):
    """Server error (5xx)."""

    pass


def raise_for_status(response: httpx.Response) -> None:
    """Convert HTTP errors to typed exceptions.

    Args:
        response: httpx Response object

    Raises:
        AuthenticationError: For 401 responses
        PermissionDeniedError: For 403 responses
        NotFoundError: For 404 responses
        ConflictError: For 409 responses
        UnprocessableEntityError: For 422 responses
        RateLimitError: For 429 responses
        BadRequestError: For other 4xx responses
        InternalServerError: For 5xx responses
    """
    if response.is_success:
        return

    status = response.status_code
    text = response.text[:500]  # Truncate for readability

    if status == 401:
        raise AuthenticationError(f"Authentication failed: {text}")
    elif status == 403:
        raise PermissionDeniedError(f"Permission denied: {text}")
    elif status == 404:
        raise NotFoundError(f"Not found: {text}")
    elif status == 409:
        raise ConflictError(f"Conflict: {text}")
    elif status == 422:
        raise UnprocessableEntityError(f"Unprocessable entity: {text}")
    elif status == 429:
        raise RateLimitError(f"Rate limit exceeded: {text}")
    elif status == 400:
        raise BadRequestError(f"Bad request: {text}")
    elif status >= 500:
        raise InternalServerError(f"Server error ({status}): {text}")
    elif status >= 400:
        raise LLMError(f"HTTP {status}: {text}")
