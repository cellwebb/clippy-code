#!/usr/bin/env python3

# Test script to verify imports work
import sys

sys.path.insert(0, "src")

try:
    from clippy.llm.openai import OpenAIProvider, _is_reasoner_model

    print("✓ Imports successful")

    # Test basic functionality
    provider = OpenAIProvider()
    print(f"✓ Provider created with base_url: {provider.base_url}")

    # Test reasoner function
    assert _is_reasoner_model("deepseek-r1") is True
    assert _is_reasoner_model("gpt-4") is False
    print("✓ Reasoner model detection works")

    # Test responses API detection
    assert provider._should_use_responses_api("code-davinci-002") is True
    assert provider._should_use_responses_api("gpt-4") is False
    print("✓ Responses API detection works")

    print("\n✓ All basic functionality tests passed!")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
