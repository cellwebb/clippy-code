"""
CRT Display Widget - Retro monitor effects with scanlines and curvature 【モニター】
"""

import random
from collections.abc import Callable, Generator
from typing import Any

from rich.console import RenderableType
from rich.text import Text
from textual.containers import Container  # type: ignore
from textual.reactive import reactive  # type: ignore
from textual.widget import Widget  # type: ignore

from .neon_styles import COLORS, create_vhs_static_line


class Scanlines(Widget):
    """
    Overlay widget that creates animated scanline effects.
    """

    DEFAULT_CSS = """
    Scanlines {
        layer: above;
        width: 100%;
        height: 100%;
        opacity: 10%;
    }
    """

    offset = reactive(0)

    def on_mount(self) -> None:
        """Start scanline animation."""
        self.animation_timer = self.set_interval(0.05, self.animate_scanlines)

    def animate_scanlines(self) -> None:
        """Animate the scanlines moving down the screen."""
        self.offset = (self.offset + 1) % 4

    def render(self) -> RenderableType:
        """Render the scanlines effect."""
        height = self.size.height if self.size else 30
        lines = []

        for i in range(height):
            if (i + self.offset) % 4 == 0:
                # Bright scanline
                lines.append("─" * (self.size.width if self.size else 80))
            elif (i + self.offset) % 4 == 1:
                # Dim scanline
                lines.append("·" * (self.size.width if self.size else 80))
            else:
                # Empty space
                lines.append("")

        text = Text("\n".join(lines), style=f"{COLORS['grid_cyan']}20")
        return text


class VHSStatic(Widget):
    """
    VHS static noise effect overlay.
    """

    DEFAULT_CSS = """
    VHSStatic {
        layer: above;
        width: 100%;
        height: 100%;
        opacity: 5%;
    }
    """

    noise_level = reactive(0.05)
    frame = reactive(0)

    def on_mount(self) -> None:
        """Start static animation."""
        self.static_timer = self.set_interval(0.1, self.update_static)

    def update_static(self) -> None:
        """Update the static noise pattern."""
        self.frame = (self.frame + 1) % 10
        # Occasional static burst
        if random.random() < 0.05:
            self.noise_level = random.uniform(0.1, 0.3)
            self.set_timer(0.2, lambda: setattr(self, "noise_level", 0.05))

    def render(self) -> RenderableType:
        """Render VHS static noise."""
        height = self.size.height if self.size else 30
        width = self.size.width if self.size else 80

        lines = []
        for _ in range(height):
            if random.random() < self.noise_level:
                lines.append(create_vhs_static_line(width))
            else:
                lines.append("")

        text = Text("\n".join(lines), style=f"{COLORS['vhs_static']}")
        return text


class CRTDisplay(Container):
    """
    CRT monitor display with retro effects.
    Simulates an old CRT monitor with curved edges, scanlines, and color bleeding.
    """

    DEFAULT_CSS = """
    CRTDisplay {
        width: 100%;
        height: 100%;
        background: #0D0221;
        border: thick #00FFFF;
        padding: 1;
    }

    .crt-frame {
        border: double #00CED1;
        background: #1A0033 90%;
    }

    .crt-content {
        padding: 2;
    }
    """

    power_on = reactive(True)
    brightness = reactive(0.9)
    contrast = reactive(1.0)
    color_bleed = reactive(0.1)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the CRT display."""
        super().__init__(*args, **kwargs)
        self.scanlines = Scanlines()
        self.static_overlay = VHSStatic()
        self.phosphor_burn = False
        self.warmup_complete = False

    def compose(self) -> Generator[Widget, None, None]:
        """Compose the CRT display with effects."""
        # Layer effects on top of each other
        yield self.scanlines
        yield self.static_overlay

    def on_mount(self) -> None:
        """Initialize CRT effects when mounted."""
        # Simulate CRT warmup
        self.warmup_animation()
        # Occasional flicker
        self.flicker_timer = self.set_interval(10.0, self.random_flicker)

    def warmup_animation(self) -> None:
        """Simulate CRT monitor warming up."""
        self.brightness = 0.3

        def increase_brightness() -> None:
            if self.brightness < 0.9:
                self.brightness += 0.1
                self.set_timer(0.1, increase_brightness)
            else:
                self.brightness = 0.9
                self.warmup_complete = True

        self.set_timer(0.5, increase_brightness)

    def random_flicker(self) -> None:
        """Create occasional screen flicker."""
        if random.random() < 0.1:  # 10% chance
            original_brightness = self.brightness
            self.brightness *= 0.7
            self.set_timer(0.05, lambda: setattr(self, "brightness", original_brightness))

    def power_off_animation(self) -> None:
        """Animate CRT power off with classic shrinking dot."""

        def shrink_display() -> None:
            if self.brightness > 0:
                self.brightness -= 0.2
                self.set_timer(0.05, shrink_display)
            else:
                self.power_on = False

        shrink_display()

    def apply_phosphor_burn(self, text: str) -> str:
        """
        Apply phosphor burn-in effect to text.
        Makes certain characters appear 'burned in' to the screen.
        """
        if not self.phosphor_burn:
            return text

        result = ""
        for char in text:
            if random.random() < 0.05:  # 5% chance of burn-in
                # Make character slightly dimmer/different color
                result += f"[{COLORS['dark_magenta']}]{char}[/]"
            else:
                result += char
        return result


class CRTFrame(Widget):
    """
    Decorative CRT monitor frame with curved corners.
    """

    DEFAULT_CSS = """
    CRTFrame {
        width: 100%;
        height: 100%;
        border: tall #FFBF00;
    }
    """

    def render(self) -> RenderableType:
        """Render the CRT frame with curved corners."""
        width = self.size.width if self.size else 80
        height = self.size.height if self.size else 24

        # Create curved corner frame
        frame_lines = []

        # Top line with curve
        top_line = "╭" + "─" * (width - 2) + "╮"
        frame_lines.append(top_line)

        # Middle lines
        for _ in range(height - 2):
            frame_lines.append("│" + " " * (width - 2) + "│")

        # Bottom line with curve
        bottom_line = "╰" + "─" * (width - 2) + "╯"
        frame_lines.append(bottom_line)

        frame_text = "\n".join(frame_lines)

        # Style with retro amber color for that classic monitor look
        text = Text(frame_text, style=f"bold {COLORS['retro_amber']}")

        # Add monitor brand text
        if height > 10 and width > 30:
            brand = "【 ＶＡＰＯＲ-ＯＳ ２０００ 】"
            text.append(f"\n{brand:^{width}}", style=f"bold {COLORS['hot_pink']}")

        return text


class RetroTerminal(Container):
    """
    Complete retro terminal with CRT effects and vaporwave aesthetics.
    """

    DEFAULT_CSS = """
    RetroTerminal {
        width: 100%;
        height: 100%;
        background: #1A0033;
    }

    .terminal-header {
        dock: top;
        height: 3;
        background: #FF10F0;
        content-align: center middle;
    }

    .terminal-body {
        background: #0D0221 95%;
        color: #33FF00;
        padding: 1;
    }
    """

    def __init__(self, title: str = "ＣＬＩＰＰＹ　ＴＥＲＭＩＮＡＬ") -> None:
        """Initialize the retro terminal."""
        super().__init__()
        self.title = title
        self.crt_display = CRTDisplay()
        self.command_history: list[str] = []
        self.current_line = ""

    def compose(self) -> Generator[Widget, None, None]:
        """Compose the terminal layout."""
        # Add CRT display as main component
        yield self.crt_display

    def type_text(self, text: str, callback: Callable[[], None] | None = None) -> None:
        """
        Simulate typing text with retro effect.

        Args:
            text: Text to type
            callback: Function to call when typing is complete
        """
        self.current_line = ""
        chars = list(text)

        def type_char() -> None:
            if chars:
                self.current_line += chars.pop(0)
                self.refresh()
                self.set_timer(0.05, type_char)
            elif callback is not None:
                callback()

        type_char()

    def add_glitch_effect(self) -> None:
        """Add a temporary glitch effect to the display."""
        original_static = self.crt_display.static_overlay.noise_level
        self.crt_display.static_overlay.noise_level = 0.5
        self.set_timer(
            0.3, lambda: setattr(self.crt_display.static_overlay, "noise_level", original_static)
        )

    def show_boot_sequence(self) -> None:
        """Show a retro boot sequence."""
        boot_messages = [
            "ＩＮＩＴＩＡＬＩＺＩＮＧ．．．",
            "ＬＯＡＤＩＮＧ　ＶＡＰＯＲＷＡＶＥ　ＯＳ",
            "ＳＣＡＮＮＩＮＧ　ＭＥＭＯＲＹ　ＢＡＮＫＳ",
            "ＳＹＮＴＨＥＳＩＺＩＮＧ　ＮＥＯＮ　ＣＯＬＯＲＳ",
            "ＣＡＬＩＢＲＡＴＩＮＧ　ＣＲＴ　ＤＩＳＰＬＡＹ",
            "ＳＹＳＴＥＭ　ＲＥＡＤＹ",
            "",
            "ＷＥＬＣＯＭＥ　ＴＯ　ＴＨＥ　ＤＩＧＩＴＡＬ　ＳＵＮＳＥＴ",
        ]

        for i, message in enumerate(boot_messages):
            self.set_timer(i * 0.5, lambda m=message: self.type_text(m))


class ChromaticAberration(Widget):
    """
    Chromatic aberration effect for that vintage CRT color bleeding.
    """

    DEFAULT_CSS = """
    ChromaticAberration {
        layer: above;
        width: 100%;
        height: 100%;
        opacity: 20%;
    }
    """

    offset = reactive(1)

    def render(self) -> RenderableType:
        """Create color bleeding effect."""
        # This would ideally shift RGB channels slightly
        # For terminal, we'll simulate with colored shadows
        width = self.size.width if self.size else 80
        height = self.size.height if self.size else 30

        lines = []
        for y in range(height):
            line = ""
            for x in range(width):
                if (x + y) % 10 == 0:
                    # Red channel shift
                    line += f"[{COLORS['glitch_red']}]░[/]"
                elif (x + y) % 10 == 3:
                    # Blue channel shift
                    line += f"[{COLORS['electric_cyan']}]░[/]"
                else:
                    line += " "
            lines.append(line)

        return Text("\n".join(lines))
