"""Configuration manager for subagent model overrides."""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .subagent_types import Subagent

logger = logging.getLogger(__name__)


class SubagentConfigManager:
    """Manages model overrides for subagent types.

    Allows users to configure which model to use for each subagent type,
    overriding the default behavior of inheriting from the parent agent.

    Configuration is stored in ~/.clippy/subagent_config.json
    """

    def __init__(self, config_path: Path | None = None):
        """Initialize the configuration manager.

        Args:
            config_path: Optional custom path for config file.
                        Defaults to ~/.clippy/subagent_config.json
        """
        if config_path is None:
            config_path = Path.home() / ".clippy" / "subagent_config.json"

        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._model_overrides: dict[str, str] = {}
        self._user_subagents: dict[str, dict[str, Any]] = {}
        self._default_subagent: str = "general"
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from disk."""
        if not self.config_path.exists():
            logger.debug(f"No subagent config file found at {self.config_path}")
            return

        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = json.load(f)
                self._model_overrides = data.get("model_overrides", {})
                self._user_subagents = data.get("user_subagents", {})
                self._default_subagent = data.get("default_subagent", "general")
                logger.debug(
                    f"Loaded subagent config: {len(self._model_overrides)} overrides, "
                    f"{len(self._user_subagents)} user subagents"
                )
        except Exception as e:
            logger.error(f"Failed to load subagent config: {e}")
            self._model_overrides = {}

    def _save_config(self) -> None:
        """Save configuration to disk."""
        try:
            data = {
                "model_overrides": self._model_overrides,
                "user_subagents": self._user_subagents,
                "default_subagent": self._default_subagent,
            }
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved subagent config to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save subagent config: {e}")
            raise

    def get_model_override(self, subagent_type: str) -> str | None:
        """Get the model override for a subagent type.

        Args:
            subagent_type: The type of subagent

        Returns:
            Model name if override is set, None otherwise
        """
        return self._model_overrides.get(subagent_type)

    def set_model_override(self, subagent_type: str, model: str | None) -> None:
        """Set the model override for a subagent type.

        Args:
            subagent_type: The type of subagent
            model: Model name to use, or None to inherit from parent

        Raises:
            ValueError: If subagent_type is not valid
        """
        # Import here to avoid circular imports
        from .subagent_types import list_subagent_types

        valid_types = list_subagent_types()
        if subagent_type not in valid_types:
            raise ValueError(
                f"Invalid subagent type: {subagent_type}. Valid types: {', '.join(valid_types)}"
            )

        if model is None:
            # Clear override
            if subagent_type in self._model_overrides:
                del self._model_overrides[subagent_type]
        else:
            self._model_overrides[subagent_type] = model

        self._save_config()
        logger.info(f"Set model override for {subagent_type}: {model}")

    def clear_model_override(self, subagent_type: str) -> bool:
        """Clear the model override for a subagent type.

        Args:
            subagent_type: The type of subagent

        Returns:
            True if override was cleared, False if no override existed
        """
        if subagent_type in self._model_overrides:
            del self._model_overrides[subagent_type]
            self._save_config()
            logger.info(f"Cleared model override for {subagent_type}")
            return True
        return False

    def clear_all_overrides(self) -> int:
        """Clear all model overrides.

        Returns:
            Number of overrides that were cleared
        """
        count = len(self._model_overrides)
        self._model_overrides = {}
        self._save_config()
        logger.info(f"Cleared all {count} model overrides")
        return count

    def list_overrides(self) -> dict[str, str]:
        """List all current model overrides.

        Returns:
            Dictionary mapping subagent type to model name
        """
        return dict(self._model_overrides)

    def get_all_configurations(self) -> dict[str, dict[str, Any]]:
        """Get complete configuration for all subagent types.

        Returns:
            Dictionary with configuration for each subagent type,
            including whether it has a model override
        """
        # Import here to avoid circular imports
        from .subagent_types import get_subagent_config, list_subagent_types

        configs = {}
        for subagent_type in list_subagent_types():
            type_config = get_subagent_config(subagent_type)
            override = self._model_overrides.get(subagent_type)

            configs[subagent_type] = {
                "model_override": override,
                "default_model": type_config.get("model"),
                "max_iterations": type_config.get("max_iterations"),
                "allowed_tools": type_config.get("allowed_tools"),
            }

        return configs

    def get_default_subagent(self) -> str:
        """Get the default subagent type.

        Returns:
            Default subagent type name
        """
        return self._default_subagent

    def set_default_subagent(self, subagent_name: str) -> tuple[bool, str]:
        """Set the default subagent type.

        Args:
            subagent_name: Name of the subagent to set as default

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Check if subagent exists
        all_subagents = self.get_all_subagent_names()
        if subagent_name not in all_subagents:
            return False, f"Unknown subagent: {subagent_name}"

        self._default_subagent = subagent_name
        self._save_config()
        logger.info(f"Set default subagent: {subagent_name}")
        return True, f"Default subagent set to '{subagent_name}'"

    def add_subagent(self, name: str, prompt: str) -> tuple[bool, str]:
        """Add a new user-defined subagent.

        Args:
            name: Name of the subagent
            prompt: System prompt for the subagent

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Import here to avoid circular imports
        from .subagent_types import SUBAGENT_TYPES

        # Check if name already exists (built-in or user)
        if name in SUBAGENT_TYPES.keys() or name in self._user_subagents:
            return False, f"Subagent '{name}' already exists"

        # Validate inputs
        if not name.strip():
            return False, "Subagent name cannot be empty"
        if not prompt.strip():
            return False, "Subagent prompt cannot be empty"

        # Add subagent
        self._user_subagents[name] = {
            "prompt": prompt.strip(),
            "allowed_tools": "all",  # Default to all tools for user subagents
            "max_iterations": 25,
        }

        self._save_config()
        logger.info(f"Added user subagent: {name}")
        return True, f"Subagent '{name}' added successfully"

    def remove_subagent(self, name: str) -> tuple[bool, str]:
        """Remove a user-defined subagent.

        Args:
            name: Name of the subagent to remove

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Import here to avoid circular imports
        from .subagent_types import SUBAGENT_TYPES

        # Cannot remove built-in subagents
        if name in SUBAGENT_TYPES.keys():
            return False, f"Cannot remove built-in subagent '{name}'"

        # Remove user subagent
        if name in self._user_subagents:
            del self._user_subagents[name]

            # If this was the default, reset to "general"
            if self._default_subagent == name:
                self._default_subagent = "general"
                default_msg = " Default subagent reset to 'general'."
            else:
                default_msg = ""

            self._save_config()
            logger.info(f"Removed user subagent: {name}")
            return True, f"Subagent '{name}' removed successfully.{default_msg}"
        else:
            return False, f"Unknown subagent: {name}"

    def get_user_subagents(self) -> list["Subagent"]:
        """Get list of user-defined subagents.

        Returns:
            List of user-defined Subagent objects
        """
        # Import here to avoid circular imports
        from .subagent_types import Subagent

        subagents = []
        for name, config in self._user_subagents.items():
            if not isinstance(config, dict):
                continue
            subagents.append(
                Subagent(
                    name=name,
                    prompt=config["prompt"],
                    is_builtin=False,
                    allowed_tools=config.get("allowed_tools", "all"),
                    model=config.get("model"),
                    max_iterations=config.get("max_iterations", 25),
                )
            )
        return subagents

    def get_all_subagent_names(self) -> list[str]:
        """Get list of all subagent names (built-in + user-defined).

        Returns:
            List of all subagent names
        """
        # Import here to avoid circular imports
        from .subagent_types import SUBAGENT_TYPES

        names = list(SUBAGENT_TYPES.keys())
        names.extend(self._user_subagents.keys())
        return names


# Global instance for easy access
_config_manager: SubagentConfigManager | None = None


def get_subagent_config_manager() -> SubagentConfigManager:
    """Get or create the global SubagentConfigManager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = SubagentConfigManager()
    return _config_manager
