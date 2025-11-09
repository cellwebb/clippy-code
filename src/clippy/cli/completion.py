"""Tab completion system for clippy-code commands."""

import os
from collections.abc import Callable
from glob import glob
from typing import Any

from prompt_toolkit.completion import (
    Completer,
    Completion,
    WordCompleter,
)
from prompt_toolkit.document import Document

from ..agent.subagent_types import list_subagent_types
from ..models import list_available_models, list_available_providers
from ..permissions import ActionType


class ClippyCommandCompleter(Completer):
    """Advanced command completer for clippy-code slash commands."""

    def __init__(self, agent: Any = None) -> None:
        self.agent = agent
        self._setup_base_commands()
        self._setup_dynamic_completers()

    def _setup_base_commands(self) -> None:
        """Setup basic command definitions."""
        self.base_commands: dict[str, dict[str, Any]] = {
            "help": {
                "description": "Show help message",
                "completer": None,
            },
            "exit": {
                "description": "Exit clippy-code",
                "alias": ["quit"],
                "completer": None,
            },
            "resume": {
                "description": "Resume a saved conversation",
                "completer": None,
                "takes_arg": True,
            },
            "status": {
                "description": "Show token usage and session info",
                "completer": None,
            },
            "compact": {
                "description": "Summarize conversation to reduce context usage",
                "completer": None,
            },
            "truncate": {
                "description": "Truncate conversation history with options",
                "completer": None,
                "takes_arg": True,
            },
            "yolo": {
                "description": "Toggle YOLO mode (auto-approve ALL actions)",
                "completer": None,
            },
            "providers": {
                "description": "List available providers",
                "completer": None,
            },
            "provider": {
                "description": "Show provider details",
                "completer": self._create_provider_completer(),
                "takes_arg": True,
            },
            "model": {
                "description": "Model management",
                "completer": self._create_model_completer(),
                "subcommands": ["list", "add", "remove", "default", "use", "load", "threshold"],
            },
            "auto": {
                "description": "Auto-approval management",
                "completer": self._create_auto_completer(),
                "subcommands": ["list", "revoke", "clear"],
            },
            "subagent": {
                "description": "Subagent configuration",
                "completer": self._create_subagent_completer(),
                "subcommands": ["list", "set", "clear", "reset"],
            },
        }

        # Only add MCP command if MCP servers are configured
        if self._has_mcp_servers():
            self.base_commands["mcp"] = {
                "description": "MCP server management",
                "completer": self._create_mcp_completer(),
                "subcommands": ["list", "tools", "refresh", "allow", "revoke", "enable", "disable"],
            }

    def _create_provider_completer(self) -> WordCompleter:
        """Create completer for provider names."""
        providers = [provider[0] for provider in list_available_providers()]
        return WordCompleter(providers, ignore_case=True)

    def _create_model_completer(self) -> Callable[[], "ModelCommandCompleter"]:
        """Create model command completer."""

        def get_completer() -> "ModelCommandCompleter":
            return ModelCommandCompleter(self.agent)

        return get_completer

    def _create_auto_completer(self) -> Callable[[], "AutoCommandCompleter"]:
        """Create auto command completer."""

        def get_completer() -> "AutoCommandCompleter":
            return AutoCommandCompleter()

        return get_completer

    def _create_mcp_completer(self) -> Callable[[], "MCPCommandCompleter"]:
        """Create MCP command completer."""

        def get_completer() -> "MCPCommandCompleter":
            return MCPCommandCompleter(self.agent)

        return get_completer

    def _create_subagent_completer(self) -> Callable[[], "SubagentCommandCompleter"]:
        """Create subagent command completer."""

        def get_completer() -> "SubagentCommandCompleter":
            return SubagentCommandCompleter()

        return get_completer

    def _has_mcp_servers(self) -> bool:
        """Check if there are any MCP servers configured."""
        if not self.agent or not hasattr(self.agent, "mcp_manager") or not self.agent.mcp_manager:
            return False

        try:
            servers = self.agent.mcp_manager.list_servers()
            return len(servers) > 0
        except Exception:
            # If there's an error accessing MCP manager, assume no servers
            return False

    def _setup_dynamic_completers(self) -> None:
        """Setup completers that need dynamic data."""
        pass  # Will be updated as needed

    def get_completions(self, document: Document, complete_event: Any) -> list[Completion]:
        """Get completions for the current document."""
        text = document.text_before_cursor
        words = text.split()

        # Handle file completion when there's an "@" symbol
        # Find the last occurrence of "@" to handle completion in the middle of text
        last_at_index = text.rfind("@")
        if last_at_index != -1:
            # Get text after the last "@"
            at_prefix = text[last_at_index + 1 :]
            # Only do file completion if the prefix is reasonable (no spaces, not a command)
            if " " not in at_prefix and not at_prefix.startswith("/"):
                return self._get_file_completions_with_position(text, last_at_index)

        # Handle general file completion when no special prefix is used
        # Check if we should offer file completions based on context
        if not text.startswith("/") and len(words) > 0:
            current_word = words[-1] if not text.endswith(" ") else ""
            # Offer file completions if the current word looks like it could be a file reference
            if self._should_offer_file_completion(current_word, text):
                return self._get_file_completions_for_word(current_word)

        # If we're at the beginning and text starts with "/", show base commands
        at_beginning = len(words) == 0 or (len(words) == 1 and not text.endswith(" "))
        if at_beginning and text.startswith("/"):
            return self._get_base_command_completions(text)
        # If we're at the beginning but text doesn't start with "/", don't show slash commands
        elif at_beginning:
            return []

        # If we have a command that starts with "/", get command-specific completions
        if text.startswith("/") and len(words) > 0:
            command = words[0].lstrip("/")
            if command in self.base_commands:
                return self._get_command_specific_completions(command, words, text, complete_event)

        return []

    def _should_offer_file_completion(self, current_word: str, full_text: str) -> bool:
        """Determine if we should offer file completions for the current word."""
        # Don't offer completions for very short words (likely still typing)
        if len(current_word) < 3:
            return False

        # Offer completions if the word contains path separators or file extensions
        if "/" in current_word or "\\" in current_word:
            return True

        # Check common file extensions
        common_extensions = [
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".html",
            ".css",
            ".json",
            ".md",
            ".txt",
            ".yaml",
            ".yml",
            ".toml",
            ".cfg",
            ".conf",
            ".xml",
            ".csv",
            ".log",
        ]

        # Offer completions if word ends with a common extension
        for ext in common_extensions:
            if current_word.endswith(ext):
                return True

        # Offer completions if word matches beginning of known filenames
        try:
            all_files = glob("**/*", recursive=True)
            all_files = [f for f in all_files if os.path.isfile(f)]
            for filename in all_files:
                if filename.startswith(current_word):
                    return True
        except Exception:
            pass

        return False

    def _get_file_completions_for_word(self, word: str) -> list[Completion]:
        """Get file completions for a word without '@' prefix."""
        try:
            matches = glob("**/*", recursive=True)
            # Filter to only include actual files
            matches = [m for m in matches if os.path.isfile(m)]

            completions = []
            for match in matches:
                # Check if the match starts with our word
                if match.startswith(word):
                    completions.append(
                        Completion(
                            text=match,
                            display=match,
                            display_meta="File",
                            start_position=-len(word),  # Replace only the word part
                        )
                    )

            # Sort completions and limit to avoid overwhelming user
            return sorted(completions, key=lambda c: c.text)[:30]
        except Exception:
            # If there's an error, return empty completions
            return []

    def _get_file_completions_with_position(self, text: str, at_index: int) -> list[Completion]:
        """Get completions for file references with proper positioning."""
        # Get text after the "@"
        prefix = text[at_index + 1 :]

        # Find all files in current directory and subdirectories
        try:
            matches = glob("**/*", recursive=True)
            # Filter out directories and hidden files (except .gitignore)
            matches = [
                m
                for m in matches
                if not os.path.isdir(m) and (not m.startswith(".") or m == ".gitignore")
            ]
            # Additional filtering to only include files (in case of symlinks, etc.)
            matches = [m for m in matches if os.path.isfile(m)]

            # If prefix is empty, show a limited number of common files
            if not prefix:
                # Sort by modification time (recent files first) and limit
                matches = sorted(
                    matches,
                    key=lambda m: os.path.getmtime(m) if os.path.exists(m) else 0,
                    reverse=True,
                )
                matches = matches[:50]  # Limit to 50 most recently modified files

            completions = []
            for match in matches:
                # Check if the match starts with our prefix
                if match.startswith(prefix):
                    completions.append(
                        Completion(
                            text="@" + match,  # Include the "@" symbol
                            display=f"@{match}",
                            display_meta="File reference",
                            start_position=-len(prefix) - 1,  # Replace prefix & "@"
                        )
                    )

            # Sort completions and limit to 50 for performance
            return sorted(completions, key=lambda c: c.text)[:50]
        except Exception:
            # If there's an error, return empty completions
            return []

    def _get_file_completions(self, text: str) -> list[Completion]:
        """Get completions for file references with '@' prefix."""
        # Remove the '@' prefix for matching
        prefix = text[1:]  # Everything after '@'

        # Find all files in current directory and subdirectories
        try:
            matches = glob("**/*", recursive=True)
            # Filter out directories and hidden files (except .gitignore)
            matches = [
                m
                for m in matches
                if not os.path.isdir(m) and (not m.startswith(".") or m == ".gitignore")
            ]
            # Additional filtering to only include files (in case of symlinks, etc.)
            matches = [m for m in matches if os.path.isfile(m)]

            # If prefix is empty, show a limited number of common files
            if not prefix:
                # Sort by modification time (recent files first) and limit
                matches = sorted(
                    matches,
                    key=lambda m: os.path.getmtime(m) if os.path.exists(m) else 0,
                    reverse=True,
                )
                matches = matches[:50]  # Limit to 50 most recently modified files

            completions = []
            for match in matches:
                # Check if the match starts with our prefix
                if match.startswith(prefix):
                    completions.append(
                        Completion(
                            text="@" + match,  # Include the "@" symbol
                            display=f"@{match}",
                            display_meta="File reference",
                            start_position=-len(prefix) - 1,  # Replace prefix & "@"
                        )
                    )

            # Sort completions and limit to 50 for performance
            return sorted(completions, key=lambda c: c.text)[:50]
        except Exception:
            # If there's an error, return empty completions
            return []

    def _get_base_command_completions(self, text: str) -> list[Completion]:
        """Get completions for base commands."""
        completions = []

        # Only show slash command completions if text starts with "/"
        if text.startswith("/"):
            text_without_slash = text.lstrip("/")
            for command, info in self.base_commands.items():
                # Include the command itself
                if command.startswith(text_without_slash):
                    # Calculate start position for completion
                    # We need to replace only the part after the slash
                    start_pos = -len(text_without_slash)
                    completions.append(
                        Completion(
                            text=command,  # Just the command without slash
                            display=f"/{command}",
                            display_meta=info["description"],
                            start_position=start_pos,
                        )
                    )

                # Include aliases
                aliases_list = info.get("alias")
                if isinstance(aliases_list, list):
                    for alias in aliases_list:
                        if alias.startswith(text_without_slash):
                            # Calculate start position for completion
                            start_pos = -len(text_without_slash)
                            completions.append(
                                Completion(
                                    text=alias,  # Just the alias without slash
                                    display=f"/{alias}",
                                    display_meta=f"Alias for /{command}",
                                    start_position=start_pos,
                                )
                            )

        return sorted(completions, key=lambda c: c.text)

    def _get_command_specific_completions(
        self, command: str, words: list[str], text: str, complete_event: Any
    ) -> list[Completion]:
        """Get completions for command-specific arguments."""
        command_info = self.base_commands.get(command)

        if not command_info:
            return []

        # Handle subcommands
        subcommands_list = command_info.get("subcommands")
        if isinstance(subcommands_list, list):
            # Check for subcommand argument completion FIRST (more specific)
            if len(words) >= 3 or (len(words) == 2 and text.endswith(" ")):
                # Handle completion for subcommand arguments (3+ words or 2 words with space)
                # For /model command, handle specific subcontexts
                if command == "model":
                    # Determine which word we're completing
                    if len(words) >= 3:
                        subcommand = words[1].lower()
                        current_word = words[-1] if not text.endswith(" ") else ""
                    else:  # len(words) == 2 and text.endswith(" ")
                        subcommand = words[1].lower()
                        current_word = ""  # Starting fresh completion

                    # For "/model load" and "/model use", show model names only
                    if subcommand in ["load", "use"]:
                        models = list_available_models()
                        completions: list[Completion] = []

                        for model_config in models:
                            model_name = model_config[0]
                            if model_name.startswith(current_word):
                                is_default = model_config[2]  # is_default boolean
                                status_indicator = " (default)" if is_default else ""
                                completions.append(
                                    Completion(
                                        text=model_name,
                                        display=f"{model_name}{status_indicator}",
                                        display_meta=model_config[1],  # Description
                                        start_position=-len(current_word),
                                    )
                                )

                        return completions

                    # For "/model add", show providers
                    elif subcommand == "add":
                        providers = list_available_providers()
                        completions = []

                        for provider_name, provider_desc in providers:
                            if provider_name.startswith(current_word):
                                completions.append(
                                    Completion(
                                        text=provider_name,
                                        display=provider_name,
                                        display_meta=provider_desc,
                                        start_position=-len(current_word),
                                    )
                                )

                        return completions
            elif len(words) <= 2:
                # Complete subcommand names AND model names for /model command
                subcommand_prefix = words[1] if len(words) > 1 else ""
                completions = []

                # For /model command, show subcommands first, then models
                if command == "model":
                    # Show subcommands first with clear prioritization
                    subcommand_completions = []
                    for subcommand in command_info["subcommands"]:
                        if subcommand.startswith(subcommand_prefix):
                            subcommand_completions.append(
                                Completion(
                                    text=subcommand,
                                    display=subcommand,
                                    display_meta=self._get_subcommand_description(
                                        command, subcommand
                                    ),
                                    start_position=-len(subcommand_prefix),
                                )
                            )

                    # Show model names below subcommands for direct switching
                    models = list_available_models()
                    model_completions = []
                    for model_config in models:
                        model_name = model_config[0]
                        # Always include models for direct switching capability
                        if model_name.startswith(subcommand_prefix):
                            is_default = model_config[2]  # is_default boolean
                            status_indicator = " (default)" if is_default else ""
                            model_completions.append(
                                Completion(
                                    text=model_name,
                                    display=f"{model_name}{status_indicator}",
                                    display_meta=model_config[1],  # Description
                                    start_position=-len(subcommand_prefix),
                                )
                            )

                    # Combine: subcommands prioritized at top, models available below
                    completions = subcommand_completions + model_completions
                else:
                    # For other commands, just show subcommands
                    for subcommand in command_info["subcommands"]:
                        if subcommand.startswith(subcommand_prefix):
                            completions.append(
                                Completion(
                                    text=subcommand,
                                    display=subcommand,
                                    display_meta=self._get_subcommand_description(
                                        command, subcommand
                                    ),
                                    start_position=-len(subcommand_prefix),
                                )
                            )

                return completions

        # Only use command-specific completer for cases NOT handled above
        # For model command, we've handled subcommand cases, so use fallback for others
        if command != "model":
            completer_factory = command_info.get("completer")
            if completer_factory:
                if callable(completer_factory):
                    completer = completer_factory()
                else:
                    completer = completer_factory

                if completer:
                    # Create a new document with the relevant part for the sub-completer
                    if len(words) > 1:
                        current_word = words[-1] if not text.endswith(" ") else ""
                        sub_doc = Document(current_word)
                        return list(completer.get_completions(sub_doc, complete_event))

        return []

    def _get_subcommand_description(self, command: str, subcommand: str) -> str:
        """Get description for a subcommand."""
        descriptions = {
            ("model", "list"): "Show your saved models",
            ("model", "add"): "Add a new model configuration",
            ("model", "remove"): "Remove a saved model",
            ("model", "default"): "Set model as default",
            ("model", "use"): "Try a model without saving",
            ("model", "load"): "Load model (same as direct switch)",
            ("model", "threshold"): "Set compaction threshold",
            ("auto", "list"): "List auto-approved actions",
            ("auto", "revoke"): "Revoke auto-approval for action",
            ("auto", "clear"): "Clear all auto-approvals",
            ("mcp", "list"): "List configured MCP servers",
            ("mcp", "tools"): "List MCP tools",
            ("mcp", "refresh"): "Refresh MCP connections",
            ("mcp", "allow"): "Trust MCP server",
            ("mcp", "revoke"): "Revoke trust for MCP server",
            ("mcp", "enable"): "Enable a disabled MCP server",
            ("mcp", "disable"): "Disable an enabled MCP server",
            ("subagent", "list"): "Show subagent configurations",
            ("subagent", "set"): "Set model for subagent type",
            ("subagent", "clear"): "Clear model override",
            ("subagent", "reset"): "Clear all overrides",
        }
        return descriptions.get((command, subcommand), subcommand)


class ModelCommandCompleter(Completer):
    """Completer for model command arguments."""

    def __init__(self, agent: Any = None) -> None:
        self.agent = agent

    def get_completions(self, document: Document, complete_event: Any) -> list[Completion]:
        """Get model command completions."""
        text = document.text_before_cursor

        # Try to get the full command context
        # This is a simplified approach - in practice, we'd need more context
        # about which subcommand we're completing for

        # Complete model names (saved models)
        models = list_available_models()
        completions: list[Completion] = []

        for model_config in models:
            model_name = model_config[0]
            if model_name.startswith(text):
                completions.append(
                    Completion(
                        text=model_name,
                        display=model_name,
                        display_meta=model_config[1],  # Description
                        start_position=-len(text),
                    )
                )

        # Complete provider names if this looks like an "add" or "use" command
        if text == "" or len(text) < 3:  # Short prefix, might be provider
            providers = list_available_providers()
            for provider_name, _ in providers:
                if provider_name.startswith(text):
                    completions.append(
                        Completion(
                            text=provider_name,
                            display=provider_name,
                            display_meta="Provider",
                            start_position=-len(text),
                        )
                    )

        return completions


class AutoCommandCompleter(Completer):
    """Completer for auto command arguments."""

    def get_completions(self, document: Document, complete_event: Any) -> list[Completion]:
        """Get auto command completions."""
        text = document.text_before_cursor

        # Complete action types for "revoke" subcommand
        action_types = [action.value for action in ActionType]
        completions: list[Completion] = []

        for action in action_types:
            if action.startswith(text):
                completions.append(
                    Completion(
                        text=action,
                        display=action,
                        display_meta="Action type",
                        start_position=-len(text),
                    )
                )

        return completions


class MCPCommandCompleter(Completer):
    """Completer for MCP command arguments."""

    def __init__(self, agent: Any = None) -> None:
        self.agent = agent

    def get_completions(self, document: Document, complete_event: Any) -> list[Completion]:
        """Get MCP command completions."""
        text = document.text_before_cursor
        completions: list[Completion] = []

        # Complete server names if available
        if self.agent and hasattr(self.agent, "mcp_manager") and self.agent.mcp_manager:
            try:
                servers = self.agent.mcp_manager.list_servers()
                for server in servers:
                    server_id = server["server_id"]
                    if server_id.startswith(text):
                        completions.append(
                            Completion(
                                text=server_id,
                                display=server_id,
                                display_meta=f"MCP Server ({server['tools_count']} tools)",
                                start_position=-len(text),
                            )
                        )
            except Exception:
                # If there's an error accessing MCP manager, return empty completions
                pass

        return completions


class SubagentCommandCompleter(Completer):
    """Completer for subagent command arguments."""

    def get_completions(self, document: Document, complete_event: Any) -> list[Completion]:
        """Get subagent command completions."""
        text = document.text_before_cursor
        completions: list[Completion] = []

        # Complete subagent types
        subagent_types = list_subagent_types()
        for subagent_type in subagent_types:
            if subagent_type.startswith(text):
                completions.append(
                    Completion(
                        text=subagent_type,
                        display=subagent_type,
                        display_meta="Subagent type",
                        start_position=-len(text),
                    )
                )

        # Could also complete model names here for "set" subcommand
        # This would require more context about which subcommand we're in

        return completions


def create_completer(agent: Any = None) -> ClippyCommandCompleter:
    """Create and return a clippy command completer."""
    return ClippyCommandCompleter(agent)
