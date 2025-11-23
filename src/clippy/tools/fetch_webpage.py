"""Fetch webpage tool implementation."""

import re
from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "fetch_webpage",
        "description": (
            "Fetch the content of a webpage from the given URL. "
            "Can return raw HTML, main content only, or plain text. "
            "Useful for reading documentation, articles, or web content."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL of the webpage to fetch"},
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds for the request (default: 30)",
                    "default": 30,
                },
                "headers": {
                    "type": "object",
                    "description": "Optional HTTP headers to include in the request",
                    "default": {},
                },
                "mode": {
                    "type": "string",
                    "description": "Content extraction mode: 'raw' (full HTML), 'content' (main content only), or 'text' (plain text)",
                    "enum": ["raw", "content", "text"],
                    "default": "raw",
                },
                "max_length": {
                    "type": "integer", 
                    "description": "Maximum characters to return (None for no limit)",
                    "default": None,
                },
            },
            "required": ["url"],
        },
    },
}


def fetch_webpage(
    url: str, 
    timeout: int = 30, 
    headers: dict[str, str] | None = None,
    mode: str = "raw",
    max_length: int | None = None
) -> tuple[bool, str, Any]:
    """Fetch a webpage."""
    try:
        import requests
    except ImportError:
        return False, "requests library not installed. Install with: pip install requests", None

    if headers is None:
        headers = {}

    try:
        # Set default user agent if not provided
        if "User-Agent" not in headers:
            headers["User-Agent"] = "clippy-code/4.5.0 (AI Coding Assistant)"

        response = requests.get(url, timeout=timeout, headers=headers, allow_redirects=True)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Try to return text content, fallback to raw content if needed
        try:
            content = response.text
        except UnicodeDecodeError:
            content = response.content.decode("utf-8", errors="replace")

        # Apply content extraction mode
        original_content = content
        original_length = len(content)
        
        if mode == "content":
            content = extract_main_content(content)
        elif mode == "text":
            content = extract_plain_text(content)
        # mode == "raw" keeps the original HTML

        # Apply length limit if specified
        if max_length is not None and len(content) > max_length:
            content = content[:max_length] + "\n\n[Content truncated due to length limit]"

        # Basic metadata
        content_type = response.headers.get("content-type", "unknown")
        content_length = len(content)

        result = {
            "content": content,
            "url": response.url,  # Final URL after redirects
            "status_code": response.status_code,
            "content_type": content_type,
            "content_length": content_length,
            "mode": mode,
            "original_length": original_length,
            "compression_ratio": round(content_length / original_length * 100, 1) if mode != "raw" and original_length > 0 else 100,
        }

        # Add processing info to message
        processing_info = []
        if mode != "raw":
            processing_info.append(f"mode: {mode}")
        if max_length is not None and len(original_content) > max_length:
            processing_info.append(f"truncated from {original_length} to {content_length}")
        
        message = f"Successfully fetched webpage: {url} ({content_length} characters"
        if processing_info:
            message += f" - {', '.join(processing_info)}"
        message += ")"

        return True, message, result

    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to fetch webpage {url}: {str(e)}"
        if isinstance(e, requests.exceptions.Timeout):
            error_msg = f"Request timed out after {timeout} seconds: {url}"
        elif isinstance(e, requests.exceptions.ConnectionError):
            error_msg = f"Connection error: unable to reach {url}"
        elif isinstance(e, requests.exceptions.HTTPError):
            error_msg = f"HTTP error {response.status_code} when fetching {url}"

        return False, error_msg, None
    except Exception as e:
        return False, f"Unexpected error fetching {url}: {str(e)}", None


def extract_main_content(html_content: str) -> str:
    """Extract main content from HTML using common patterns."""
    # Remove script, style, and other non-content tags
    html_content = re.sub(
        r'<(script|style|noscript|iframe|svg|!--.*?-->)[^>]*>.*?</\1>', 
        '', 
        html_content, 
        flags=re.DOTALL | re.IGNORECASE
    )
    
    # Common content container patterns
    content_patterns = [
        r'<main[^>]*>(.*?)</main>',
        r'<article[^>]*>(.*?)</article>', 
        r'<div[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</div>',
        r'<div[^>]*class="[^"]*main[^"]*"[^>]*>(.*?)</div>',
        r'<div[^>]*id="[^"]*content[^"]*"[^>]*>(.*?)</div>',
        r'<div[^>]*id="[^"]*main[^"]*"[^>]*>(.*?)</div>',
        r'<section[^>]*class="[^"]*content[^"]*"[^>]*>(.*?)</section>',
    ]
    
    # Try to extract main content using patterns
    for pattern in content_patterns:
        match = re.search(pattern, html_content, flags=re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1)
            break
    else:
        # Fallback: try to find body content
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, flags=re.DOTALL | re.IGNORECASE)
        if body_match:
            content = body_match.group(1)
        else:
            content = html_content
    
    # Remove common navigation, header, footer patterns
    unwanted_patterns = [
        r'<(header|footer|nav|aside)[^>]*>.*?</\1>',
        r'<div[^>]*class="[^"]*(nav|sidebar|menu|header|footer)[^"]*"[^>]*>.*?</div>',
        r'<div[^>]*id="[^"]*(nav|sidebar|menu|header|footer)[^"]*"[^>]*>.*?</div>',
    ]
    
    for pattern in unwanted_patterns:
        content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Clean up extra whitespace
    content = re.sub(r'\n\s*\n', '\n\n', content)  # Reduce multiple newlines
    content = content.strip()
    
    return content


def extract_plain_text(html_content: str) -> str:
    """Extract plain text from HTML, removing all tags and formatting."""
    # First extract main content to reduce noise
    main_content = extract_main_content(html_content)
    
    # Remove all HTML tags
    text = re.sub(r'<[^>]+>', '', main_content)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)  # Convert multiple spaces/newlines to single space
    text = text.replace('&nbsp;', ' ')  # Handle non-breaking spaces
    text = text.replace('&lt;', '<')    # Handle HTML entities
    text = text.replace('&gt;', '>')
    text = text.replace('&amp;', '&')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    
    # Clean up spaces around punctuation
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    
    return text.strip()
