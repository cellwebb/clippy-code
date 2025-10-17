"""Error formatting utilities for the agent system."""


def format_api_error(error: Exception) -> str:
    """
    Format API errors into user-friendly messages.

    Args:
        error: The exception to format

    Returns:
        User-friendly error message string
    """
    try:
        from openai import (
            APIConnectionError,
            APITimeoutError,
            AuthenticationError,
            BadRequestError,
            ConflictError,
            InternalServerError,
            NotFoundError,
            PermissionDeniedError,
            RateLimitError,
            UnprocessableEntityError,
        )

        if isinstance(error, AuthenticationError):
            return (
                "Authentication failed. Please check your API key.\n\n"
                "Set OPENAI_API_KEY in your environment or .env file."
            )
        elif isinstance(error, RateLimitError):
            return (
                "Rate limit exceeded. The API has throttled your requests.\n\n"
                "The system will automatically retry with exponential backoff."
            )
        elif isinstance(error, APIConnectionError):
            return (
                "Connection error. Failed to connect to the API.\n\n"
                "Check your internet connection or base URL settings."
            )
        elif isinstance(error, APITimeoutError):
            return (
                "Request timeout. The API took too long to respond.\n\n"
                "The system will automatically retry."
            )
        elif isinstance(error, BadRequestError):
            return f"Bad request. The API rejected the request.\n\nDetails: {str(error)}"
        elif isinstance(error, InternalServerError):
            return (
                "Server error. The API encountered an internal error.\n\n"
                "The system will automatically retry."
            )
        elif isinstance(error, PermissionDeniedError):
            return (
                "Permission denied. Your API key doesn't have permission to access "
                "this resource.\n\n"
                "Check your API key permissions with your provider."
            )
        elif isinstance(error, NotFoundError):
            return f"Resource not found. Check if the model exists.\n\nDetails: {str(error)}"
        elif isinstance(error, ConflictError):
            return (
                f"Conflict error. The request conflicts with the current state.\n\nDetails: {error}"
            )
        elif isinstance(error, UnprocessableEntityError):
            return (
                "Unprocessable entity. The request was well-formed but was unable to be "
                "processed.\n\n"
                f"Details: {error}"
            )
        else:
            return f"{type(error).__name__}: {str(error)}"
    except ImportError:
        return f"{type(error).__name__}: {str(error)}"
