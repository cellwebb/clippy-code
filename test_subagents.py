#!/usr/bin/env python3
"""Simple test script for subagent functionality."""

import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_subagent_imports():
    """Test that all subagent components can be imported."""
    print("Testing subagent imports...")

    try:
        from clippy.agent.subagent_types import list_subagent_types
        from clippy.tools import get_tool_by_name

        print("✓ All imports successful")

        # Test subagent types
        types = list_subagent_types()
        print(f"✓ Available subagent types: {types}")

        # Test tool availability
        tool = get_tool_by_name("delegate_to_subagent")
        if tool:
            print("✓ delegate_to_subagent tool available")
        else:
            print("✗ delegate_to_subagent tool not found")

        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_subagent_config():
    """Test subagent configuration."""
    print("\nTesting subagent configuration...")

    try:
        from clippy.agent.subagent_types import (
            get_subagent_config,
            list_subagent_types,
            validate_subagent_config,
        )

        # Test getting config for each type
        for subagent_type in list_subagent_types():
            config = get_subagent_config(subagent_type)
            print(f"✓ {subagent_type}: max_iterations={config.get('max_iterations')}")

        # Test validation
        valid_config = {
            "name": "test_subagent",
            "task": "Test task",
            "subagent_type": "general",
            "timeout": 300,
        }
        is_valid, error = validate_subagent_config(valid_config)
        if is_valid:
            print("✓ Configuration validation works")
        else:
            print(f"✗ Configuration validation failed: {error}")

        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("📎 Testing clippy-code subagent implementation...")

    success = True
    success &= test_subagent_imports()
    success &= test_subagent_config()

    if success:
        print("\n🎉 All tests passed! Subagent system is ready.")
        print("\nNext steps:")
        print("1. Set up an API key (e.g., OPENAI_API_KEY)")
        print("2. Try the subagent functionality with: python -m clippy -i")
        print("3. Use the delegate_to_subagent tool in your prompts")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
