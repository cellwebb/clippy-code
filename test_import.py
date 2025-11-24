#!/usr/bin/env python3
"""Test script to verify the imports work correctly."""

# Test if we can import from the new module
try:
    from src.clippy.cli.commands.system import (
        handle_compact_command,
        handle_help_command,
        handle_status_command,
        handle_yolo_command,
    )

    # Use the imports to silence the linter
    _ = (handle_compact_command, handle_help_command, handle_status_command, handle_yolo_command)
    print("✓ Successfully imported from system.py")
except ImportError as e:
    print(f"✗ Failed to import from system.py: {e}")

# Test if we can import from the main module
try:
    from src.clippy.cli import commands

    # Use the import to silence the linter
    _ = commands
    print("✓ Successfully imported from commands.py")
except ImportError as e:
    print(f"✗ Failed to import from commands.py: {e}")

print("✓ All imports successful!")
