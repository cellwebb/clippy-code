"""Tool result types for better type safety and consistency."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    """Standardized result type for all tool operations.
    
    Provides better type safety than tuple[bool, str, Any] and makes the
    intent of each field explicit.
    
    Attributes:
        success: Whether the tool operation succeeded
        message: Human-readable message describing the result
        data: Optional data payload (for successful operations)
    """
    success: bool
    message: str
    data: Any = None
    
    @classmethod
    def success_result(cls, message: str, data: Any = None) -> "ToolResult":
        """Create a successful result.
        
        Args:
            message: Success message
            data: Optional data payload
            
        Returns:
            ToolResult instance with success=True
        """
        return cls(success=True, message=message, data=data)
    
    @classmethod
    def failure_result(cls, message: str) -> "ToolResult":
        """Create a failure result.
        
        Args:
            message: Error message
            
        Returns:
            ToolResult instance with success=False
        """
        return cls(success=False, message=message, data=None)