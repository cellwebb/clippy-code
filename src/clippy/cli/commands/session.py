"""Session control commands for interactive CLI mode."""

import json
import shlex
import time
from typing import Any, Literal

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel

from ...agent import ClippyAgent

CommandResult = Literal["continue", "break", "run"]


def _format_time_ago(timestamp: float) -> str:
    """Format a timestamp as 'X time ago' string."""
    now = time.time()
    diff = now - timestamp

    if diff < 60:
        return "just now" if diff < 10 else f"{int(diff)} seconds ago"
    elif diff < 3600:
        minutes = int(diff / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < 86400:
        hours = int(diff / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < 604800:
        days = int(diff / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        weeks = int(diff / 604800)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"


def _get_all_conversations_with_timestamps(agent: ClippyAgent) -> list[dict[str, Any]]:
    """Get all conversations with their data including timestamps."""
    conversations = []

    try:
        conversation_files = agent.conversations_dir.glob("*.json")
        for conv_file in conversation_files:
            try:
                with open(conv_file) as f:
                    data = json.load(f)

                conversations.append(
                    {
                        "name": conv_file.stem,
                        "timestamp": data.get("timestamp", 0),
                        "model": data.get("model", "unknown"),
                        "message_count": len(data.get("conversation_history", [])),
                    }
                )
            except (json.JSONDecodeError, FileNotFoundError):
                # Handle empty or corrupted files - use file modification time
                try:
                    conversations.append(
                        {
                            "name": conv_file.stem,
                            "timestamp": conv_file.stat().st_mtime,  # Use file modification time
                            "model": "unknown",
                            "message_count": 0,
                        }
                    )
                except Exception:
                    # If we can't even get file stats, skip this file
                    continue

        # Sort by timestamp (most recent first)
        conversations.sort(key=lambda x: x["timestamp"], reverse=True)

    except Exception:
        # If we can't read the directory, return empty list
        pass

    return conversations


def _display_conversation_history(agent: ClippyAgent, console: Console) -> None:
    """Display the conversation history for scrolling back."""
    history = agent.conversation_history

    if not history:
        console.print("[dim]No messages in this conversation yet.[/dim]")
        return

    # Skip system message for display (too verbose)
    display_history = [msg for msg in history if msg.get("role") != "system"]

    if not display_history:
        console.print("[dim]No user messages in this conversation yet.[/dim]")
        return

    # Show recent messages (last 20 to avoid overwhelming output)
    recent_messages = display_history[-20:] if len(display_history) > 20 else display_history

    console.print(
        f"\n[bold cyan]Conversation History ({len(display_history)} messages):[/bold cyan]"
    )
    console.print("[dim]Scroll up to see earlier messages[/dim]\n")

    for i, msg in enumerate(recent_messages):
        role = msg.get("role", "unknown")
        content = msg.get("content", "").strip()

        if not content:
            continue

        # Format based on role
        if role == "user":
            console.print(f"[bold green]You:[/bold green] {escape(content)}")
        elif role == "assistant":
            # Truncate very long assistant responses for display
            if len(content) > 500:
                display_content = escape(content[:500]) + "\n[dim]... (truncated)[/dim]"
            else:
                display_content = escape(content)
            console.print(f"[bold blue]Clippy:[/bold blue] {display_content}")
        elif role == "tool":
            console.print(
                f"[bold yellow]Tool Result:[/bold yellow] "
                f"[dim]{escape(content[:200])}{'...' if len(content) > 200 else ''}[/dim]"
            )
        else:
            console.print(
                f"[dim]{role}: {escape(content[:100])}{'...' if len(content) > 100 else ''}[/dim]"
            )

        console.print("")  # Add spacing between messages

    # Show if there are more messages not displayed
    if len(display_history) > 20:
        console.print(
            f"[dim]... and {len(display_history) - 20} earlier messages not shown[/dim]\n"
        )

    console.print("[dim]You can now continue the conversation below:[/dim]")


def handle_exit_command(console: Console) -> CommandResult:
    """Handle /exit or /quit commands."""
    console.print("[yellow]Goodbye![/yellow]")
    return "break"


def handle_reset_command(agent: ClippyAgent, console: Console) -> CommandResult:
    """Handle /reset, /clear, or /new commands."""
    agent.reset_conversation()
    console.print("[green]Conversation history reset[/green]")
    return "continue"


def handle_resume_command(agent: ClippyAgent, console: Console, command_args: str) -> CommandResult:
    """Handle /resume command."""
    # Import dynamically to respect monkeypatching in tests
    import sys

    get_conversations_func = sys.modules[
        "clippy.cli.commands"
    ]._get_all_conversations_with_timestamps

    # Parse command arguments
    args = shlex.split(command_args) if command_args else []

    # If no name specified, show interactive selection of conversations
    if not args:
        conversations = get_conversations_func(agent)
        if not conversations:
            console.print("[yellow]No saved conversations found.[/yellow]")
            return "continue"

        # Import questionary for interactive selection
        try:
            import questionary
        except ImportError:
            # Fallback to showing available conversations with timestamps
            console.print(
                "[yellow]Interactive selection not available. Available conversations:[/yellow]"
            )
            for conv in conversations:
                time_ago = _format_time_ago(conv["timestamp"])
                msg_count = conv["message_count"]
                console.print(
                    f"  [cyan]{conv['name']}[/cyan] - {time_ago} "
                    f"([dim]{msg_count} message{'s' if msg_count != 1 else ''}[/dim])"
                )
            console.print("[dim]Usage: /resume <name>[/dim]")
            return "continue"

        # Create choices with detailed information for questionary
        choices = []
        for conv in conversations:
            time_ago = _format_time_ago(conv["timestamp"])
            msg_count = conv["message_count"]
            display_name = f"{conv['name']} ({time_ago}, {msg_count} messages)"
            choices.append(questionary.Choice(title=display_name, value=conv["name"]))

        # Show interactive selection
        conversation_name = questionary.select(
            "Select a conversation to resume:",
            choices=choices,
            instruction="Use arrow keys to navigate, Enter to select",
        ).ask()

        # If user cancelled the selection
        if conversation_name is None:
            console.print("[yellow]Resume cancelled.[/yellow]")
            return "continue"
    else:
        conversation_name = args[0]

    # Load the conversation
    success, message = agent.load_conversation(conversation_name)

    if success:
        console.print(f"[green]✓ {escape(message)}[/green]")

        # Show the conversation history so user can scroll back
        _display_conversation_history(agent, console)

        # Show info about the loaded conversation
        conversations = get_conversations_func(agent)
        if conversations:
            names = [conv["name"] for conv in conversations[:5]]  # Show first 5
            if len(conversations) > 5:
                names.append(f"...and {len(conversations) - 5} more")
            console.print(f"[dim]Available conversations {', '.join(names)}[/dim]")
    else:
        console.print(f"[red]✗ {escape(message)}[/red]")
        # Show available conversations if loading failed
        conversations = get_conversations_func(agent)
        if conversations:
            names = [conv["name"] for conv in conversations[:5]]  # Show first 5
            if len(conversations) > 5:
                names.append(f"...and {len(conversations) - 5} more")
            console.print(f"[dim]Available conversations {', '.join(names)}[/dim]")
        else:
            console.print("[dim]No saved conversations found.[/dim]")

    return "continue"


def handle_truncate_command(
    agent: ClippyAgent, console: Console, command_args: str
) -> CommandResult:
    """Handle /truncate command."""
    # Parse command arguments
    args = command_args.strip().split()

    if len(args) < 1:
        console.print("[red]Usage: /truncate <count> [option][/red]")
        console.print("[dim]Options: --keep-recent (default), --keep-older[/dim]")
        return "continue"

    try:
        count = int(args[0])
        if count < 0:
            raise ValueError()
    except ValueError:
        console.print("[red]Error: <count> must be a non-negative integer[/red]")
        return "continue"

    # Parse option
    keep_recent = True  # default
    if len(args) > 1:
        option = args[1].lower()
        if option == "--keep-recent":
            keep_recent = True
        elif option == "--keep-older":
            keep_recent = False
        else:
            console.print(f"[red]Error: Unknown option '{args[1]}'[/red]")
            console.print("[dim]Available options: --keep-recent, --keep-older[/dim]")
            return "continue"

    # Get current conversation
    history = agent.conversation_history

    # Filter out system messages for counting and truncation
    non_system_history = [msg for msg in history if msg.get("role") != "system"]

    if len(non_system_history) <= count and count > 0:
        console.print(
            f"[yellow]Conversation already has {len(non_system_history)} "
            f"messages (≤ {count})[/yellow]"
        )
        return "continue"

    # Special case: count == 0 means keep only system messages
    if count == 0:
        new_history = [msg for msg in history if msg.get("role") == "system"]
        removed_count = len(non_system_history)

        # Update conversation
        agent.conversation_history = new_history

        # Show result
        console.print(
            Panel.fit(
                f"[bold green]✓ Conversation Truncated[/bold green]\n\n"
                f"[bold]Messages Removed:[/bold] {removed_count}\n"
                f"[bold]Messages Kept:[/bold] 0 (system messages only)\n"
                f"[bold]Total Messages:[/bold] {len(new_history)}\n\n"
                f"[dim]Use /status to see the updated token count.[/dim]",
                title="Truncate Complete",
                border_style="green",
            )
        )
        return "continue"

    # Perform truncation
    if keep_recent:
        # Keep the most recent messages
        new_history = [msg for msg in history if msg.get("role") == "system"] + non_system_history[
            -count:
        ]
        removed_count = len(non_system_history) - count
    else:
        # Keep the oldest messages
        new_history = [msg for msg in history if msg.get("role") == "system"] + non_system_history[
            :count
        ]
        removed_count = len(non_system_history) - count

    # Update conversation
    agent.conversation_history = new_history

    # Show result
    console.print(
        Panel.fit(
            f"[bold green]✓ Conversation Truncated[/bold green]\n\n"
            f"[bold]Messages Removed:[/bold] {removed_count}\n"
            f"[bold]Messages Kept:[/bold] {count} ({'recent' if keep_recent else 'older'})\n"
            f"[bold]Total Messages:[/bold] {len(new_history)}\n\n"
            f"[dim]Use /status to see the updated token count.[/dim]",
            title="Truncate Complete",
            border_style="green",
        )
    )

    return "continue"
