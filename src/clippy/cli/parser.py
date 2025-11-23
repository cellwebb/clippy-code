"""Argument parser for CLI."""

import argparse


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="clippy-code - A CLI coding agent powered by OpenAI-compatible LLMs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # General options (for main app, not subcommands)
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

    
    # Add subcommands after general options
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=False)
    
    # Auth command
    auth_parser = subparsers.add_parser(
        "auth",
        help="Authenticate with Claude Code OAuth",
        description="Authenticate or re-authenticate your Claude Code OAuth token"
    )
    auth_parser.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress non-error output"
    )
    auth_parser.add_argument(
        "--log-level",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        default="INFO",
        help="Set log level (default: INFO)"
    )
    
    # Auth status command
    status_parser = subparsers.add_parser(
        "auth-status", 
        help="Check Claude Code OAuth authentication status",
        description="Check if Claude Code OAuth token is configured"
    )

    # Add prompt argument to main parser (not subcommands)
    parser.add_argument(
        "prompt",
        nargs="*",
        help="The task or question for clippy-code (one-shot mode)",
    )

    return parser


def parse_args(argv):
    """Parse arguments with special handling for prompts vs subcommands."""
    # If no arguments provided, return defaults
    if not argv:
        args = argparse.Namespace()
        args.prompt = []
        args.yes = False
        args.yolo = False
        args.verbose = False
        args.model = None
        args.base_url = None
        args.config = None
        
        args.command = None
        return args
    
    # Check if first argument is a known command
    known_commands = ["auth", "auth-status"]
    if argv[0] in known_commands:
        # Parse normally for commands
        parser = create_parser()
        return parser.parse_args(argv)
    else:
        # For prompts, manually parse options to avoid subparser issues
        parser = argparse.ArgumentParser()
        parser.add_argument("-y", "--yes", action="store_true")
        parser.add_argument("--yolo", action="store_true")
        parser.add_argument("--model", type=str)
        parser.add_argument("--base-url", type=str)
        parser.add_argument("--config", type=str)
        parser.add_argument("-v", "--verbose", action="store_true")
        
        parser.add_argument("prompt", nargs="*")
        
        args = parser.parse_args(argv)
        args.command = None
        return args