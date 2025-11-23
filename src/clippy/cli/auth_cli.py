"""CLI for authenticating Claude Code OAuth tokens.

Provides a command to authenticate and re-authenticate Claude Code subscriptions.
"""

import logging
import os
import sys

from rich.console import Console

from ..oauth.claude_code import authenticate_and_save, load_stored_token

logger = logging.getLogger(__name__)
console = Console()


def auth(quiet: bool = False, log_level: str = "INFO") -> None:
    """Authenticate Claude Code OAuth token.

    This command allows you to authenticate or re-authenticate your
    Claude Code OAuth token when it expires or you want to refresh it.
    It opens a browser window for the OAuth flow and saves the token
    to ~/.clippy/.env.

    The token is used by the claude-code provider to access your
    Claude Code subscription instead of requiring an Anthropic API key.

    Examples:
        clippy auth                    # Interactive authentication
        clippy auth --quiet            # Quiet mode
        clippy auth --log-level DEBUG  # Debug logging
    """
    # Setup logging
    if quiet:
        effective_log_level = "ERROR"
    else:
        effective_log_level = log_level

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, effective_log_level.upper()),
        format="%(levelname)s: %(message)s" if quiet else "%(name)s - %(levelname)s - %(message)s",
    )

    # Check if there's an existing token
    existing_token = load_stored_token()
    if existing_token and not quiet:
        console.print("✓ Found existing Claude Code access token.")
        console.print()

    if not quiet:
        console.print("🔐 Starting Claude Code OAuth authentication...")
        console.print("   Your browser will open automatically")
        console.print("   (Waiting up to 3 minutes for callback)")
        console.print()

    # Perform OAuth authentication
    success = authenticate_and_save(quiet=quiet)

    if success:
        if not quiet:
            console.print("✅ Claude Code authentication completed successfully!")
            console.print("   Your new token has been saved and is ready to use.")
            console.print()
            console.print("💡 You can now use Claude Code models:")
            console.print("   • clippy-code --model claude-code:claude-sonnet-4-5")
            console.print("   • /model add claude-code claude-sonnet-4-5 --name claude-sonnet")
    else:
        console.print("❌ Claude Code authentication failed.")
        console.print("   Please try again or check your network connection.")
        sys.exit(1)


def status() -> None:
    """Check Claude Code OAuth authentication status."""
    token = load_stored_token()
    
    if token:
        console.print("✅ Claude Code OAuth token is configured")
        console.print("   Token is stored in ~/.clippy/.env")
        
        # Check if it's set in the environment
        env_token = os.getenv("CLAUDE_CODE_ACCESS_TOKEN")
        if env_token:
            console.print("✅ Token is loaded in current environment")
        else:
            console.print("⚠️  Token not found in current environment")
            console.print("   You may need to restart your session or source ~/.clippy/.env")
    else:
        console.print("❌ No Claude Code OAuth token found")
        console.print("   Run 'clippy auth' to authenticate")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "auth":
        quiet = "--quiet" in sys.argv or "-q" in sys.argv
        log_level = "INFO"
        for i, arg in enumerate(sys.argv):
            if arg == "--log-level" and i + 1 < len(sys.argv):
                log_level = sys.argv[i + 1]
        auth(quiet=quiet, log_level=log_level)
    elif len(sys.argv) > 1 and sys.argv[1] == "status":
        status()
    else:
        print("Usage: python auth_cli.py [auth|status]")
        sys.exit(1)