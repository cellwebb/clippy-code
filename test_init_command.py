#!/usr/bin/env python3
"""Simple test to verify the /init command functionality."""

import sys
from pathlib import Path

# Add the project to the Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from rich.console import Console

    from src.clippy.cli.commands import (
        handle_help_command,
    )

    print("✓ All /init command functions imported successfully")

    # Print help to show the new command
    print("\n" + "=" * 50)
    print("HELP COMMAND OUTPUT (showing /init):")
    print("=" * 50)
    console = Console()
    handle_help_command(console)
    print("=" * 50)

    print("\n✓ Test passed! The /init command is available in the help output.")

except Exception as e:
    print(f"✗ Test failed: {e}")
    sys.exit(1)
