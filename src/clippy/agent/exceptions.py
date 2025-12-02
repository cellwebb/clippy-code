"""Agent-specific exceptions.

This module exists to avoid circular imports between agent modules.
"""


class InterruptedExceptionError(Exception):
    """Exception raised when user interrupts execution."""

    pass
