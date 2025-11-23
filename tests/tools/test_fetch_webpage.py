"""Tests for fetch_webpage tool."""

from unittest.mock import MagicMock, patch

from clippy.tools.fetch_webpage import fetch_webpage


class TestFetchWebpage:
    """Test cases for fetch_webpage tool."""

    @patch("requests.get")
    def test_fetch_webpage_success(self, mock_get):
        """Test successful webpage fetching."""
        # Mock response
        mock_response = MagicMock()
        mock_response.text = "<html><body>Hello world!</body></html>"
        mock_response.url = "https://example.com"
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        success, message, result = fetch_webpage("https://example.com")

        assert success is True
        assert "Successfully fetched" in message
        assert result is not None
        assert result["content"] == "<html><body>Hello world!</body></html>"
        assert result["url"] == "https://example.com"
        assert result["status_code"] == 200
        assert result["content_type"] == "text/html"
        assert result["content_length"] == len(result["content"])

    @patch("requests.get")
    def test_fetch_webpage_with_timeout(self, mock_get):
        """Test webpage fetching with custom timeout."""
        mock_response = MagicMock()
        mock_response.text = "Test content"
        mock_response.url = "https://example.com"
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        success, message, result = fetch_webpage("https://example.com", timeout=60)

        assert success is True
        mock_get.assert_called_once_with(
            "https://example.com",
            timeout=60,
            headers={"User-Agent": "clippy-code/4.5.0 (AI Coding Assistant)"},
            allow_redirects=True,
        )

    @patch("requests.get")
    def test_fetch_webpage_with_custom_headers(self, mock_get):
        """Test webpage fetching with custom headers."""
        mock_response = MagicMock()
        mock_response.text = "Test content"
        mock_response.url = "https://example.com"
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        custom_headers = {"Authorization": "Bearer token123"}
        success, message, result = fetch_webpage("https://example.com", headers=custom_headers)

        assert success is True
        mock_get.assert_called_once_with(
            "https://example.com",
            timeout=30,
            headers={
                "User-Agent": "clippy-code/4.5.0 (AI Coding Assistant)",
                "Authorization": "Bearer token123",
            },
            allow_redirects=True,
        )

    @patch("requests.get")
    def test_fetch_webpage_http_error(self, mock_get):
        """Test handling HTTP errors."""
        import requests

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP 404")
        mock_get.return_value = mock_response

        success, message, result = fetch_webpage("https://example.com/notfound")

        assert success is False
        assert "HTTP error 404" in message
        assert result is None

    @patch("requests.get")
    def test_fetch_webpage_timeout_error(self, mock_get):
        """Test handling timeout errors."""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        success, message, result = fetch_webpage("https://example.com")

        assert success is False
        assert "Request timed out" in message
        assert result is None

    @patch("requests.get")
    def test_fetch_webpage_connection_error(self, mock_get):
        """Test handling connection errors."""
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        success, message, result = fetch_webpage("https://example.com")

        assert success is False
        assert "Connection error" in message
        assert result is None

    @patch("requests.get")
    def test_fetch_webpage_unicode_decode_error(self, mock_get):
        """Test handling Unicode decode errors."""
        mock_response = MagicMock()
        # Use property to simulate the UnicodeDecodeError when accessing .text
        error = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")
        type(mock_response).text = property(lambda self: (_ for _ in ()).throw(error))
        mock_response.content = b"Some binary content"
        mock_response.url = "https://example.com"
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/octet-stream"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        success, message, result = fetch_webpage("https://example.com")

        assert success is True
        assert result is not None
        # Should decode content with error replacement
        assert result["content"] == "Some binary content"

    def test_fetch_webpage_requests_not_installed(self):
        """Test handling when requests library is not installed."""
        # Mock the import system to simulate requests not being available
        original_import = __builtins__["__import__"]

        def mock_import(name, *args, **kwargs):
            if name == "requests":
                raise ImportError("No module named 'requests'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            success, message, result = fetch_webpage("https://example.com")

            assert success is False
            assert "requests library not installed" in message
            assert result is None

    @patch("requests.get")
    def test_fetch_webpage_content_mode(self, mock_get):
        """Test content mode extraction."""
        mock_response = MagicMock()
        mock_response.text = """
        <html>
        <head><script>console.log('test');</script></head>
        <body>
        <nav><a href="/">Home</a></nav>
        <main>
        <h1>Main Title</h1>
        <p>This is the main content we want to keep.</p>
        <div class="sidebar">Sidebar content</div>
        </main>
        <footer>Footer content</footer>
        </body>
        </html>
        """.strip()
        mock_response.url = "https://example.com"
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        success, message, result = fetch_webpage("https://example.com", mode="content")

        assert success is True
        assert result["mode"] == "content"
        assert result["compression_ratio"] < 100
        # Content extraction keeps inner content of main tag
        assert "Main Title" in result["content"]
        assert "This is the main content we want to keep" in result["content"]
        # Navigation, footer, and scripts should be removed
        assert "<nav>" not in result["content"]
        assert "<footer>" not in result["content"]
        assert "<script>" not in result["content"]
        assert "Home" not in result["content"]  # Navigation content should be gone
        assert "Footer content" not in result["content"]  # Footer content should be gone

    @patch("requests.get")
    def test_fetch_webpage_text_mode(self, mock_get):
        """Test text mode extraction."""
        mock_response = MagicMock()
        mock_response.text = "<h1>Title</h1><p>Paragraph text.</p><div>Sidebar</div>"
        mock_response.url = "https://example.com"
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        success, message, result = fetch_webpage("https://example.com", mode="text")

        assert success is True
        assert result["mode"] == "text"
        assert result["compression_ratio"] < 100
        # Should be plain text without HTML tags
        assert "<h1>" not in result["content"]
        assert "<p>" not in result["content"]
        assert "Title" in result["content"]
        assert "Paragraph text" in result["content"]

    @patch("requests.get")
    def test_fetch_webpage_max_length_limiting(self, mock_get):
        """Test content length limiting."""
        mock_response = MagicMock()
        mock_response.text = "A" * 1000  # 1000 character content
        mock_response.url = "https://example.com"
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        success, message, result = fetch_webpage("https://example.com", max_length=100)

        assert success is True
        assert len(result["content"]) <= 150  # 100 + truncation message (allow extra space)
        assert "Content truncated" in result["content"]
        assert result["original_length"] == 1000
        assert len(result["content"].replace("\n\n[Content truncated due to length limit]", "")) == 100

    @patch("requests.get")
    def test_fetch_webpage_content_mode_article_fallback(self, mock_get):
        """Test content mode falls back to article tag when main is not found."""
        mock_response = MagicMock()
        mock_response.text = """
        <html>
        <body>
        <article>
        <h1>Article Title</h1>
        <p>Article content here.</p>
        </article>
        </body>
        </html>
        """.strip()
        mock_response.url = "https://example.com"
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        success, message, result = fetch_webpage("https://example.com", mode="content")

        assert success is True
        # Content extraction keeps inner content, not the wrapper
        assert "Article Title" in result["content"]
        assert "Article content here" in result["content"]
        # Should not have the outer article tag
        assert "<article>" not in result["content"]
