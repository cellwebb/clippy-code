"""Model configuration and presets for different LLM providers."""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class ModelConfig:
    """Configuration for a specific model/provider combination."""

    name: str
    model_id: str
    base_url: str | None
    description: str
    api_key_env: str  # Environment variable name for API key


def _load_model_presets() -> dict[str, ModelConfig]:
    """Load model presets from YAML configuration file."""
    # Load the YAML file from the same directory as this module
    yaml_path = Path(__file__).parent / "models.yaml"

    with open(yaml_path) as f:
        config = yaml.safe_load(f)

    # Parse YAML into ModelConfig objects
    presets: dict[str, ModelConfig] = {}

    for provider_name, provider_data in config["providers"].items():
        base_url = provider_data.get("base_url")
        api_key_env = provider_data.get("api_key_env", "OPENAI_API_KEY")
        default_model = provider_data.get("default_model")
        models = provider_data.get("models", {})

        # Add provider name as a model alias if it has a default model
        if default_model and default_model in models:
            model_data = models[default_model]
            presets[provider_name] = ModelConfig(
                name=provider_name,
                model_id=model_data["model_id"],
                base_url=base_url,
                description=model_data["description"],
                api_key_env=api_key_env,
            )

        # Add all individual models
        for model_name, model_data in models.items():
            presets[model_name] = ModelConfig(
                name=model_name,
                model_id=model_data["model_id"],
                base_url=base_url,
                description=model_data["description"],
                api_key_env=api_key_env,
            )

    return presets


# Load presets on module import
MODEL_PRESETS: dict[str, ModelConfig] = _load_model_presets()


def get_model_config(name: str) -> ModelConfig | None:
    """Get model configuration by name."""
    return MODEL_PRESETS.get(name.lower())


def list_available_models() -> list[tuple[str, str]]:
    """Get list of available models with descriptions."""
    return [(config.name, config.description) for config in MODEL_PRESETS.values()]
