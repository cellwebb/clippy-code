"""
Vaporwave Clippy TUI - Main application bringing nostalgic dreams to life 【アプリ】
"""

import asyncio
from typing import Optional, List
from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Input, Button, Static, TabbedContent, TabPane
from textual.reactive import reactive
from textual.binding import Binding
from textual.message import Message
from textual import work

from .vaporwave.neon_styles import VAPORWAVE_CSS, COLORS, JAPANESE_TEXT
from .vaporwave.clippy_entity import ClippyEntity, ClippyState
from .vaporwave.crt_display import CRTDisplay, RetroTerminal, Scanlines
from .vaporwave.dream_bubbles import ConversationBubbles, DreamBubble, StatusMessage


class VaporwaveHeader(Static):
    """Custom header with vaporwave aesthetic."""

    DEFAULT_CSS = """
    VaporwaveHeader {
        dock: top;
        height: 3;
        background: #FF10F0;
        content-align: center middle;
        text-style: bold reverse;
    }
    """

    def render(self) -> str:
        """Render the vaporwave header."""
        title = "【ＣＬＩＰＰＹ　２０００】✨ ＤＩＧＩＴＡＬ　ＡＳＳＩＳＴＡＮＴ　✨【クリッピー】"
        return title


class VaporwaveFooter(Static):
    """Custom footer with status information."""

    DEFAULT_CSS = """
    VaporwaveFooter {
        dock: bottom;
        height: 3;
        background: #1A0033;
        padding: 0 1;
    }
    """

    status_text = reactive("ＲＥＡＤＹ")
    channel = reactive(1)

    def render(self) -> str:
        """Render the footer with status."""
        left = f"CH{self.channel:02d}"
        center = self.status_text
        right = "【ＥＳＣ】ＭＥＮＵ　【Ｆ１】ＨＥＬＰ"

        # Create a formatted status bar
        width = self.size.width if self.size else 80
        padding = (width - len(left) - len(center) - len(right)) // 2

        return f"{left}{' ' * padding}{center}{' ' * padding}{right}"


class MessageInput(Input):
    """Styled input for user messages."""

    DEFAULT_CSS = """
    MessageInput {
        dock: bottom;
        height: 3;
        margin: 1 2;
        background: #0D0221 90%;
        border: solid #00FFFF;
        padding: 0 1;
    }

    MessageInput:focus {
        border: double #FF10F0;
        background: #1A0033 80%;
    }
    """

    def __init__(self, placeholder: str = "Type your message... (Enter to send)") -> None:
        """Initialize the message input."""
        super().__init__(placeholder=placeholder)


class ChannelTab(Static):
    """A channel tab in the vaporwave style."""

    def __init__(self, label: str, channel_id: int) -> None:
        """Initialize a channel tab."""
        super().__init__(label)
        self.channel_id = channel_id


class AddResponseMessage(Message):
    """Message to safely add response from background thread."""
    
    def __init__(self, response: str, message_type: str = "assistant") -> None:
        self.response = response
        self.message_type = message_type
        super().__init__()


class VaporwaveClippy(App):
    """
    The main Vaporwave Clippy TUI application.
    A nostalgic, dreamy interface for the AI assistant.
    """

    CSS = VAPORWAVE_CSS

    BINDINGS = [
        Binding("escape", "toggle_menu", "Menu"),
        Binding("f1", "show_help", "Help"),
        Binding("ctrl+c", "quit", "Exit"),
        Binding("ctrl+n", "new_chat", "New Chat"),
        Binding("ctrl+t", "next_channel", "Next Channel"),
        Binding("ctrl+shift+t", "prev_channel", "Previous Channel"),
        Binding("ctrl+g", "toggle_glitch", "Glitch Mode"),
        Binding("ctrl+v", "full_vaporwave", "Full Aesthetic"),
    ]

    # Application state
    current_channel = reactive(1)
    messages: List[tuple[str, str]] = []  # (role, content) pairs
    glitch_mode = reactive(False)
    full_vaporwave = reactive(False)

    def __init__(self, agent=None) -> None:
        """
        Initialize the Vaporwave Clippy app.

        Args:
            agent: The ClippyAgent instance for handling AI interactions
        """
        super().__init__()
        self.agent = agent
        self.clippy_entity: Optional[ClippyEntity] = None
        self.conversation: Optional[ConversationBubbles] = None
        self.status_message: Optional[StatusMessage] = None
        self.input_field: Optional[MessageInput] = None
        self.processing = False
        self.processing_task = None  # Track the current processing task

    def compose(self) -> ComposeResult:
        """Compose the vaporwave UI layout."""
        # Custom header
        yield VaporwaveHeader()

        # Main content area with CRT effect
        with CRTDisplay(classes="crt-main"):
            # Add scanline overlay
            yield Scanlines()

            # Main layout
            with Horizontal():
                # Left panel - Clippy
                with Vertical(classes="clippy-panel", id="clippy-panel"):
                    self.clippy_entity = ClippyEntity(ClippyState.IDLE)
                    yield self.clippy_entity
                    yield Static(
                        "【ＨＥＬＰＥＲ】\nI'm here to assist\nwith your code dreams",
                        classes="clippy-status"
                    )

                # Right panel - Conversation
                with Vertical(classes="conversation-panel"):
                    # Channel tabs
                    with TabbedContent(initial="chat", classes="channel-tabs"):
                        with TabPane("【ＣＨＡＴ】", id="chat"):
                            self.conversation = ConversationBubbles()
                            yield self.conversation

                        with TabPane("【ＴＯＯＬＳ】", id="tools"):
                            yield Static("Tool execution logs will appear here")

                        with TabPane("【ＭＥＭＯＲＹ】", id="memory"):
                            yield Static("Conversation history stored on VHS tapes")

                        with TabPane("【４０４】", id="void"):
                            yield Static(
                                "【ＶＯＩＤ】\n"
                                "You've found the digital void\n"
                                "Where lost data dreams...\n"
                                "リアリティは幻想です",
                                classes="void-text"
                            )

            # Input area
            self.input_field = MessageInput()
            yield self.input_field

            # Status message overlay
            self.status_message = StatusMessage("System initialized", "success")
            yield self.status_message

        # Custom footer
        yield VaporwaveFooter()

    def on_add_response_message(self, message: AddResponseMessage) -> None:
        """Handle response message from background thread."""
        if self.conversation:
            self.conversation.add_message(message.response, message.message_type)

    async def on_mount(self) -> None:
        """Initialize the app when mounted."""
        # Show boot sequence
        await self.show_boot_sequence()

        # Welcome message from Clippy with enhanced styling
        if self.conversation:
            self.conversation.add_message(
                f"Welcome to the digital sunset! 🌆 "
                "I'm your vaporwave assistant, ready to help you code through the neon haze. "
                "What dreams shall we synthesize today?",
                "assistant"
            )

        # Set Clippy to idle with occasional animations
        if self.clippy_entity:
            self.clippy_entity.set_state(ClippyState.IDLE)
            self.set_interval(5.0, self.random_clippy_animation)

    async def show_boot_sequence(self) -> None:
        """Show a subtle retro boot sequence."""
        boot_messages = [
            ("Loading vaporwave interface...", 0.8),
            ("Synthesizing neon colors...", 0.6),
            ("Calibrating CRT effects...", 0.5),
            ("System ready 🌟", 0.3),
        ]

        for message, delay in boot_messages:
            if self.status_message:
                self.status_message.show_message(message, "loading")
            await asyncio.sleep(delay)

        if self.status_message:
            self.status_message.show_message("Welcome to the digital dreamscape", "success", 2.0)

    def random_clippy_animation(self) -> None:
        """Trigger random Clippy animations for liveliness."""
        if self.clippy_entity and not self.processing:
            import random
            animations = [
                (ClippyState.IDLE, 0.7),
                (ClippyState.DREAMING, 0.1),
                (ClippyState.VAPORWAVE, 0.1),
                (ClippyState.QUESTIONING, 0.1),
            ]

            state, _ = random.choices(
                animations,
                weights=[w for _, w in animations]
            )[0]

            if state != ClippyState.IDLE:
                self.clippy_entity.set_state(state, duration=2.0)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user message submission."""
        message = event.value.strip()
        if not message:
            return

        # Clear input
        if self.input_field:
            self.input_field.value = ""

        # Handle slash commands
        if message.startswith('/'):
            await self.handle_slash_command(message)
            return

        # Add user message to conversation
        if self.conversation:
            self.conversation.add_message(message, "user")

        # Store message
        self.messages.append(("user", message))

        # Cancel any existing processing task
        if self.processing_task and not self.processing_task.done():
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass

        # Process with agent - run as background task
        self.processing_task = asyncio.create_task(self.process_message(message))

    async def handle_slash_command(self, command: str) -> None:
        """Handle slash commands."""
        cmd = command.lower().split()[0]

        if cmd in ['/quit', '/exit']:
            self.exit()
        elif cmd == '/help':
            self.action_show_help()
        elif cmd == '/reset':
            self.action_new_chat()
        elif cmd == '/clear':
            self.action_new_chat()
        else:
            self.notify(f"Unknown command: {cmd}", severity="warning")

    async def process_message(self, message: str) -> None:
        """Process message with the agent."""
        self.processing = True

        try:
            # Update Clippy state
            if self.clippy_entity:
                self.clippy_entity.start_thinking()

            # Check if agent exists
            if self.agent:
                response = await self.call_agent(message)
            else:
                # Simulated response for testing
                await asyncio.sleep(1.5)
                response = self.generate_vaporwave_response(message)

            # Store response
            self.messages.append(("assistant", response))

            # Add response to conversation - use Post message to main thread
            self.post_message(AddResponseMessage(response))

            # Update Clippy state
            if self.clippy_entity:
                self.clippy_entity.trigger_success()

        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            return
        except Exception as e:
            self.notify(f"Error processing message: {e}", severity="error")
            # Also add error message safely
            error_msg = f"ERROR: {str(e)}\nリアリティは壊れました"
            self.post_message(AddResponseMessage(error_msg, "system"))
        finally:
            self.processing = False

    async def call_agent(self, message: str):
        """Call the actual agent for processing."""
        try:
            # The agent.run() method handles everything:
            # - Adding user message to history
            # - Calling LLM
            # - Handling tool calls with approvals
            # - Returning the final response

            # Run in a thread to avoid blocking the UI
            import asyncio
            from functools import partial

            # Create a partial with auto_approve_all
            agent_call = partial(self.agent.run, message, auto_approve_all=True)

            # Run in thread pool and use call_soon_threadsafe for the response
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, agent_call)

            return response

        except asyncio.CancelledError:
            # Task was cancelled, propagate up
            raise
        except Exception as e:
            self.notify(f"Agent error: {e}", severity="error")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}"

    def generate_vaporwave_response(self, message: str) -> str:
        """Generate a vaporwave-themed response for testing."""
        import random

        responses = [
            f"Ah yes, '{message}'... reminds me of digital sunsets and neon dreams. "
            "Let me help you navigate through this vapor...",

            f"'{message}' resonates with the aesthetic frequency. "
            f"{JAPANESE_TEXT['thinking']}... I sense you seek the path through the digital void.",

            "Your words echo through the CRT display... "
            "Together we'll synthesize the perfect solution in this retro-future dreamscape.",

            f"ERROR_404_REALITY_NOT_FOUND... Just kidding! "
            f"Let me process '{message}' through my vaporwave neural networks...",

            "It looks like you're trying to escape into the digital sunset. "
            "Would you like help with that? ✨",
        ]

        return random.choice(responses)

    def action_quit(self) -> None:
        """Quit the application with proper cleanup."""
        # Cancel any running tasks
        if self.processing_task and not self.processing_task.done():
            self.processing_task.cancel()
        
        self.exit()

    def action_toggle_menu(self) -> None:
        """Toggle the menu display."""
        self.notify("Menu not yet implemented")

    def action_show_help(self) -> None:
        """Show help dialog."""
        if self.conversation:
            help_text = """
【ＨＥＬＰ】Command Reference:

Ctrl+N : New conversation
Ctrl+T : Next channel
Ctrl+G : Toggle glitch mode
Ctrl+V : Full vaporwave mode
ESC    : Menu
F1     : This help
Ctrl+C : Exit

Type 'AESTHETIC' for a surprise!
            """
            self.conversation.add_message(help_text, "system")

    def action_new_chat(self) -> None:
        """Start a new chat."""
        self.messages.clear()
        if self.conversation:
            self.conversation.clear_conversation()
            self.conversation.add_message(
                "Memory wiped. Starting fresh in the digital void... "
                f"{JAPANESE_TEXT['welcome']} back!",
                "assistant"
            )

    def action_next_channel(self) -> None:
        """Switch to next channel."""
        self.current_channel = (self.current_channel % 4) + 1
        self.notify(f"Switched to channel {self.current_channel}")

    def action_prev_channel(self) -> None:
        """Switch to previous channel."""
        self.current_channel = ((self.current_channel - 2) % 4) + 1
        self.notify(f"Switched to channel {self.current_channel}")

    def action_toggle_glitch(self) -> None:
        """Toggle glitch mode."""
        self.glitch_mode = not self.glitch_mode
        if self.clippy_entity:
            if self.glitch_mode:
                self.clippy_entity.set_state(ClippyState.GLITCHING)
                self.notify("G L I T C H  M O D E  A C T I V A T E D")
            else:
                self.clippy_entity.set_state(ClippyState.IDLE)
                self.notify("Glitch mode deactivated")

    def action_full_vaporwave(self) -> None:
        """Activate full vaporwave aesthetic."""
        self.full_vaporwave = not self.full_vaporwave
        if self.clippy_entity:
            if self.full_vaporwave:
                self.clippy_entity.enter_vaporwave_mode()
                self.notify("【ＦＵＬＬ　ＡＥＳＴＨＥＴＩＣ　ＭＯＤＥ】")
                if self.conversation:
                    self.conversation.add_message(
                        f"{JAPANESE_TEXT['aesthetic']} MODE ACTIVATED\n"
                        "Reality.exe has stopped responding...\n"
                        "Welcome to the V A P O R W A V E",
                        "system"
                    )
            else:
                self.clippy_entity.set_state(ClippyState.IDLE)
                self.notify("Returning to normal reality...")


def run_vaporwave_clippy(agent=None):
    """
    Run the Vaporwave Clippy TUI application.

    Args:
        agent: Optional ClippyAgent instance for AI functionality
    """
    app = VaporwaveClippy(agent=agent)
    app.run()