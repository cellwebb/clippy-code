"""Model configuration and management system for LLM providers."""

import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ProviderConfig:
    """Configuration for a specific LLM provider."""

    name: str
    base_url: str | None
    api_key_env: str | None
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


class UserProviderManager:
    """Manages user-defined provider configurations."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize the user provider manager.

        Args:
            config_dir: Directory to store user configurations. Defaults to ~/.clippy
        """
        if config_dir is None:
            config_dir = Path.home() / ".clippy"

        self.config_dir = config_dir
        self.providers_file = config_dir / "providers.json"
        self.config_dir.mkdir(exist_ok=True)

        # Ensure the providers file exists
        self._ensure_providers_file()

    def _ensure_providers_file(self) -> None:
        """Create provider configuration file if none exists."""
        if not self.providers_file.exists():
            empty_config: dict[str, Any] = {"providers": {}}
            self._save_providers(empty_config)

    def _load_providers(self) -> dict[str, Any]:
        """Load user providers from JSON file."""
        try:
            with open(self.providers_file) as f:
                data: dict[str, Any] = json.load(f)
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is corrupted, create empty
            empty_config: dict[str, Any] = {"providers": {}}
            self._save_providers(empty_config)
            return empty_config

    def _save_providers(self, data: dict[str, Any]) -> None:
        """Save user providers to JSON file."""
        with open(self.providers_file, "w") as f:
            json.dump(data, f, indent=2)

    def list_providers(self) -> dict[str, dict[str, Any]]:
        """Get all user-defined providers."""
        data = self._load_providers()
        providers = data.get("providers", {})
        # Type cast to ensure correct return type
        return providers if isinstance(providers, dict) else {}

    def get_provider(self, name: str) -> dict[str, Any] | None:
        """Get a specific user provider by name (case-insensitive)."""
        name_lower = name.lower()
        providers = self.list_providers()

        for provider_name, provider_data in providers.items():
            if provider_name.lower() == name_lower:
                return provider_data
        return None

    def add_provider(
        self,
        name: str,
        base_url: str | None,
        api_key_env: str | None,
        description: str,
        pydantic_system: str | None = None,
    ) -> tuple[bool, str]:
        """Add a new user provider.

        Args:
            name: Provider name
            base_url: Base URL for the provider
            api_key_env: Environment variable for API key
            description: Provider description
            pydantic_system: Pydantic system type

        Returns:
            Tuple of (success, message)
        """
        # Check if provider already exists
        if self.get_provider(name):
            return False, f"Provider '{name}' already exists"

        # Load current providers
        data = self._load_providers()

        # Add new provider
        new_provider = {
            "base_url": base_url,
            "api_key_env": api_key_env,
            "description": description,
            "pydantic_system": pydantic_system,
        }
        data["providers"][name] = new_provider

        # Save and return
        self._save_providers(data)
        return True, f"Added provider '{name}'"

    def remove_provider(self, name: str) -> tuple[bool, str]:
        """Remove a user provider."""
        data = self._load_providers()
        providers = data.get("providers", {})

        name_lower = name.lower()
        # Find the provider to remove (case-insensitive)
        provider_to_remove = None
        for provider_name in providers:
            if provider_name.lower() == name_lower:
                provider_to_remove = provider_name
                break

        if not provider_to_remove:
            return False, f"Provider '{name}' not found"

        del providers[provider_to_remove]
        data["providers"] = providers
        self._save_providers(data)
        return True, f"Removed provider '{provider_to_remove}'"

    def update_provider(
        self,
        name: str,
        base_url: str | None = None,
        api_key_env: str | None = None,
        description: str | None = None,
        pydantic_system: str | None = None,
        *,
        _update_api_key_env: bool = False,
    ) -> tuple[bool, str]:
        """Update an existing user provider.

        Args:
            name: Provider name to update
            base_url: New base URL (optional)
            api_key_env: New API key env variable (optional)
            description: New description (optional)
            pydantic_system: New pydantic system (optional)

        Returns:
            Tuple of (success, message)
        """
        provider = self.get_provider(name)
        if not provider:
            return False, f"Provider '{name}' not found"

        # Load current providers
        data = self._load_providers()

        # Find the actual provider name (case-insensitive match)
        actual_name = None
        for provider_name in data["providers"]:
            if provider_name.lower() == name.lower():
                actual_name = provider_name
                break

        if not actual_name:
            return False, f"Provider '{name}' not found"

        # Update fields if provided
        if base_url is not None:
            data["providers"][actual_name]["base_url"] = base_url
        if api_key_env is not None or _update_api_key_env:
            data["providers"][actual_name]["api_key_env"] = api_key_env
        if description is not None:
            data["providers"][actual_name]["description"] = description
        if pydantic_system is not None:
            data["providers"][actual_name]["pydantic_system"] = pydantic_system

        # Save and return
        self._save_providers(data)
        return True, f"Updated provider '{actual_name}'"


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
        """Create empty model configuration if none exists."""
        if not self.models_file.exists():
            empty_models: dict[str, Any] = {"models": []}
            self._save_models(empty_models)

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

    def switch_model(self, name: str) -> tuple[bool, str]:
        """Switch to a model for the current session without setting it as default."""
        model = self.get_model(name)
        if not model:
            return False, f"Model '{name}' not found"

        # Just return success - don't set as default
        return True, f"Switched to model '{name}' (current session only)"


# Module-level cache for lazy initialization
# These are accessed through getter functions to ensure proper initialization.
# For CLI applications, this simple caching pattern is sufficient.
# Use reset_all_caches() in tests to clear state between test cases.
_providers: dict[str, ProviderConfig] = {}
_user_manager: UserModelManager | None = None
_user_provider_manager: UserProviderManager | None = None
_lock = threading.Lock()  # Protects all module-level state above


def reset_all_caches() -> None:
    """Reset all module-level caches.

    This should be called in tests to ensure clean state between test cases.
    In production, use reload_providers() or reload_model_manager() for targeted reloads.
    """
    global _providers, _user_manager, _user_provider_manager
    with _lock:
        _providers.clear()
        _user_manager = None
        _user_provider_manager = None


def get_user_provider_manager() -> UserProviderManager:
    """Get the user provider manager instance."""
    global _user_provider_manager
    with _lock:
        if _user_provider_manager is None:
            _user_provider_manager = UserProviderManager()
        return _user_provider_manager


def _load_providers() -> dict[str, ProviderConfig]:
    """Load provider configurations from both built-in YAML and user JSON files.

    User providers take precedence over built-in providers in case of name conflicts.
    """
    global _providers

    with _lock:
        if _providers:
            return _providers

        # Load built-in providers from YAML
        yaml_path = Path(__file__).parent / "providers.yaml"
        with open(yaml_path) as f:
            built_in_config = yaml.safe_load(f)

        # First, load built-in providers
        for provider_name, provider_data in built_in_config["providers"].items():
            _providers[provider_name] = ProviderConfig(
                name=provider_name,
                base_url=provider_data.get("base_url"),
                api_key_env=provider_data.get("api_key_env"),
                description=provider_data.get("description", ""),
                pydantic_system=provider_data.get("pydantic_system"),
            )

        # Then, load and merge user providers (these override built-in ones)
        # Note: get_user_provider_manager() also uses _lock, but threading.Lock is reentrant-safe
        # when called from the same thread. For cross-thread safety, we release and reacquire.

    user_manager = get_user_provider_manager()
    user_providers = user_manager.list_providers()

    with _lock:
        for provider_name, provider_data in user_providers.items():
            _providers[provider_name] = ProviderConfig(
                name=provider_name,
                base_url=provider_data.get("base_url"),
                api_key_env=provider_data.get("api_key_env"),
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
    with _lock:
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


def list_available_models_with_provider() -> list[tuple[str, str, bool, int | None, str]]:
    """Get list of available user models with descriptions, default status,
    compaction thresholds, and provider names.

    Returns:
        List of tuples (name, description, is_default, compaction_threshold, provider)
    """
    user_manager = get_user_manager()
    models = user_manager.list_models()
    return [
        (
            model.name,
            model.description,
            model.is_default,
            model.compaction_threshold,
            model.provider,
        )
        for model in models
    ]


def list_available_providers() -> list[tuple[str, str]]:
    """Get list of available providers with descriptions.

    Returns:
        List of tuples (name, description)
    """
    providers = get_providers()
    return [(provider.name, provider.description) for provider in providers.values()]


def list_providers_by_source() -> dict[str, list[tuple[str, str]]]:
    """Get list of providers separated by source (built-in vs user-defined).

    Returns:
        Dictionary with keys 'built_in' and 'user' containing lists of (name, description)
    """
    result: dict[str, list[tuple[str, str]]] = {"built_in": [], "user": []}

    # Get built-in providers from YAML
    yaml_path = Path(__file__).parent / "providers.yaml"
    with open(yaml_path) as f:
        built_in_config = yaml.safe_load(f)

    for provider_name, provider_data in built_in_config["providers"].items():
        result["built_in"].append((provider_name, provider_data.get("description", "")))

    # Get user providers from JSON
    user_manager = get_user_provider_manager()
    user_providers = user_manager.list_providers()

    for provider_name, provider_data in user_providers.items():
        result["user"].append((provider_name, provider_data.get("description", "")))

    return result


def is_user_provider(name: str) -> bool:
    """Check if a provider is user-defined.

    Args:
        name: Provider name to check

    Returns:
        True if provider is user-defined, False if built-in
    """
    # Load built-in providers
    yaml_path = Path(__file__).parent / "providers.yaml"
    with open(yaml_path) as f:
        built_in_config = yaml.safe_load(f)

    # If it's in built-in config, it's not user-defined
    if name in built_in_config["providers"]:
        return False

    # Otherwise, check if it exists in user providers
    user_manager = get_user_provider_manager()
    return user_manager.get_provider(name) is not None


def reload_providers() -> dict[str, ProviderConfig]:
    """Reload provider configurations from both built-in and user sources.

    This should be called after modifying provider configurations to ensure
    the latest configuration is loaded.

    Returns:
        Dictionary of provider configurations
    """
    global _providers, _user_provider_manager
    with _lock:
        _providers.clear()  # Clear the cache
        _user_provider_manager = None  # Clear user provider manager cache
    return _load_providers()


def reload_model_manager() -> UserModelManager:
    """Reload the user model manager to clear the cache and get fresh data.

    This should be called after modifying model configurations to ensure
    the latest configuration is loaded.

    Returns:
        Fresh UserModelManager instance
    """
    global _user_manager
    with _lock:
        _user_manager = None  # Clear the cache
    return get_user_manager()


def get_model_compaction_threshold(
    name_or_id: str, preferred_model_name: str | None = None
) -> int | None:
    """Get the compaction threshold for a specific model.

    Looks up by saved model name first (case-insensitive), then by model_id.
    If multiple models have the same model_id, prefers the preferred_model_name if provided,
    otherwise prefers the highest threshold among models with thresholds.

    Args:
        name_or_id: Saved model name or underlying provider model_id
        preferred_model_name: Preferred saved model name when multiple models
      share the same model_id

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
    matches = []
    for m in user_manager.list_models():
        if m.model_id.lower() == lookup:
            matches.append(m)

    if not matches:
        return None

    # If we have a preferred model name, try to find it first
    if preferred_model_name:
        preferred_lower = preferred_model_name.lower()
        for m in matches:
            if m.name.lower() == preferred_lower:
                return m.compaction_threshold

    # Find all models that have thresholds
    models_with_thresholds = [m for m in matches if m.compaction_threshold is not None]

    if models_with_thresholds:
        # Return the highest threshold (most conservative)
        max_model = max(models_with_thresholds, key=lambda m: m.compaction_threshold or 0)
        return max_model.compaction_threshold

    # If no model has a threshold, return None
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
    result = user_manager.set_compaction_threshold(name, threshold)

    # Reload the model manager cache to ensure the change takes effect immediately
    reload_model_manager()

    return result
