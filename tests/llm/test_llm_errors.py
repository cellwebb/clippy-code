"""Tests for LLM errors."""

from unittest.mock import Mock

import pytest

from clippy.llm.errors import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InternalServerError,
    LLMError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
    raise_for_status,
)


class TestLLMErrors:
    """Test LLM error classes."""

    def test_api_connection_error(self):
        """Test APIConnectionError."""
        error = APIConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert "Connection failed" in str(error)

    def test_api_timeout_error(self):
        """Test APITimeoutError."""
        error = APITimeoutError("Request timed out")
        assert str(error) == "Request timed out"
        assert "timed out" in str(error)

    def test_bad_request_error(self):
        """Test BadRequestError."""
        error = BadRequestError("Bad request")
        assert str(error) == "Bad request"

    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"
        assert isinstance(error, LLMError)

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Invalid API key")
        assert str(error) == "Invalid API key"
        assert "Invalid API key" in str(error)

    def test_raise_for_status_success(self):
        """Test raise_for_status with successful response."""
        mock_response = Mock()
        mock_response.is_success = True

        # Should not raise any exception
        raise_for_status(mock_response)

    def test_raise_for_status_400(self):
        """Test raise_for_status with 400 status."""
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 400
        mock_response.text = "Bad request"

        with pytest.raises(BadRequestError):
            raise_for_status(mock_response)

    def test_raise_for_status_401(self):
        """Test raise_for_status with 401 status."""
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with pytest.raises(AuthenticationError):
            raise_for_status(mock_response)

    def test_raise_for_status_403(self):
        """Test raise_for_status with 403 status."""
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 403
        mock_response.text = "Forbidden"

        with pytest.raises(PermissionDeniedError):
            raise_for_status(mock_response)

    def test_raise_for_status_404(self):
        """Test raise_for_status with 404 status."""
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 404
        mock_response.text = "Not found"

        with pytest.raises(NotFoundError):
            raise_for_status(mock_response)

    def test_raise_for_status_409(self):
        """Test raise_for_status with 409 status."""
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 409
        mock_response.text = "Conflict"

        with pytest.raises(ConflictError):
            raise_for_status(mock_response)

    def test_raise_for_status_422(self):
        """Test raise_for_status with 422 status."""
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 422
        mock_response.text = "Unprocessable entity"

        with pytest.raises(UnprocessableEntityError):
            raise_for_status(mock_response)

    def test_raise_for_status_429(self):
        """Test raise_for_status with 429 status."""
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"

        with pytest.raises(RateLimitError):
            raise_for_status(mock_response)

    def test_raise_for_status_500(self):
        """Test raise_for_status with 500 status."""
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 500
        mock_response.text = "Server error"

        with pytest.raises(InternalServerError):
            raise_for_status(mock_response)

    def test_raise_for_status_other_4xx(self):
        """Test raise_for_status with other 4xx status."""
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 418
        mock_response.text = "I'm a teapot"

        with pytest.raises(LLMError):
            raise_for_status(mock_response)

    def test_raise_for_status_with_response_text(self):
        """Test raise_for_status includes response text."""
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 400
        mock_response.text = "Invalid request format"

        with pytest.raises(BadRequestError) as exc_info:
            raise_for_status(mock_response)

        assert "Invalid request format" in str(exc_info.value)

    def test_api_connection_error_inheritance(self):
        """Test APIConnectionError inheritance."""
        error = APIConnectionError("test")
        assert isinstance(error, Exception)
        assert isinstance(error, LLMError)

    def test_api_timeout_error_inheritance(self):
        """Test APITimeoutError inheritance."""
        error = APITimeoutError("test")
        assert isinstance(error, Exception)
        assert isinstance(error, LLMError)

    def test_bad_request_error_inheritance(self):
        """Test BadRequestError inheritance."""
        error = BadRequestError("test")
        assert isinstance(error, Exception)
        assert isinstance(error, LLMError)

    def test_rate_limit_error_inheritance(self):
        """Test RateLimitError inheritance."""
        error = RateLimitError("test")
        assert isinstance(error, Exception)
        assert isinstance(error, LLMError)

    def test_authentication_error_inheritance(self):
        """Test AuthenticationError inheritance."""
        error = AuthenticationError("test")
        assert isinstance(error, Exception)
        assert isinstance(error, LLMError)

    def test_error_messages_are_preserved(self):
        """Test that error messages are preserved correctly."""
        messages = [
            ("Connection failed", APIConnectionError),
            ("Request timed out", APITimeoutError),
            ("Bad request", BadRequestError),
            ("Rate limited", RateLimitError),
            ("Auth failed", AuthenticationError),
            ("Permission denied", PermissionDeniedError),
            ("Not found", NotFoundError),
            ("Conflict", ConflictError),
            ("Unprocessable", UnprocessableEntityError),
            ("Server error", InternalServerError),
        ]

        for message, error_class in messages:
            error = error_class(message)
            assert message in str(error)
