"""Argument parser for CLI."""

import argparse


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="clippy-code - A CLI coding agent powered by OpenAI-compatible LLMs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "prompt",
        nargs="*",
        help="The task or question for clippy-code (one-shot mode)",
    )

    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Auto-approve all actions (use with caution!)",
    )

    parser.add_argument(
        "--yolo",
        action="store_true",
        help="YOLO mode - auto-approve everything without any prompts (use with extreme caution!)",
    )

    parser.add_argument(
        "--model",
        type=str,
        help="Model to use (e.g., gpt-5, llama3.1-8b for Cerebras)",
    )

    parser.add_argument(
        "--base-url",
        type=str,
        help="Base URL for OpenAI-compatible API (e.g., https://api.cerebras.ai/v1)",
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to custom permission config file",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging (shows retry attempts and API errors)",
    )

    return parser
