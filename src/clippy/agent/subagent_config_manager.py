"""Configuration manager for subagent model overrides."""

import json
import logging
from pathlib import Path
from typing import Any

from clippy.agent.subagent_types import list_subagent_types

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
                logger.debug(f"Loaded subagent config: {len(self._model_overrides)} overrides")
        except Exception as e:
            logger.error(f"Failed to load subagent config: {e}")
            self._model_overrides = {}

    def _save_config(self) -> None:
        """Save configuration to disk."""
        try:
            data = {"model_overrides": self._model_overrides}
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
        from clippy.agent.subagent_types import get_subagent_config

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


# Global instance for easy access
_config_manager: SubagentConfigManager | None = None


def get_subagent_config_manager() -> SubagentConfigManager:
    """Get or create the global SubagentConfigManager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = SubagentConfigManager()
    return _config_manager
