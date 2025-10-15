"""Tests for the model configuration system."""

from pathlib import Path

from clippy.models import ModelConfig, get_model_config, list_available_models


def test_model_config_dataclass() -> None:
    """Test ModelConfig dataclass creation."""
    config = ModelConfig(
        name="test-model",
        model_id="test-id",
        base_url="https://api.test.com/v1",
        description="Test Model",
        api_key_env="TEST_API_KEY",
    )

    assert config.name == "test-model"
    assert config.model_id == "test-id"
    assert config.base_url == "https://api.test.com/v1"
    assert config.description == "Test Model"
    assert config.api_key_env == "TEST_API_KEY"


def test_yaml_file_exists() -> None:
    """Test that models.yaml file exists."""
    yaml_path = Path(__file__).parent.parent / "src" / "clippy" / "models.yaml"
    assert yaml_path.exists(), "models.yaml file should exist"


def test_load_model_presets() -> None:
    """Test loading model presets from YAML."""
    models = list_available_models()

    # Should have multiple models loaded
    assert len(models) > 0, "Should load at least one model"

    # Check structure
    for name, description in models:
        assert isinstance(name, str)
        assert isinstance(description, str)
        assert len(name) > 0
        assert len(description) > 0


def test_get_openai_model() -> None:
    """Test getting OpenAI model configuration."""
    config = get_model_config("gpt-5")

    assert config is not None
    if config is not None:
        assert config.name == "gpt-5"
        assert config.model_id == "gpt-5"
        assert config.base_url is None  # OpenAI uses default
        assert config.api_key_env == "OPENAI_API_KEY"


def test_get_cerebras_model() -> None:
    """Test getting Cerebras model configuration."""
    config = get_model_config("cerebras")

    assert config is not None
    if config is not None:
        assert config.name == "cerebras"
        assert config.model_id == "qwen-3-coder-480b"
        assert config.base_url == "https://api.cerebras.ai/v1"
        assert config.api_key_env == "CEREBRAS_API_KEY"


def test_get_ollama_model() -> None:
    """Test getting Ollama model configuration."""
    config = get_model_config("ollama")

    assert config is not None
    if config is not None:
        assert config.name == "ollama"
        assert config.model_id == "llama2"
        assert config.base_url == "http://localhost:11434/v1"
        assert config.api_key_env == "OLLAMA_API_KEY"


def test_get_groq_model() -> None:
    """Test getting Groq model configuration."""
    config = get_model_config("groq")

    assert config is not None
    if config is not None:
        assert config.name == "groq"
        assert config.model_id == "llama3-70b-8192"
        assert config.base_url == "https://api.groq.com/openai/v1"
        assert config.api_key_env == "GROQ_API_KEY"


def test_get_together_model() -> None:
    """Test getting Together AI model configuration."""
    config = get_model_config("together-llama-8b")

    assert config is not None
    if config is not None:
        assert config.name == "together-llama-8b"
        assert config.model_id == "meta-llama/Llama-3-8b-chat-hf"
        assert config.base_url == "https://api.together.xyz/v1"
        assert config.api_key_env == "TOGETHER_API_KEY"


def test_get_deepseek_model() -> None:
    """Test getting DeepSeek model configuration."""
    config = get_model_config("deepseek")

    assert config is not None
    if config is not None:
        assert config.name == "deepseek"
        assert config.model_id == "deepseek-coder"
        assert config.base_url == "https://api.deepseek.com/v1"
        assert config.api_key_env == "DEEPSEEK_API_KEY"


def test_get_nonexistent_model() -> None:
    """Test getting a model that doesn't exist."""
    config = get_model_config("nonexistent-model")
    assert config is None


def test_case_insensitive_lookup() -> None:
    """Test that model lookup is case-insensitive."""
    config_lower = get_model_config("gpt-5")
    config_upper = get_model_config("gpt-5")
    config_mixed = get_model_config("gpt-5")

    assert config_lower is not None
    assert config_upper is not None
    assert config_mixed is not None
    if config_lower is not None and config_upper is not None and config_mixed is not None:
        assert config_lower.name == config_upper.name == config_mixed.name


def test_all_models_have_required_fields() -> None:
    """Test that all models have required fields populated."""
    models = list_available_models()

    for name, description in models:
        config = get_model_config(name)
        assert config is not None
        if config is not None:
            assert config.name
            assert config.model_id
            assert config.description
            assert config.api_key_env
            # base_url can be None for OpenAI


def test_api_key_env_vars_unique_per_provider() -> None:
    """Test that different providers use different API key env vars."""
    openai = get_model_config("gpt-5")
    cerebras = get_model_config("cerebras")
    groq = get_model_config("groq")

    assert openai is not None
    assert cerebras is not None
    assert groq is not None

    if openai is not None and cerebras is not None and groq is not None:
        assert openai.api_key_env == "OPENAI_API_KEY"
        assert cerebras.api_key_env == "CEREBRAS_API_KEY"
        assert groq.api_key_env == "GROQ_API_KEY"
        assert openai.api_key_env != cerebras.api_key_env
        assert cerebras.api_key_env != groq.api_key_env
