"""
Dream Bubbles - Gradient speech bubbles for vaporwave Clippy 【夢の泡】
"""

import random
from typing import Optional, List, Tuple
from textual.widget import Widget
from textual.reactive import reactive
from textual.timer import Timer
from rich.console import RenderableType
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich.padding import Padding

from .neon_styles import (
    COLORS,
    JAPANESE_TEXT,
    create_sunset_gradient,
    interpolate_color,
    get_gradient_text
)


class DreamBubble(Widget):
    """
    A gradient speech bubble with typewriter effect and vaporwave aesthetics.
    """

    DEFAULT_CSS = """
    DreamBubble {
        width: auto;
        min-width: 30;
        max-width: 60;
        height: auto;
        min-height: 5;
        margin: 1;
        padding: 1;
    }

    DreamBubble.user {
        align: right top;
        background: #4A0E4E;
    }

    DreamBubble.assistant {
        align: left top;
        background: #FF10F0;
    }

    DreamBubble.system {
        align: center top;
        background: #0D0221;
    }
    """

    message = reactive("")
    displayed_text = reactive("")
    is_typing = reactive(False)
    bubble_type = reactive("assistant")  # "user", "assistant", "system"

    def __init__(
        self,
        message: str = "",
        bubble_type: str = "assistant",
        typing_speed: float = 0.03,
        auto_type: bool = True
    ) -> None:
        """
        Initialize the dream bubble.

        Args:
            message: The message to display
            bubble_type: Type of bubble (user/assistant/system)
            typing_speed: Speed of typewriter effect in seconds per character
            auto_type: Whether to automatically start typing on mount
        """
        super().__init__()
        self.message = message
        self.bubble_type = bubble_type
        self.typing_speed = typing_speed
        self.auto_type = auto_type
        self.typing_timer: Optional[Timer] = None
        self.char_index = 0

    def on_mount(self) -> None:
        """Start typewriter effect when mounted."""
        if self.auto_type and self.message:
            self.start_typing()

    def start_typing(self) -> None:
        """Start the typewriter effect."""
        self.is_typing = True
        self.displayed_text = ""
        self.char_index = 0
        self.typing_timer = self.set_interval(self.typing_speed, self.type_character)

    def type_character(self) -> None:
        """Type one character at a time."""
        if self.char_index < len(self.message):
            self.displayed_text = self.message[:self.char_index + 1]
            self.char_index += 1
        else:
            # Typing complete
            self.is_typing = False
            if self.typing_timer:
                self.typing_timer.stop()
                self.typing_timer = None

    def set_message(self, message: str, auto_type: bool = True) -> None:
        """
        Set a new message for the bubble.

        Args:
            message: New message to display
            auto_type: Whether to automatically start typing
        """
        self.message = message
        if auto_type:
            self.start_typing()
        else:
            self.displayed_text = message

    def render_bubble_frame(self, width: int) -> List[str]:
        """
        Create ASCII art bubble frame with rounded corners.

        Args:
            width: Width of the bubble content
        """
        # Different styles for different bubble types
        if self.bubble_type == "user":
            corners = ("╭", "╮", "╰", "╯")
            tail = "  >"
        elif self.bubble_type == "assistant":
            corners = ("◜", "◝", "◟", "◞")
            tail = "<  "
        else:  # system
            corners = ("┌", "┐", "└", "┘")
            tail = ""

        frame = []
        # Top line
        frame.append(corners[0] + "─" * (width + 2) + corners[1])
        # Bottom line (will be added after content)

        return frame, corners, tail

    def apply_gradient_to_text(self, text: str) -> str:
        """Apply gradient colors to text based on bubble type."""
        if self.bubble_type == "user":
            return get_gradient_text(text, "digital_lavender", "vapor_pink")
        elif self.bubble_type == "assistant":
            return get_gradient_text(text, "electric_cyan", "hot_pink")
        else:
            return get_gradient_text(text, "grid_cyan", "neon_purple")

    def render(self) -> RenderableType:
        """Render the speech bubble with gradient effects."""
        # Get the text to display
        display_text = self.displayed_text if self.is_typing else self.message

        if not display_text:
            return Text("")

        # Split into lines for proper formatting
        lines = display_text.split('\n')
        max_width = max(len(line) for line in lines) if lines else 0
        max_width = min(max_width, 50)  # Cap width at 50 chars

        # Get bubble frame
        frame_top, corners, tail = self.render_bubble_frame(max_width)

        # Build the bubble content
        bubble_lines = [frame_top[0]]

        for line in lines:
            # Pad line to width
            padded_line = line.ljust(max_width)
            # Apply gradient if not typing, otherwise normal color
            if not self.is_typing:
                styled_line = self.apply_gradient_to_text(padded_line)
            else:
                styled_line = padded_line

            bubble_lines.append(f"│ {styled_line} │")

        # Add bottom frame
        bubble_lines.append(corners[2] + "─" * (max_width + 2) + corners[3])

        # Add tail to indicate speaker
        if tail and self.bubble_type != "system":
            if self.bubble_type == "user":
                bubble_lines[-1] = bubble_lines[-1][:-3] + tail
            else:
                bubble_lines[-1] = tail + bubble_lines[-1][3:]

        # Add typing indicator if still typing
        if self.is_typing:
            bubble_lines.append("    ░▒▓█▓▒░" if self.char_index % 2 == 0 else "    ▓▒░█░▒▓")

        # Choose color based on type
        color_map = {
            "user": COLORS["vapor_pink"],
            "assistant": COLORS["electric_cyan"],
            "system": COLORS["grid_cyan"]
        }
        bubble_color = color_map.get(self.bubble_type, COLORS["electric_cyan"])

        # Create final text with styling
        result = Text("\n".join(bubble_lines), style=f"{bubble_color}")

        return result


class ThoughtCloud(DreamBubble):
    """
    A thought bubble variant with cloud-like appearance.
    """

    def render_bubble_frame(self, width: int) -> Tuple[List[str], Tuple[str, ...], str]:
        """Create cloud-like thought bubble frame."""
        # Cloud-like frame
        frame = []
        frame.append("  ☁" + "─" * (width - 2) + "☁  ")
        # Middle will be added with content
        # Bottom will be added after

        corners = ("☁", "☁", "☁", "☁")
        tail = "   ○ ○ ○"

        return frame, corners, tail


class GlitchBubble(DreamBubble):
    """
    A glitchy speech bubble with corruption effects.
    """

    glitch_level = reactive(0.1)

    def __init__(self, *args, **kwargs):
        """Initialize glitch bubble."""
        super().__init__(*args, **kwargs)
        self.glitch_chars = ["▓", "▒", "░", "█", "▄", "▀"]

    def on_mount(self) -> None:
        """Start glitch animations."""
        super().on_mount()
        self.glitch_timer = self.set_interval(0.5, self.update_glitch)

    def update_glitch(self) -> None:
        """Update glitch level randomly."""
        self.glitch_level = random.uniform(0.05, 0.3)

    def apply_glitch(self, text: str) -> str:
        """Apply glitch corruption to text."""
        result = ""
        for char in text:
            if random.random() < self.glitch_level and char != " ":
                result += random.choice(self.glitch_chars)
            else:
                result += char
        return result

    def render(self) -> RenderableType:
        """Render with glitch effects."""
        # Get base render
        base_render = super().render()

        if isinstance(base_render, Text):
            # Apply glitch to the text
            glitched_text = self.apply_glitch(base_render.plain)
            return Text(glitched_text, style=base_render.style or "")

        return base_render


class ConversationBubbles(Widget):
    """
    Container for managing multiple conversation bubbles.
    """

    DEFAULT_CSS = """
    ConversationBubbles {
        width: 100%;
        height: 100%;
        overflow-y: scroll;
        padding: 1;
        background: #1A0033 10%;
    }
    """

    def __init__(self) -> None:
        """Initialize conversation container."""
        super().__init__()
        self.bubbles: List[DreamBubble] = []
        self.max_bubbles = 50  # Limit for performance

    def add_message(
        self,
        message: str,
        bubble_type: str = "assistant",
        auto_scroll: bool = True
    ) -> DreamBubble:
        """
        Add a new message bubble to the conversation.

        Args:
            message: The message text
            bubble_type: Type of bubble (user/assistant/system)
            auto_scroll: Whether to auto-scroll to the new message

        Returns:
            The created bubble widget
        """
        # Create appropriate bubble type
        if "error" in message.lower():
            bubble = GlitchBubble(message, bubble_type)
        elif bubble_type == "system":
            bubble = ThoughtCloud(message, bubble_type)
        else:
            bubble = DreamBubble(message, bubble_type)

        self.bubbles.append(bubble)

        # Remove old bubbles if we exceed the limit
        if len(self.bubbles) > self.max_bubbles:
            self.bubbles.pop(0)

        # Mount the bubble
        self.mount(bubble)

        if auto_scroll:
            self.scroll_end()

        return bubble

    def clear_conversation(self) -> None:
        """Clear all bubbles from the conversation."""
        for bubble in self.bubbles:
            bubble.remove()
        self.bubbles.clear()

    def compose(self):
        """Compose the conversation view."""
        # Bubbles are added dynamically via add_message
        return []


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