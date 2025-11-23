"""
Vaporwave color schemes and styles - neon dreams and digital sunsets 【美的】
"""

# Vaporwave color palette
COLORS = {
    # Primary neon colors
    "hot_pink": "#FF10F0",
    "electric_cyan": "#00FFFF",
    "neon_purple": "#9D00FF",
    "sunset_orange": "#FF6B35",
    "laser_lime": "#39FF14",

    # Secondary colors
    "deep_purple": "#1A0033",
    "midnight_blue": "#0D0221",
    "dark_magenta": "#4A0E4E",
    "vapor_pink": "#FF69B4",
    "digital_lavender": "#E6E6FA",

    # Background and accents
    "grid_cyan": "#00CED1",
    "vhs_static": "#2E2E2E",
    "crt_green": "#33FF00",
    "retro_amber": "#FFBF00",
    "glitch_red": "#FF0040",
}

# Japanese text for aesthetic
JAPANESE_TEXT = {
    "clippy": "クリッピー",
    "loading": "ローディング",
    "error": "エラー",
    "success": "成功",
    "welcome": "ようこそ",
    "goodbye": "さようなら",
    "thinking": "考え中",
    "dream": "夢",
    "digital": "デジタル",
    "aesthetic": "美的",
}

# ASCII frames for various UI elements
ASCII_FRAMES = {
    "crt_corners": {
        "top_left": "╭",
        "top_right": "╮",
        "bottom_left": "╰",
        "bottom_right": "╯",
        "horizontal": "─",
        "vertical": "│",
    },
    "glitch_chars": ["▓", "▒", "░", "█", "▄", "▀", "▌", "▐", "■", "□"],
    "grid_chars": ["╱", "╲", "╳", "┃", "━", "┏", "┓", "┗", "┛"],
}

# Textual CSS for vaporwave aesthetic
VAPORWAVE_CSS = """
/* Define color variables for vaporwave theme */
$hot_pink: #FF10F0;
$electric_cyan: #00FFFF;
$neon_purple: #9D00FF;
$sunset_orange: #FF6B35;
$laser_lime: #39FF14;
$deep_purple: #1A0033;
$midnight_blue: #0D0221;
$dark_magenta: #4A0E4E;
$vapor_pink: #FF69B4;
$digital_lavender: #E6E6FA;
$grid_cyan: #00CED1;
$vhs_static: #2E2E2E;
$crt_green: #33FF00;
$retro_amber: #FFBF00;
$glitch_red: #FF0040;

/* Main application screen */
Screen {
    background: $deep_purple;
    overflow: hidden;
}

/* CRT monitor effect container */
.crt-container {
    border: thick $electric_cyan;
    border-title-align: center;
    padding: 1;
    margin: 1;
    background: $vhs_static 20%;
}

/* Scanline overlay effect */
.scanlines {
    background: $grid_cyan 5%;
}

/* Clippy character container */
.clippy-entity {
    width: 20;
    height: 10;
    border: solid $hot_pink;
    content-align: center middle;
    text-style: bold;
}

.clippy-glow {
    text-style: bold reverse;
    color: $electric_cyan;
    background: $deep_purple;
}

/* Speech bubble styles */
.speech-bubble {
    border: double $vapor_pink;
    padding: 1 2;
    margin: 1;
    background: $dark_magenta;
}

.speech-bubble-text {
    color: $digital_lavender;
    text-style: italic;
}

/* Channel selector tabs */
.channel-tab {
    width: 100%;
    height: 3;
    background: $midnight_blue;
    border: tall $neon_purple;
}

.channel-tab-active {
    background: $hot_pink;
    border: double $laser_lime;
    text-style: bold reverse;
}

.channel-tab-inactive {
    background: $vhs_static 50%;
    border: solid $grid_cyan 50%;
    color: $digital_lavender 70%;
}

/* Grid background animation */
.grid-background {
    background: $deep_purple;
    color: $grid_cyan 30%;
}

/* Button styles */
Button {
    width: 16;
    background: $dark_magenta;
    border: tall $electric_cyan;
    text-style: bold;
}

Button:hover {
    background: $hot_pink;
    border: tall $laser_lime;
}

Button:focus {
    background: $glitch_red;
    text-style: bold reverse blink;
}

/* Input field styles */
Input {
    background: $midnight_blue 90%;
    border: solid $electric_cyan;
    color: $crt_green;
}

Input:focus {
    border: double $hot_pink;
    background: $deep_purple;
}

/* Text area for conversation */
.conversation-area {
    background: $vhs_static 10%;
    border: solid $grid_cyan;
    padding: 1;
    scrollbar-background: $deep_purple;
    scrollbar-color: $hot_pink;
}

/* Loading animation container */
.loading-container {
    content-align: center middle;
    background: $midnight_blue 80%;
    border: solid $electric_cyan;
}

/* Error message styling */
.error-message {
    background: $glitch_red 20%;
    border: double $glitch_red;
    color: $hot_pink;
    text-style: bold blink;
}

/* Success message styling */
.success-message {
    background: $crt_green 20%;
    border: double $laser_lime;
    color: $electric_cyan;
    text-style: bold;
}

/* Glitch text effect */
.glitch-text {
    text-style: bold;
    color: $hot_pink;
    text-opacity: 90%;
}

.glitch-text:hover {
    color: $electric_cyan;
    text-style: bold reverse;
}

/* Floating elements */
.floating {
    offset: 0 -1;
    layer: above;
}

/* VHS static overlay */
.vhs-static {
    opacity: 5%;
    background: $vhs_static;
}

/* Japanese text styling */
.japanese-text {
    color: $vapor_pink;
    text-style: bold;
    text-align: center;
}

/* Modal dialog styling */
ModalScreen {
    background: $vhs_static 80%;
}

.dialog {
    background: $midnight_blue;
    border: double $hot_pink;
    padding: 2;
}

/* Footer status bar */
.status-bar {
    dock: bottom;
    height: 3;
    background: $deep_purple;
    border-top: thick $electric_cyan;
}

/* Title bar */
.title-bar {
    dock: top;
    height: 3;
    background: $hot_pink;
    content-align: center middle;
    text-style: bold reverse;
}

/* Retro terminal font effect */
.terminal-text {
    color: $crt_green;
    text-style: bold;
}
"""

def get_gradient_text(text: str, start_color: str = "hot_pink", end_color: str = "electric_cyan") -> str:
    """
    Create gradient colored text using ANSI escape codes.
    This is a simplified version - in practice you'd interpolate colors.
    """
    # For now, just alternate between two colors
    result = ""
    colors = [COLORS[start_color], COLORS[end_color]]
    for i, char in enumerate(text):
        color = colors[i % 2]
        # Using Rich markup format that Textual understands
        result += f"[{color}]{char}[/]"
    return result

def get_glitch_text(text: str, glitch_level: float = 0.1) -> str:
    """
    Add glitch effects to text by randomly replacing characters.

    Args:
        text: Original text
        glitch_level: Probability of glitching each character (0.0-1.0)
    """
    import random

    result = ""
    glitch_chars = ASCII_FRAMES["glitch_chars"]

    for char in text:
        if char == " ":
            result += char
        elif random.random() < glitch_level:
            result += random.choice(glitch_chars)
        else:
            result += char

    return result

def create_vhs_static_line(width: int = 80) -> str:
    """Generate a line of VHS static noise."""
    import random
    chars = ["░", "▒", "▓", " ", ".", ":", "█"]
    return "".join(random.choice(chars) for _ in range(width))

def create_grid_pattern(width: int = 20, height: int = 10) -> str:
    """Create a perspective grid pattern for backgrounds."""
    lines = []
    for y in range(height):
        line = ""
        for x in range(width):
            if y == 0 or y == height - 1:
                line += "─"
            elif x == 0 or x == width - 1:
                line += "│"
            elif (x + y) % 4 == 0:
                line += "┼"
            elif x % 2 == 0:
                line += "│"
            elif y % 2 == 0:
                line += "─"
            else:
                line += " "
        lines.append(line)
    return "\n".join(lines)

# Color interpolation for smooth gradients
def interpolate_color(color1: str, color2: str, factor: float) -> str:
    """
    Interpolate between two hex colors.

    Args:
        color1: Starting color in hex format
        color2: Ending color in hex format
        factor: Interpolation factor (0.0 = color1, 1.0 = color2)
    """
    # Remove '#' if present
    color1 = color1.lstrip('#')
    color2 = color2.lstrip('#')

    # Convert to RGB
    r1, g1, b1 = int(color1[0:2], 16), int(color1[2:4], 16), int(color1[4:6], 16)
    r2, g2, b2 = int(color2[0:2], 16), int(color2[2:4], 16), int(color2[4:6], 16)

    # Interpolate
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)

    # Convert back to hex
    return f"#{r:02x}{g:02x}{b:02x}"

def create_sunset_gradient(steps: int = 10) -> list[str]:
    """Create a sunset gradient color palette."""
    colors = []
    sunset_colors = [
        COLORS["deep_purple"],
        COLORS["neon_purple"],
        COLORS["hot_pink"],
        COLORS["sunset_orange"],
        COLORS["vapor_pink"],
    ]

    for i in range(len(sunset_colors) - 1):
        for j in range(steps // (len(sunset_colors) - 1)):
            factor = j / (steps // (len(sunset_colors) - 1))
            colors.append(interpolate_color(sunset_colors[i], sunset_colors[i + 1], factor))

    return colors