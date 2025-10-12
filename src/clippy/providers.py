"""LLM provider abstraction layer for model-agnostic support."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ContentBlockType(Enum):
    """Types of content blocks in responses."""
    TEXT = "text"
    TOOL_USE = "tool_use"


@dataclass
class ContentBlock:
    """Represents a content block in a response."""
    type: ContentBlockType
    text: Optional[str] = None
    name: Optional[str] = None  # For tool use
    input: Optional[Dict[str, Any]] = None  # For tool use
    id: Optional[str] = None  # For tool use


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    content: List[ContentBlock]
    stop_reason: str
    model: str
    usage: Optional[Dict[str, int]] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize the provider with API key and additional config."""
        pass

    @abstractmethod
    def create_message(
        self,
        messages: List[Dict[str, Any]],
        system: str,
        tools: List[Dict[str, Any]],
        max_tokens: int,
        model: str,
        **kwargs
    ) -> LLMResponse:
        """
        Create a message with the LLM provider.

        Args:
            messages: Conversation history in standardized format
            system: System prompt
            tools: Tool definitions in standardized format
            max_tokens: Maximum tokens for response
            model: Model identifier
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse object with standardized response
        """
        pass

    @abstractmethod
    def get_default_model(self) -> str:
        """Get the default model for this provider."""
        pass

    @abstractmethod
    def convert_tools_to_provider_format(self, tools: List[Dict[str, Any]]) -> Any:
        """Convert standardized tool format to provider-specific format."""
        pass

    @abstractmethod
    def convert_messages_to_provider_format(self, messages: List[Dict[str, Any]]) -> Any:
        """Convert standardized message format to provider-specific format."""
        pass


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation."""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize Anthropic provider."""
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError(
                "anthropic package is required for AnthropicProvider. "
                "Install it with: pip install anthropic"
            )

        self.client = Anthropic(api_key=api_key)

    def create_message(
        self,
        messages: List[Dict[str, Any]],
        system: str,
        tools: List[Dict[str, Any]],
        max_tokens: int,
        model: str,
        **kwargs
    ) -> LLMResponse:
        """Create a message using Anthropic's API."""
        # Convert to Anthropic format
        anthropic_messages = self.convert_messages_to_provider_format(messages)
        anthropic_tools = self.convert_tools_to_provider_format(tools)

        # Call Anthropic API
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=anthropic_messages,
            tools=anthropic_tools,
            **kwargs
        )

        # Convert response to standardized format
        content_blocks = []
        for block in response.content:
            if block.type == "text":
                content_blocks.append(ContentBlock(
                    type=ContentBlockType.TEXT,
                    text=block.text
                ))
            elif block.type == "tool_use":
                content_blocks.append(ContentBlock(
                    type=ContentBlockType.TOOL_USE,
                    name=block.name,
                    input=block.input,
                    id=block.id
                ))

        return LLMResponse(
            content=content_blocks,
            stop_reason=response.stop_reason,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        )

    def get_default_model(self) -> str:
        """Get the default Anthropic model."""
        return "claude-3-5-sonnet-20241022"

    def convert_tools_to_provider_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Anthropic uses the same tool format as our standard."""
        return tools

    def convert_messages_to_provider_format(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Anthropic uses the same message format as our standard."""
        return messages


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation."""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize OpenAI provider."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is required for OpenAIProvider. "
                "Install it with: pip install openai"
            )

        self.client = OpenAI(api_key=api_key)

    def create_message(
        self,
        messages: List[Dict[str, Any]],
        system: str,
        tools: List[Dict[str, Any]],
        max_tokens: int,
        model: str,
        **kwargs
    ) -> LLMResponse:
        """Create a message using OpenAI's API."""
        # Convert to OpenAI format
        openai_messages = self.convert_messages_to_provider_format(messages)

        # Add system message at the beginning
        openai_messages = [{"role": "system", "content": system}] + openai_messages

        openai_tools = self.convert_tools_to_provider_format(tools)

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=openai_messages,
            tools=openai_tools,
            **kwargs
        )

        # Convert response to standardized format
        content_blocks = []
        message = response.choices[0].message

        # Handle text content
        if message.content:
            content_blocks.append(ContentBlock(
                type=ContentBlockType.TEXT,
                text=message.content
            ))

        # Handle tool calls
        if message.tool_calls:
            for tool_call in message.tool_calls:
                import json
                content_blocks.append(ContentBlock(
                    type=ContentBlockType.TOOL_USE,
                    name=tool_call.function.name,
                    input=json.loads(tool_call.function.arguments),
                    id=tool_call.id
                ))

        return LLMResponse(
            content=content_blocks,
            stop_reason=response.choices[0].finish_reason,
            model=response.model,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            } if response.usage else None
        )

    def get_default_model(self) -> str:
        """Get the default OpenAI model."""
        return "gpt-4o"

    def convert_tools_to_provider_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert tools to OpenAI format."""
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            })
        return openai_tools

    def convert_messages_to_provider_format(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert messages to OpenAI format."""
        openai_messages = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            # Handle different content types
            if isinstance(content, str):
                # Simple text message
                openai_messages.append({
                    "role": role,
                    "content": content
                })
            elif isinstance(content, list):
                # Complex message with multiple blocks
                text_parts = []
                tool_calls = []
                tool_results = []

                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(block["text"])
                        elif block.get("type") == "tool_use":
                            import json
                            tool_calls.append({
                                "id": block["id"],
                                "type": "function",
                                "function": {
                                    "name": block["name"],
                                    "arguments": json.dumps(block["input"])
                                }
                            })
                        elif block.get("type") == "tool_result":
                            # OpenAI expects tool results as separate messages
                            tool_results.append({
                                "role": "tool",
                                "tool_call_id": block["tool_use_id"],
                                "content": block["content"]
                            })

                # Add assistant message with text and/or tool calls
                if role == "assistant":
                    msg_data = {"role": role}
                    if text_parts:
                        msg_data["content"] = "\n".join(text_parts)
                    if tool_calls:
                        msg_data["tool_calls"] = tool_calls
                    openai_messages.append(msg_data)

                # Add tool result messages
                openai_messages.extend(tool_results)

        return openai_messages


class ProviderFactory:
    """Factory for creating LLM provider instances."""

    PROVIDERS = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
    }

    @staticmethod
    def create_provider(
        provider_name: str,
        api_key: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """
        Create a provider instance.

        Args:
            provider_name: Name of the provider ("anthropic", "openai")
            api_key: API key for the provider
            **kwargs: Additional provider-specific configuration

        Returns:
            LLMProvider instance

        Raises:
            ValueError: If provider name is not supported
        """
        provider_name = provider_name.lower()

        if provider_name not in ProviderFactory.PROVIDERS:
            supported = ", ".join(ProviderFactory.PROVIDERS.keys())
            raise ValueError(
                f"Unsupported provider: {provider_name}. "
                f"Supported providers: {supported}"
            )

        provider_class = ProviderFactory.PROVIDERS[provider_name]
        return provider_class(api_key=api_key, **kwargs)

    @staticmethod
    def get_supported_providers() -> List[str]:
        """Get list of supported provider names."""
        return list(ProviderFactory.PROVIDERS.keys())
