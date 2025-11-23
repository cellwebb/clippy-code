"""
Vaporwave Clippy Entity - The digital assistant from your dreams 【クリッピー】
"""

import random
import asyncio
from enum import Enum
from typing import Optional
from textual.widget import Widget
from textual.reactive import reactive
from textual.timer import Timer
from rich.console import RenderableType
from rich.text import Text
from rich.panel import Panel
from rich.align import Align

from .neon_styles import COLORS, JAPANESE_TEXT, get_glitch_text


class ClippyState(Enum):
    """Different states for Clippy animations."""
    IDLE = "idle"
    THINKING = "thinking"
    EXCITED = "excited"
    QUESTIONING = "questioning"
    WORKING = "working"
    SUCCESS = "success"
    ERROR = "error"
    GLITCHING = "glitching"
    DREAMING = "dreaming"
    VAPORWAVE = "vaporwave"


class ClippyEntity(Widget):
    """
    The vaporwave Clippy character - animated, glitchy, and nostalgic.
    """

    DEFAULT_CSS = """
    ClippyEntity {
        width: 24;
        height: 12;
        content-align: center middle;
        background: #1A0033 20%;
        border: solid #FF10F0;
        margin: 1;
    }
    """

    # Reactive properties for animation
    state = reactive(ClippyState.IDLE)
    frame = reactive(0)
    glitch_level = reactive(0.0)
    color_shift = reactive(0)

    # ASCII art for different Clippy states
    CLIPPY_FRAMES = {
        ClippyState.IDLE: [
            """
   ╭─────╮
   │ ◉ ◉ │
   │  ◡  │
   ╰─┬─┬─╯
     │ │
     │ │
     │ │
     ╰─╯
            """,
            """
   ╭─────╮
   │ ◉ ◉ │
   │  ◡  │
   ╰─┬─┬─╯
     │ │
     │ │
     │ │
     ╰─╯
            """,
            """
   ╭─────╮
   │ ─ ─ │
   │  ◡  │
   ╰─┬─┬─╯
     │ │
     │ │
     │ │
     ╰─╯
            """,
        ],
        ClippyState.THINKING: [
            """
   ╭─────╮ ●
   │ ◉ ◉ │
   │  ~  │
   ╰─┬─┬─╯
     │ │
     │ │
     │ │
     ╰─╯
            """,
            """
   ╭─────╮ ○●
   │ ◉ ◉ │
   │  ~  │
   ╰─┬─┬─╯
     │ │
     │ │
     │ │
     ╰─╯
            """,
            """
   ╭─────╮ ○○●
   │ ◉ ◉ │
   │  ~  │
   ╰─┬─┬─╯
     │ │
     │ │
     │ │
     ╰─╯
            """,
        ],
        ClippyState.EXCITED: [
            """
   ╭─────╮
   │ ★ ★ │
   │  ▽  │ !!!
   ╰─┬─┬─╯
    ╱│ │╲
   ╱ │ │ ╲
  ╱  │ │  ╲
     ╰─╯
            """,
            """
   ╭─────╮ ✨
   │ ★ ★ │
   │  ▽  │
   ╰─┬─┬─╯
     │ │
    ╱│ │╲
   ╱ ╰─╯ ╲
            """,
        ],
        ClippyState.QUESTIONING: [
            """
   ╭─────╮
   │ ? ? │ ?
   │  o  │
   ╰─┬─┬─╯
     │ │
     │ │
     │ │
     ╰─╯
            """,
            """
   ╭─────╮ ??
   │ ◉ ? │
   │  ~  │
   ╰─┬─┬─╯
     │ │
     │ │
     │ │
     ╰─╯
            """,
        ],
        ClippyState.WORKING: [
            """
   ╭─────╮ ⚙
   │ ◉ ◉ │
   │  ─  │
   ╰─┬─┬─╯
     │ │ ⚙
     │ │
     │ │ ⚙
     ╰─╯
            """,
            """
   ╭─────╮
   │ ◉ ◉ │ ⚙
   │  ─  │
   ╰─┬─┬─╯ ⚙
     │ │
     │ │
     │ │
     ╰─╯
            """,
        ],
        ClippyState.SUCCESS: [
            """
   ╭─────╮ ✓
   │ ^ ^ │
   │  ◡  │ ✨
   ╰─┬─┬─╯
     │ │
    ╱│ │╲
   ╱ ╰─╯ ╲
            """,
        ],
        ClippyState.ERROR: [
            """
   ╭─────╮
   │ x x │ !
   │  ╿  │
   ╰─┬─┬─╯
     │ │
     │ │
     │ │
     ╰─╯
            """,
        ],
        ClippyState.GLITCHING: [
            """
   ▓▒░░░▒▓
   ░ ◉ ▓ ░
   ▒  ░  ▓
   ░▒▓▓▒░▒
     ▓ ░
     ░ ▒
     ▒ ▓
     ░▒░
            """,
            """
   ╭─▓▒░╮
   │ ░ ▓ │
   ▒  ◡  ░
   ╰▓░▒▓╯
     ▒ │
     │ ░
     ▓ │
     ╰▒╯
            """,
        ],
        ClippyState.DREAMING: [
            """
   ╭─────╮ ☁
   │ - - │ ☁
   │  ◡  │ ☁
   ╰─┬─┬─╯ zzz
     │ │
     │ │
     │ │
     ╰─╯
            """,
        ],
        ClippyState.VAPORWAVE: [
            """
╔═══════╗
║ ◈ ◈ ║ ♪
║  ▼  ║ ♫
╚═╤═╤═╝
  │ │ ▓▒░
  │ │ ▒▓░
  │ │ ░▓▒
  ╰─╯
            """,
        ],
    }

    # Glitch patterns for corruption effects
    GLITCH_PATTERNS = [
        "▓▒░ {} ░▒▓",
        "█▄▀ {} ▀▄█",
        "░░▒ {} ▒░░",
        "▌▐ {} ▐▌",
    ]

    # Japanese phrases for Clippy
    PHRASES = [
        "ようこそ、ユーザーさん",  # Welcome, user-san
        "デジタルの夢へ",  # To digital dreams
        "一緒に未来を作りましょう",  # Let's create the future together
        "エラーは美しい",  # Errors are beautiful
        "リアリティは幻想です",  # Reality is an illusion
    ]

    def __init__(self, initial_state: ClippyState = ClippyState.IDLE) -> None:
        """Initialize the vaporwave Clippy."""
        super().__init__()
        self.state = initial_state
        self.animation_timer: Optional[Timer] = None
        self.glitch_timer: Optional[Timer] = None
        self.current_phrase = random.choice(self.PHRASES)

    def on_mount(self) -> None:
        """Start animations when mounted."""
        # Start main animation loop
        self.animation_timer = self.set_interval(0.5, self.animate_frame)
        # Occasional glitch effects
        self.glitch_timer = self.set_interval(3.0, self.random_glitch)

    def animate_frame(self) -> None:
        """Advance to the next animation frame."""
        frames = self.CLIPPY_FRAMES.get(self.state, self.CLIPPY_FRAMES[ClippyState.IDLE])
        self.frame = (self.frame + 1) % len(frames)
        self.color_shift = (self.color_shift + 1) % 360

    def random_glitch(self) -> None:
        """Randomly trigger glitch effects."""
        if random.random() < 0.1:  # 10% chance of glitch
            self.glitch_level = random.uniform(0.1, 0.5)
            # Reset glitch after a moment
            self.set_timer(0.2, lambda: setattr(self, 'glitch_level', 0.0))

    def set_state(self, new_state: ClippyState, duration: Optional[float] = None) -> None:
        """
        Change Clippy's state with optional auto-return to idle.

        Args:
            new_state: The new state to transition to
            duration: If provided, return to IDLE after this many seconds
        """
        self.state = new_state
        self.frame = 0  # Reset animation frame

        if duration:
            self.set_timer(duration, lambda: self.set_state(ClippyState.IDLE))

    def render_clippy(self) -> str:
        """Render the current Clippy frame with effects."""
        frames = self.CLIPPY_FRAMES.get(self.state, self.CLIPPY_FRAMES[ClippyState.IDLE])
        current_frame = frames[self.frame % len(frames)]

        # Apply glitch effects if active
        if self.glitch_level > 0:
            current_frame = get_glitch_text(current_frame, self.glitch_level)

        return current_frame

    def get_color_for_state(self) -> str:
        """Get the appropriate color for the current state."""
        color_map = {
            ClippyState.IDLE: COLORS["electric_cyan"],
            ClippyState.THINKING: COLORS["neon_purple"],
            ClippyState.EXCITED: COLORS["hot_pink"],
            ClippyState.QUESTIONING: COLORS["sunset_orange"],
            ClippyState.WORKING: COLORS["laser_lime"],
            ClippyState.SUCCESS: COLORS["crt_green"],
            ClippyState.ERROR: COLORS["glitch_red"],
            ClippyState.GLITCHING: COLORS["hot_pink"],
            ClippyState.DREAMING: COLORS["digital_lavender"],
            ClippyState.VAPORWAVE: COLORS["vapor_pink"],
        }
        return color_map.get(self.state, COLORS["electric_cyan"])

    def render(self) -> RenderableType:
        """Render the Clippy widget."""
        clippy_art = self.render_clippy()
        color = self.get_color_for_state()

        # Create styled text with color
        text = Text(clippy_art, style=f"bold {color}")

        # Add a thought bubble with Japanese text occasionally
        if self.state == ClippyState.THINKING and self.frame == 0:
            thought = random.choice(list(JAPANESE_TEXT.values()))
            text.append(f"\n  {thought}", style=f"italic {COLORS['vapor_pink']}")

        # Wrap in a panel for better presentation
        panel = Panel(
            Align.center(text, vertical="middle"),
            border_style=color,
            title=f"[{COLORS['hot_pink']}]【{JAPANESE_TEXT['clippy']}】[/]",
            title_align="center",
        )

        return panel

    def trigger_excitement(self) -> None:
        """Trigger an excitement animation."""
        self.set_state(ClippyState.EXCITED, duration=2.0)

    def trigger_error(self) -> None:
        """Trigger an error animation."""
        self.set_state(ClippyState.ERROR, duration=3.0)

    def trigger_success(self) -> None:
        """Trigger a success animation."""
        self.set_state(ClippyState.SUCCESS, duration=2.0)

    def start_thinking(self) -> None:
        """Start the thinking animation."""
        self.set_state(ClippyState.THINKING)

    def stop_thinking(self) -> None:
        """Stop thinking and return to idle."""
        self.set_state(ClippyState.IDLE)

    def enter_vaporwave_mode(self) -> None:
        """Enter full vaporwave aesthetic mode."""
        self.set_state(ClippyState.VAPORWAVE)
        self.glitch_level = 0.2  # Constant low-level glitch

    def say_phrase(self) -> str:
        """Get a random Japanese phrase from Clippy."""
        return random.choice(self.PHRASES)


class FloatingClippy(ClippyEntity):
    """
    A floating version of Clippy that can move around the screen.
    """

    DEFAULT_CSS = """
    FloatingClippy {
        layer: above;
        width: 24;
        height: 12;
        background: #1A0033 20%;
        border: solid #FF10F0;
    }
    """

    position_x = reactive(0)
    position_y = reactive(0)
    velocity_x = reactive(1)
    velocity_y = reactive(1)

    def on_mount(self) -> None:
        """Start floating animation."""
        super().on_mount()
        self.float_timer = self.set_interval(0.1, self.update_position)

    def update_position(self) -> None:
        """Update Clippy's floating position."""
        # Simple bounce physics
        self.position_x += self.velocity_x
        self.position_y += self.velocity_y

        # Bounce off edges (simplified - would need actual screen dimensions)
        if self.position_x <= 0 or self.position_x >= 50:
            self.velocity_x *= -1
        if self.position_y <= 0 or self.position_y >= 20:
            self.velocity_y *= -1

        # Apply CSS offset
        self.styles.offset = (self.position_x, self.position_y)