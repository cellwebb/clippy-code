"""Simple tests for LLM HTTP client utilities."""

from unittest.mock import Mock, patch

import httpx
import pytest

from clippy.llm.http_client import create_client, post_with_retry


class TestHttpClientSimple:
    """Test HTTP client utilities."""

    @patch("clippy.llm.http_client.httpx")
    def test_create_client_basic(self, mock_httpx):
        """Test create_client basic functionality."""
        mock_client = Mock()
        mock_httpx.Client.return_value = mock_client

        client = create_client()

        assert client == mock_client
        mock_httpx.Client.assert_called_once()

    def test_post_with_retry_basic_success(self):
        """Test post_with_retry succeeds on first attempt."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.post.return_value = mock_response

        result = post_with_retry(
            mock_client,
            "https://example.com/api",
            json={"test": "data"},
            headers={"Authorization": "Bearer token"},
        )

        assert result == mock_response
        mock_client.post.assert_called_once()

    def test_post_with_retry_preserves_parameters(self):
        """Test post_with_retry passes all parameters correctly."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.post.return_value = mock_response

        result = post_with_retry(
            mock_client,
            "https://example.com/api",
            json={"key": "value"},
            headers={"Content-Type": "application/json"},
        )

        assert result == mock_response
        mock_client.post.assert_called_once_with(
            "https://example.com/api",
            json={"key": "value"},
            headers={"Content-Type": "application/json"},
        )

    def test_post_with_retry_retry_on_failure(self):
        """Test post_with_retry retries on failure."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200

        # First call fails with connect error, second succeeds
        mock_client.post.side_effect = [httpx.ConnectError("Connection failed"), mock_response]

        result = post_with_retry(
            mock_client,
            "https://example.com/api",
            json={"test": "data"},
            headers={"Content-Type": "application/json"},
        )

        assert result == mock_response
        assert mock_client.post.call_count == 2

    def test_post_with_retry_max_retries_exceeded(self):
        """Test post_with_retry raises exception after max retries (3 by default)."""
        mock_client = Mock()
        mock_client.post.side_effect = httpx.ConnectError("Connection failed")

        with pytest.raises(httpx.ConnectError):
            post_with_retry(
                mock_client,
                "https://example.com/api",
                json={"test": "data"},
                headers={"Content-Type": "application/json"},
            )

        # Should have tried 3 times (default max retries)
        assert mock_client.post.call_count == 3
