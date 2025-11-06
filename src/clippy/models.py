"""Model configuration and management system for LLM providers."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ProviderConfig:
    """Configuration for a specific LLM provider."""

    name: str
    base_url: str | None
    api_key_env: str
    description: str
    pydantic_system: str | None = None


@dataclass
class UserModelConfig:
    """User-defined model configuration."""

    name: str
    provider: str
    model_id: str
    description: str
    is_default: bool = False
    compaction_threshold: int | None = None  # Token threshold for auto compaction
    context_window: int | None = None
    max_tokens: int | None = None


class UserModelManager:
    """Manages user-defined model configurations."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize the user model manager.

        Args:
            config_dir: Directory to store user configurations. Defaults to ~/.clippy
        """
        if config_dir is None:
            config_dir = Path.home() / ".clippy"

        self.config_dir = config_dir
        self.models_file = config_dir / "models.json"
        self.config_dir.mkdir(exist_ok=True)

        # Ensure default models exist
        self._ensure_default_models()

    def _ensure_default_models(self) -> None:
        """Create default model configuration if none exists."""
        if not self.models_file.exists():
            default_models = {
                "models": [
                    {
                        "name": "gpt-5",
                        "provider": "openai",
                        "model_id": "gpt-5",
                        "description": "openai/gpt-5",
                        "is_default": True,
                        "compaction_threshold": None,
                    }
                ]
            }
            self._save_models(default_models)

    def _load_models(self) -> dict[str, Any]:
        """Load user models from JSON file."""
        try:
            with open(self.models_file) as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is corrupted, create default
            default_models: dict[str, Any] = {"models": []}
            self._save_models(default_models)
            return default_models

    def _save_models(self, data: dict[str, Any]) -> None:
        """Save user models to JSON file."""
        with open(self.models_file, "w") as f:
            json.dump(data, f, indent=2)

    def list_models(self) -> list[UserModelConfig]:
        """Get all user-defined models."""
        data = self._load_models()
        models = []
        for model_data in data.get("models", []):
            models.append(UserModelConfig(**model_data))
        return models

    def get_model(self, name: str) -> UserModelConfig | None:
        """Get a specific model by name (case-insensitive)."""
        name_lower = name.lower()
        for model in self.list_models():
            if model.name.lower() == name_lower:
                return model
        return None

    def get_default_model(self) -> UserModelConfig | None:
        """Get the default model."""
        for model in self.list_models():
            if model.is_default:
                return model

        # If no default is set, return the first model
        models = self.list_models()
        return models[0] if models else None

    def add_model(
        self,
        name: str,
        provider: str,
        model_id: str,
        is_default: bool = False,
        compaction_threshold: int | None = None,
    ) -> tuple[bool, str]:
        """Add a new user model.

        Args:
            name: Display name for the model
            provider: Provider name (must exist in providers.yaml)
            model_id: Actual model ID for the API
            is_default: Whether to set as default model
            compaction_threshold: Token threshold for auto compaction (optional)

        Returns:
            Tuple of (success, message)
        """
        # Check if provider exists
        if not get_provider(provider):
            return False, f"Unknown provider: {provider}"

        # Check if model name already exists
        if self.get_model(name):
            return False, f"Model '{name}' already exists"

        # Load current models
        data = self._load_models()

        # If setting as default, unset other defaults
        if is_default:
            for model_data in data.get("models", []):
                model_data["is_default"] = False

        # Auto-generate description as provider/model_id
        description = f"{provider}/{model_id}"

        # Add new model
        new_model = {
            "name": name,
            "provider": provider,
            "model_id": model_id,
            "description": description,
            "is_default": is_default,
            "compaction_threshold": compaction_threshold,
        }
        data["models"].append(new_model)

        # Save and return
        self._save_models(data)
        return True, f"Added model '{name}'"

    def remove_model(self, name: str) -> tuple[bool, str]:
        """Remove a user model."""
        data = self._load_models()
        original_count = len(data.get("models", []))

        # Filter out the model to remove
        data["models"] = [model for model in data.get("models", []) if model["name"] != name]

        if len(data["models"]) == original_count:
            return False, f"Model '{name}' not found"

        self._save_models(data)
        return True, f"Removed model '{name}'"

    def set_default(self, name: str) -> tuple[bool, str]:
        """Set a model as the default."""
        data = self._load_models()
        model_found = False

        # Unset all defaults and set the requested one
        for model_data in data.get("models", []):
            if model_data["name"] == name:
                model_data["is_default"] = True
                model_found = True
            else:
                model_data["is_default"] = False

        if not model_found:
            return False, f"Model '{name}' not found"

        self._save_models(data)
        return True, f"Set '{name}' as default model"

    def set_compaction_threshold(self, name: str, threshold: int | None) -> tuple[bool, str]:
        """Set the compaction threshold for a model."""
        data = self._load_models()
        model_found = False

        # Find and update the model
        for model_data in data.get("models", []):
            if model_data["name"].lower() == name.lower():
                model_data["compaction_threshold"] = threshold
                model_found = True
                break

        if not model_found:
            return False, f"Model '{name}' not found"

        self._save_models(data)
        if threshold is None:
            return True, f"Removed compaction threshold from model '{name}'"
        else:
            return True, f"Set compaction threshold for model '{name}' to {threshold:,} tokens"


# Global instances
_providers: dict[str, ProviderConfig] = {}
_user_manager: UserModelManager | None = None


def _load_providers() -> dict[str, ProviderConfig]:
    """Load provider configurations from YAML file."""
    global _providers

    if _providers:
        return _providers

    yaml_path = Path(__file__).parent / "providers.yaml"

    with open(yaml_path) as f:
        config = yaml.safe_load(f)

    for provider_name, provider_data in config["providers"].items():
        _providers[provider_name] = ProviderConfig(
            name=provider_name,
            base_url=provider_data.get("base_url"),
            api_key_env=provider_data.get("api_key_env", "OPENAI_API_KEY"),
            description=provider_data.get("description", ""),
            pydantic_system=provider_data.get("pydantic_system"),
        )

    return _providers


def get_providers() -> dict[str, ProviderConfig]:
    """Get all available providers."""
    return _load_providers()


def get_provider(name: str) -> ProviderConfig | None:
    """Get a specific provider by name."""
    providers = _load_providers()
    return providers.get(name)


def get_user_manager() -> UserModelManager:
    """Get the user model manager instance."""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserModelManager()
    return _user_manager


def get_model_config(name: str) -> tuple[UserModelConfig | None, ProviderConfig | None]:
    """Get a user model configuration and its provider.

    Args:
        name: Model name to look up

    Returns:
        Tuple of (model_config, provider_config)
    """
    user_manager = get_user_manager()
    model = user_manager.get_model(name)

    if model:
        provider = get_provider(model.provider)
        return model, provider

    return None, None


def get_default_model_config() -> tuple[UserModelConfig | None, ProviderConfig | None]:
    """Get the default model configuration and its provider."""
    user_manager = get_user_manager()
    model = user_manager.get_default_model()

    if model:
        provider = get_provider(model.provider)
        return model, provider

    return None, None


def list_available_models() -> list[tuple[str, str, bool, int | None]]:
    """Get list of available user models with descriptions, default status,
    and compaction thresholds.

    Returns:
        List of tuples (name, description, is_default, compaction_threshold)
    """
    user_manager = get_user_manager()
    models = user_manager.list_models()
    return [
        (model.name, model.description, model.is_default, model.compaction_threshold)
        for model in models
    ]


def list_available_providers() -> list[tuple[str, str]]:
    """Get list of available providers with descriptions.

    Returns:
        List of tuples (name, description)
    """
    providers = get_providers()
    return [(provider.name, provider.description) for provider in providers.values()]


def get_model_compaction_threshold(name_or_id: str) -> int | None:
    """Get the compaction threshold for a specific model.

    Looks up by saved model name first (case-insensitive), then by model_id.

    Args:
        name_or_id: Saved model name or underlying provider model_id

    Returns:
        Compaction threshold in tokens, or None if not set
    """
    user_manager = get_user_manager()

    # Try by saved model name (case-insensitive)
    model = user_manager.get_model(name_or_id)
    if model:
        return model.compaction_threshold

    # Fallback: try to find by model_id (case-insensitive)
    lookup = name_or_id.lower()
    for m in user_manager.list_models():
        if m.model_id.lower() == lookup:
            return m.compaction_threshold

    return None


def set_model_compaction_threshold(name: str, threshold: int | None) -> tuple[bool, str]:
    """Set the compaction threshold for a specific model.

    Args:
        name: Model name to update
        threshold: New threshold value (int) or None to remove

    Returns:
        Tuple of (success, message)
    """
    user_manager = get_user_manager()
    return user_manager.set_compaction_threshold(name, threshold)
