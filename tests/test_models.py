"""Tests for the new provider-based model configuration system."""

import json
import tempfile
from pathlib import Path

from clippy.models import (
    ProviderConfig,
    UserModelConfig,
    UserModelManager,
    get_default_model_config,
    get_model_config,
    get_provider,
    get_providers,
    list_available_models,
    list_available_providers,
)


def test_provider_config_dataclass() -> None:
    """Test ProviderConfig dataclass creation."""
    config = ProviderConfig(
        name="test-provider",
        base_url="https://api.test.com/v1",
        api_key_env="TEST_API_KEY",
        description="Test Provider",
    )

    assert config.name == "test-provider"
    assert config.base_url == "https://api.test.com/v1"
    assert config.api_key_env == "TEST_API_KEY"
    assert config.description == "Test Provider"


def test_user_model_config_dataclass() -> None:
    """Test UserModelConfig dataclass creation."""
    config = UserModelConfig(
        name="my-model",
        provider="openai",
        model_id="gpt-5",
        description="My GPT-5 Model",
        is_default=True,
    )

    assert config.name == "my-model"
    assert config.provider == "openai"
    assert config.model_id == "gpt-5"
    assert config.description == "My GPT-5 Model"
    assert config.is_default is True


def test_providers_yaml_exists() -> None:
    """Test that providers.yaml file exists."""
    yaml_path = Path(__file__).parent.parent / "src" / "clippy" / "providers.yaml"
    assert yaml_path.exists(), "providers.yaml file should exist"


def test_load_providers() -> None:
    """Test loading providers from YAML."""
    providers = get_providers()

    # Should have multiple providers loaded
    assert len(providers) > 0, "Should load at least one provider"

    # Check that common providers exist
    assert "openai" in providers
    assert "anthropic" in providers
    assert "custom-anthropic" in providers
    assert "cerebras" in providers
    assert "gemini" in providers
    assert "ollama" in providers

    # Check structure
    for name, provider in providers.items():
        assert isinstance(provider, ProviderConfig)
        assert provider.name == name
        assert isinstance(provider.api_key_env, str)
        assert isinstance(provider.description, str)


def test_get_provider() -> None:
    """Test getting a specific provider."""
    provider = get_provider("openai")

    assert provider is not None
    assert provider.name == "openai"
    assert provider.base_url is None  # OpenAI uses default
    assert provider.api_key_env == "OPENAI_API_KEY"
    assert provider.pydantic_system == "openai"


def test_get_provider_anthropic() -> None:
    """Ensure anthropic provider metadata loads correctly."""
    provider = get_provider("anthropic")

    assert provider is not None
    assert provider.base_url == "https://api.anthropic.com/v1"
    assert provider.api_key_env == "ANTHROPIC_API_KEY"
    assert provider.pydantic_system == "anthropic"


def test_get_provider_gemini() -> None:
    """Ensure gemini provider metadata loads correctly."""
    provider = get_provider("gemini")

    assert provider is not None
    assert provider.base_url == "https://generativelanguage.googleapis.com/v1beta"
    assert provider.api_key_env == "GOOGLE_API_KEY"
    assert provider.pydantic_system == "google-gla"


def test_get_provider_nonexistent() -> None:
    """Test getting a provider that doesn't exist."""
    provider = get_provider("nonexistent-provider")
    assert provider is None


def test_list_available_providers() -> None:
    """Test listing available providers."""
    providers = list_available_providers()

    assert len(providers) > 0
    # Each item should be (name, description) tuple
    for name, description in providers:
        assert isinstance(name, str)
        assert isinstance(description, str)
        assert len(name) > 0
        assert len(description) > 0


def test_user_model_manager_with_temp_dir() -> None:
    """Test UserModelManager with a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_config_dir = Path(tmpdir)
        manager = UserModelManager(config_dir=temp_config_dir)

        # Should create config directory
        assert temp_config_dir.exists()
        assert manager.models_file.exists()

        # Should have default model (gpt-5)
        models = manager.list_models()
        assert len(models) == 1
        assert models[0].name == "gpt-5"
        assert models[0].provider == "openai"
        assert models[0].model_id == "gpt-5"
        assert models[0].is_default is True


def test_user_model_manager_add_model() -> None:
    """Test adding a model to UserModelManager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_config_dir = Path(tmpdir)
        manager = UserModelManager(config_dir=temp_config_dir)

        # Add a new model
        success, message = manager.add_model(
            name="my-llama",
            provider="ollama",
            model_id="llama3.2:latest",
            is_default=False,
        )

        assert success is True
        assert "Added model" in message

        # Verify it was added
        models = manager.list_models()
        assert len(models) == 2  # gpt-5 (default) + my-llama

        # Get the specific model
        llama = manager.get_model("my-llama")
        assert llama is not None
        assert llama.name == "my-llama"
        assert llama.provider == "ollama"
        assert llama.model_id == "llama3.2:latest"
        assert llama.description == "ollama/llama3.2:latest"
        assert llama.is_default is False


def test_user_model_manager_add_duplicate() -> None:
    """Test adding a duplicate model name."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_config_dir = Path(tmpdir)
        manager = UserModelManager(config_dir=temp_config_dir)

        # Try to add a model with existing name
        success, message = manager.add_model(
            name="gpt-5",
            provider="openai",
            model_id="gpt-5",
        )

        assert success is False
        assert "already exists" in message


def test_user_model_manager_add_invalid_provider() -> None:
    """Test adding a model with invalid provider."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_config_dir = Path(tmpdir)
        manager = UserModelManager(config_dir=temp_config_dir)

        # Try to add a model with non-existent provider
        success, message = manager.add_model(
            name="test",
            provider="nonexistent",
            model_id="test-model",
        )

        assert success is False
        assert "Unknown provider" in message


def test_user_model_manager_remove_model() -> None:
    """Test removing a model."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_config_dir = Path(tmpdir)
        manager = UserModelManager(config_dir=temp_config_dir)

        # Add a model
        manager.add_model(
            name="temp-model",
            provider="openai",
            model_id="gpt-4o",
        )

        # Remove it
        success, message = manager.remove_model("temp-model")

        assert success is True
        assert "Removed model" in message

        # Verify it's gone
        model = manager.get_model("temp-model")
        assert model is None


def test_user_model_manager_remove_nonexistent() -> None:
    """Test removing a model that doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_config_dir = Path(tmpdir)
        manager = UserModelManager(config_dir=temp_config_dir)

        success, message = manager.remove_model("nonexistent")

        assert success is False
        assert "not found" in message


def test_user_model_manager_set_default() -> None:
    """Test setting a model as default."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_config_dir = Path(tmpdir)
        manager = UserModelManager(config_dir=temp_config_dir)

        # Add a new model
        manager.add_model(
            name="my-model",
            provider="openai",
            model_id="gpt-4o",
        )

        # Set it as default
        success, message = manager.set_default("my-model")

        assert success is True
        assert "default" in message.lower()

        # Verify it's now default
        default = manager.get_default_model()
        assert default is not None
        assert default.name == "my-model"
        assert default.is_default is True

        # Verify old default is no longer default
        gpt5_model = manager.get_model("gpt-5")
        assert gpt5_model is not None
        assert gpt5_model.is_default is False


def test_user_model_manager_get_default() -> None:
    """Test getting the default model."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_config_dir = Path(tmpdir)
        manager = UserModelManager(config_dir=temp_config_dir)

        default = manager.get_default_model()

        assert default is not None
        assert default.name == "gpt-5"
        assert default.is_default is True


def test_get_model_config() -> None:
    """Test getting a model configuration and its provider."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_config_dir = Path(tmpdir)
        manager = UserModelManager(config_dir=temp_config_dir)

        # Add a test model
        manager.add_model(
            name="test-model",
            provider="cerebras",
            model_id="llama3.1-8b",
        )

        # Manually update global manager for testing
        import clippy.models

        clippy.models._user_manager = manager

        # Get the model config
        model, provider = get_model_config("test-model")

        assert model is not None
        assert provider is not None
        assert model.name == "test-model"
        assert model.provider == "cerebras"
        assert model.model_id == "llama3.1-8b"
        assert model.description == "cerebras/llama3.1-8b"
        assert provider.name == "cerebras"
        assert provider.base_url == "https://api.cerebras.ai/v1"


def test_get_default_model_config() -> None:
    """Test getting the default model configuration."""
    # Use a temporary directory to ensure test isolation
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_config_dir = Path(tmpdir)
        manager = UserModelManager(config_dir=temp_config_dir)

        # Manually set the global manager for this test
        import clippy.models

        clippy.models._user_manager = manager

        model, provider = get_default_model_config()

        assert model is not None
        assert provider is not None
        assert model.is_default is True
        # Should default to "gpt-5" in a clean environment
        assert model.name == "gpt-5"
        assert model.provider == "openai"
        assert provider.name == "openai"


def test_list_available_models() -> None:
    """Test listing available user models."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_config_dir = Path(tmpdir)
        manager = UserModelManager(config_dir=temp_config_dir)

        # Add some models
        manager.add_model("model1", "openai", "gpt-4o")
        manager.add_model("model2", "cerebras", "llama3.1-8b", is_default=False)

        # Manually update global manager for testing
        import clippy.models

        clippy.models._user_manager = manager

        models = list_available_models()

        # Should have 3 models: gpt-5 (default) + model1 + model2
        assert len(models) >= 2

        # Check structure
        for model_config in models:
            name, description, is_default = model_config[:3]  # Extract first three values
            # Try to get threshold if it exists (newer models might have it)
            _threshold = model_config[3] if len(model_config) > 3 else None

            assert isinstance(name, str)
            assert isinstance(description, str)
            assert isinstance(is_default, bool)


def test_persistence() -> None:
    """Test that model configurations persist across manager instances."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_config_dir = Path(tmpdir)

        # Create manager and add a model
        manager1 = UserModelManager(config_dir=temp_config_dir)
        manager1.add_model("persistent", "ollama", "llama2")

        # Create a new manager instance pointing to same directory
        manager2 = UserModelManager(config_dir=temp_config_dir)

        # Should be able to retrieve the model
        model = manager2.get_model("persistent")
        assert model is not None
        assert model.name == "persistent"
        assert model.model_id == "llama2"


def test_json_format() -> None:
    """Test that the JSON file has correct format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_config_dir = Path(tmpdir)
        manager = UserModelManager(config_dir=temp_config_dir)

        # Add a model
        manager.add_model("test", "openai", "gpt-4o")

        # Read the JSON file directly
        with open(manager.models_file) as f:
            data = json.load(f)

        # Verify structure
        assert "models" in data
        assert isinstance(data["models"], list)
        assert len(data["models"]) == 2  # gpt-5 + test

        # Verify each model has required fields
        for model in data["models"]:
            assert "name" in model
            assert "provider" in model
            assert "model_id" in model
            assert "description" in model
            assert "is_default" in model
