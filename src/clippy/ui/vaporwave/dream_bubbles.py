"""
Dream Bubbles - Simplified gradient speech bubbles for vaporwave Clippy 【夢の泡】
"""

import random
from typing import Optional, List
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import VerticalScroll
from textual.reactive import reactive
from rich.console import RenderableType
from rich.text import Text

from .neon_styles import (
    COLORS,
    JAPANESE_TEXT,
)


class ConversationBubbles(VerticalScroll):
    """
    Simplified container for conversation messages with vaporwave styling.
    """

    DEFAULT_CSS = """
    ConversationBubbles {
        width: 100%;
        height: 100%;
        padding: 1;
        background: #1A0033 10%;
        scrollbar-background: #0D0221;
        scrollbar-color: #00FFFF;
    }
    
    .message-widget {
        margin: 1 2;
        padding: 0 1;
        border-left: solid #FF10F0;
        background: #1A0033 20%;
    }
    """

    def __init__(self) -> None:
        """Initialize conversation container."""
        super().__init__()
        self.messages: List[Static] = []

    def add_message(
        self,
        message: str,
        bubble_type: str = "assistant",
        auto_scroll: bool = True
    ) -> Widget:
        """
        Add a new message bubble to the conversation.

        Args:
            message: The message text
            bubble_type: Type of bubble (user/assistant/system)
            auto_scroll: Whether to auto-scroll to the new message

        Returns:
            The created message widget
        """
        # Vaporwave styling based on message type
        if bubble_type == "user":
            color = "#FF69B4"  # vapor pink
            prefix = "✨ YOU:"
            border_color = "#FF10F0"
            bg_color = "#4A0E4E 30%"
        elif bubble_type == "system":
            color = "#00CED1"  # grid cyan
            prefix = "🔧 SYSTEM:"
            border_color = "#39FF14"
            bg_color = "#0D0221 50%"
        else:
            color = "#00FFFF"  # electric cyan
            prefix = "📎 CLIPPY:"
            border_color = "#00FFFF"
            bg_color = "#1A0033 40%"

        # Create styled message using Rich Text with gradient effect
        text = Text()
        
        # Add timestamp for retro terminal feel
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        text.append(f"[{timestamp}] ", style=f"dim {color}")
        text.append(f"{prefix} ", style=f"bold {color}")
        text.append(message, style=color)

        # Create and configure the message widget
        message_widget = Static(text)
        message_widget.styles.border_left = ("thick", border_color)
        message_widget.styles.background = bg_color
        message_widget.styles.border_radius = 2
        message_widget.styles.margin = (0, 1)
        message_widget.styles.padding = (1, 2)

        # Mount the message directly to this container
        self.mount(message_widget)
        self.messages.append(message_widget)

        # Auto-scroll to new message
        if auto_scroll:
            try:
                self.scroll_end(animate=False)
            except Exception:
                # Fallback if auto-scroll fails
                pass

        return message_widget

    def clear_conversation(self) -> None:
        """Clear all messages from the conversation."""
        for message in self.messages:
            message.remove()
        self.messages.clear()

    # Note: No compose() method needed - messages are mounted dynamically


class StatusMessage(Widget):
    """
    Floating status message with vaporwave styling.
    """

    DEFAULT_CSS = """
    StatusMessage {
        layer: above;
        dock: top;
        width: auto;
        height: 3;
        margin: 1;
        padding: 0 2;
        background: #FF10F0;
        border: double #39FF14;
    }
    """

    message = reactive("")
    message_type = reactive("info")  # info, success, error, loading

    def __init__(self, message: str = "", message_type: str = "info") -> None:
        """Initialize status message."""
        super().__init__()
        self.message = message
        self.message_type = message_type

    def render(self) -> RenderableType:
        """Render the status message."""
        # Choose icon based on type
        icons = {
            "info": "ℹ",
            "success": "✓",
            "error": "✗",
            "loading": "◉"
        }
        icon = icons.get(self.message_type, "●")

        # Choose color based on type
        colors = {
            "info": COLORS["electric_cyan"],
            "success": COLORS["crt_green"],
            "error": COLORS["glitch_red"],
            "loading": COLORS["sunset_orange"]
        }
        color = colors.get(self.message_type, COLORS["electric_cyan"])

        # Format message with icon
        formatted = f"{icon} {self.message}"

        # Add Japanese text for aesthetic
        if self.message_type == "loading":
            formatted += f" {JAPANESE_TEXT['loading']}..."

        return Text(formatted, style=f"bold {color}")

    def show_message(self, message: str, message_type: str = "info", duration: float = 3.0) -> None:
        """
        Show a temporary status message.

        Args:
            message: The message to display
            message_type: Type of message
            duration: How long to show the message
        """
        self.message = message
        self.message_type = message_type
        self.display = True

        # Auto-hide after duration
        self.set_timer(duration, lambda: setattr(self, 'display', False))


# Future enhancement: Complex DreamBubble class for later use
class DreamBubble(Widget):
    """
    Advanced gradient speech bubble with typewriter effect - for future enhancement.
    """
    # This will be implemented later once basic functionality works
    pass