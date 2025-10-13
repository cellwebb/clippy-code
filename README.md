# clippy-code 📎

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

> A production-ready, model-agnostic CLI coding agent built with extensibility and safety as first-class concerns.

clippy-code is an AI-powered development assistant that demonstrates modern software engineering practices through a clean, modular architecture. It features provider abstraction, robust permission controls, and an intuitive CLI interface—designed to be both powerful for users and maintainable for developers.

**🎯 Portfolio Highlights**: Model-agnostic LLM abstraction • Security-first design • SOLID principles • Comprehensive type safety • Production-ready architecture

## Table of Contents

- [Technical Highlights](#technical-highlights)
- [Installation](#installation)
- [Quick Start](#usage)
- [Architecture Deep Dive](#architecture-deep-dive)
  - [System Architecture](#system-architecture)
  - [Design Decisions](#design-decisions)
  - [Technical Challenges & Solutions](#technical-challenges--solutions)
  - [Project Structure](#project-structure)
  - [Code Quality Standards](#code-quality-standards)
- [Extensibility](#extensibility)
  - [Adding New LLM Providers](#adding-new-llm-providers)
  - [Adding New Tools](#adding-new-tools)
- [Development & Testing](#development--testing)
- [Safety & Security Features](#safety--security-features)
- [Configuration](#configuration)
- [Skills Demonstrated](#skills-demonstrated)
- [Future Roadmap](#future-roadmap)

## Technical Highlights

### Architecture & Design Patterns

- **Provider Abstraction Layer**: Clean separation between business logic and LLM APIs using the Abstract Factory and Strategy patterns
- **Model-Agnostic Design**: Plug-and-play support for multiple LLM providers (Anthropic Claude, OpenAI GPT) with standardized interfaces
- **Permission System**: Policy-based security model with configurable access controls and approval workflows
- **Tool System**: Extensible tool framework with clear separation of concerns (definition, execution, permissions)
- **Error Handling**: Comprehensive error handling with graceful degradation and user-friendly messaging

### Engineering Practices

- **Type Safety**: Fully typed Python codebase using type hints and Pydantic models
- **Dependency Injection**: Loose coupling through dependency injection for testability
- **Clean Code**: Adherence to SOLID principles and PEP 8 standards
- **Modular Design**: Clear module boundaries with single responsibility principle
- **Configuration Management**: Multi-layer configuration (environment, CLI args, defaults)

### Key Features

- **🏗️ Provider Abstraction**: Unified interface for multiple LLM providers—easily extensible to Google Gemini, Cohere, or custom models
- **🔒 Security-First**: Fine-grained permission system with approval workflows for destructive operations
- **🎨 Rich UX**: Beautiful terminal UI with syntax highlighting, panels, and markdown rendering
- **🔄 Stateful & Stateless Modes**: Interactive REPL for multi-turn conversations or one-shot execution
- **⚡ Async-Ready**: Architecture designed for future async/await implementation
- **🛠️ Tool Framework**: Extensible tool system for file operations, command execution, and more

## Installation

### From PyPI (Recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install clippy-code
uv tool install clippy-code

# Or use pipx
pipx install clippy-code
```

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/clippy.git
cd clippy

# Install with uv (default provider: Anthropic)
uv pip install -e .

# Or install with OpenAI support
uv pip install -e ".[openai]"

# Or install with all providers
uv pip install -e ".[all-providers]"

# Or install with dev dependencies
uv pip install -e ".[dev]"
```

### Setup API Keys

clippy-code supports multiple LLM providers. Configure the provider you want to use:

#### Anthropic Claude (Default)

```bash
# Option 1: Create a .env file in the project directory
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env

# Option 2: Create a global config in your home directory
echo "ANTHROPIC_API_KEY=your_api_key_here" > ~/.clippy.env

# Option 3: Export as environment variable
export ANTHROPIC_API_KEY=your_api_key_here
```

Get your API key from [Anthropic Console](https://console.anthropic.com/)

#### OpenAI

```bash
# Option 1: Add to .env file
echo "OPENAI_API_KEY=your_api_key_here" >> .env

# Option 2: Add to global config
echo "OPENAI_API_KEY=your_api_key_here" >> ~/.clippy.env

# Option 3: Export as environment variable
export OPENAI_API_KEY=your_api_key_here
```

Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

## Usage

### One-Shot Mode

Execute a single task and exit:

```bash
# Simple task (uses default provider: Anthropic)
clippy "create a hello world python script"

# Use OpenAI instead
clippy --provider openai "create a hello world python script"

# Specify a particular model
clippy --model gpt-4o "refactor the main.py file to use async/await"
clippy --provider anthropic --model claude-3-5-sonnet-20241022 "analyze this code"

# Auto-approve all actions (use with caution!)
clippy -y "write unit tests for utils.py"
```

### Interactive Mode

Start an interactive session:

```bash
# Start interactive mode
clippy -i

# Or just run clippy with no arguments
clippy
```

In interactive mode, you can:

- Have multi-turn conversations
- `/reset` - Reset the conversation history
- `/help` - Show available commands
- `/exit` or `/quit` - Exit clippy-code
- Press Ctrl+C during execution to interrupt

### Document Mode (NEW!)

Experience a Microsoft Word-inspired TUI interface where you type directly on the page:

```bash
# Start document mode
clippy -d

# Or with specific model
clippy -d --model gpt-4o
```

Document mode features:

- 📄 **Word-like document interface** with proper borders and styling
- 💬 **Colored message backgrounds**:
  - Blue background for your messages
  - Gray background for clippy's responses
- ⌨️ **Type in the blue input area** at the bottom
- ✅ **Press `Enter` to send** your message
- 🎨 **Clean scrolling conversation** that looks like a real document
- 📊 **Live status bar** showing model, message count, and tokens
- **Keyboard shortcuts**:
  - `Enter` - Submit your message
  - `Ctrl+Q` - Quit document
  - `Ctrl+H` - Toggle help
  - `Ctrl+R` - Reset conversation
  - `Ctrl+S` - Show status

Document mode provides a Microsoft Word-inspired interface with color-coded messages and a clean, professional appearance.

## Permission System

has a built-in permission system to keep you safe:

### Auto-Approved Actions (No confirmation needed)

- 📖 **read_file** - Read file contents
- 📂 **list_directory** - List directory contents
- 🔍 **search_files** - Search for files
- ℹ️ **get_file_info** - Get file metadata

### Require Approval (Will ask before executing)

- ✏️ **write_file** - Write or modify files
- 🗑️ **delete_file** - Delete files
- 📁 **create_directory** - Create new directories
- ⚡ **execute_command** - Run shell commands

When clippy-code wants to perform an action that requires approval, you'll see:

```
→ write_file
  path: example.py
  content: print("Hello, World!")

[?] Approve this action? [y/N/stop]:
```

Options:

- `y` - Approve and execute
- `N` - Reject (default)
- `stop` - Stop execution entirely

## Available Tools

clippy-code has access to these tools:

| Tool               | Description               | Auto-Approved |
| ------------------ | ------------------------- | ------------- |
| `read_file`        | Read file contents        | ✅            |
| `write_file`       | Write/modify files        | ❌            |
| `delete_file`      | Delete files              | ❌            |
| `list_directory`   | List directory contents   | ✅            |
| `create_directory` | Create directories        | ❌            |
| `execute_command`  | Run shell commands        | ❌            |
| `search_files`     | Search with glob patterns | ✅            |
| `get_file_info`    | Get file metadata         | ✅            |

## Examples

### Example 1: Creating a new feature

```bash
clippy "create a user authentication module with login and signup functions"
```

### Example 2: Code review

```bash
clippy "review the code in src/utils.py and suggest improvements"
```

### Example 3: Debugging

```bash
clippy "find and fix the bug causing the test_api.py tests to fail"
```

### Example 4: Refactoring

```bash
clippy "refactor database.py to use async/await instead of blocking calls"
```

## Configuration

### Environment Variables

#### Provider Configuration

- `CLIPPY_PROVIDER` - LLM provider to use: `anthropic` (default) or `openai`
- `CLIPPY_MODEL` - Model identifier (uses provider default if not set)
- `CLIPPY_MAX_TOKENS` - Max tokens for responses (default: 4096)

#### API Keys

- `ANTHROPIC_API_KEY` - Your Anthropic API key (required for Anthropic provider)
- `OPENAI_API_KEY` - Your OpenAI API key (required for OpenAI provider)

### Provider-Specific Models

#### Anthropic Models

- `claude-3-5-sonnet-20241022` (default)
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`

#### OpenAI Models

- `gpt-4o` (default)
- `gpt-4-turbo`
- `gpt-4`
- `gpt-3.5-turbo`

### Example .env File

```bash
# Choose your provider
CLIPPY_PROVIDER=anthropic  # or openai

# Set the appropriate API key
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here

# Optional: Set a specific model
CLIPPY_MODEL=claude-3-5-sonnet-20241022  # or gpt-4o

# Optional: Configure max tokens
CLIPPY_MAX_TOKENS=4096
```

### Custom Permissions (Coming Soon)

You'll be able to customize permission levels via a config file.

## Architecture Deep Dive

### System Architecture

clippy-code follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│                   CLI Layer                         │
│  (Argument Parsing, User Interaction, Display)      │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│                  Agent Layer                        │
│  (Conversation Management, Response Processing)     │
└─────────────┬───────────────────┬───────────────────┘
              │                   │
┌─────────────▼─────────┐  ┌──────▼──────────────────┐
│   Provider Layer      │  │   Executor Layer        │
│ (LLM Abstraction)     │  │ (Tool Execution)        │
└─────────────┬─────────┘  └──────┬──────────────────┘
              │                   │
┌─────────────▼─────────┐  ┌──────▼──────────────────┐
│  Anthropic | OpenAI   │  │  Permission System      │
│  (Concrete Providers) │  │  (Policy Enforcement)   │
└───────────────────────┘  └─────────────────────────┘
```

### Design Decisions

#### 1. **Provider Abstraction Pattern**

**Challenge**: Need to support multiple LLM providers with different API interfaces.

**Solution**: Implemented an abstract base class `LLMProvider` with concrete implementations for each provider. This allows:

- Runtime provider switching without code changes
- Consistent response format across providers
- Easy addition of new providers (Gemini, Cohere, etc.)

**Code Example**:

```python
class LLMProvider(ABC):
    @abstractmethod
    def create_message(self, messages, system, tools, max_tokens, model) -> LLMResponse:
        pass

class AnthropicProvider(LLMProvider):
    # Anthropic-specific implementation

class OpenAIProvider(LLMProvider):
    # OpenAI-specific implementation with format conversion
```

#### 2. **Permission System Architecture**

**Challenge**: Balance automation with user control and safety.

**Solution**: Policy-based permission system with three access levels:

- **Auto-Approved**: Read-only operations (read_file, list_directory)
- **Require Approval**: Destructive operations (write_file, delete_file)
- **Denied**: Completely blocked operations

**Benefits**:

- Prevents accidental file deletion or unwanted command execution
- User maintains full control over agent actions
- Extensible for custom permission policies

#### 3. **Tool System Design**

Tools are defined declaratively and executed through a centralized executor:

```python
# Tool Definition (What the LLM sees)
{
    "name": "write_file",
    "description": "Write content to a file",
    "input_schema": {...}
}

# Tool Execution (How it's actually run)
executor.execute(tool_name, tool_input)
  → permission_check()
  → execute_action()
  → return result
```

### Technical Challenges & Solutions

#### Challenge 1: Cross-Provider Tool Format Incompatibility

**Problem**: Different LLM providers use incompatible formats for tool/function calling:

- Anthropic uses a flat `tools` array with `input_schema`
- OpenAI uses nested `functions` with `parameters` instead of `input_schema`
- Message formats differ (Anthropic supports multi-part content blocks, OpenAI uses separate tool result messages)

**Solution**:

- Created provider-specific conversion methods (`convert_tools_to_provider_format`, `convert_messages_to_provider_format`)
- Standardized internal format based on Anthropic's schema (cleaner, more expressive)
- OpenAI provider translates on-the-fly during API calls

**Result**: ✅ Single tool definition works across all providers. Adding a new provider requires ~100 lines of conversion logic.

#### Challenge 2: Maintaining Conversation State Across Providers

**Problem**: Conversation history must be preserved in a provider-agnostic format, but each provider expects different structures for tool results.

**Solution**:

- Stored conversation history in standardized format (Anthropic-like)
- Provider implementations handle conversion during API calls
- Created `LLMResponse` dataclass to normalize responses back to standard format

**Result**: ✅ Conversation history remains provider-agnostic. Switching providers mid-conversation is architecturally possible.

#### Challenge 3: Balancing Type Safety with Dynamic Tool Execution

**Problem**: Tool execution is dynamic (mapped from string names), but we want compile-time type safety.

**Solution**:

- Used Enums for `ActionType` to prevent typos
- Centralized tool name → action type mapping in a single dictionary
- Pydantic models for runtime validation of tool inputs
- Type hints throughout for static analysis with MyPy

**Result**: ✅ Caught errors at both compile-time (MyPy) and runtime (Pydantic validation).

#### Challenge 4: User Experience During Long-Running Operations

**Problem**: Agent might make multiple tool calls in sequence; users need visibility and control.

**Solution**:

- Rich terminal UI with real-time feedback for each operation
- Interrupt handling (Ctrl+C) at multiple levels:
  - During LLM API calls
  - During tool execution
  - During approval prompts
- Graceful degradation—partial progress is preserved

**Result**: ✅ Users can interrupt at any time without losing context. Operations are transparent and controllable.

### Project Structure

```
clippy/
├── src/
│   └── clippy/
│       ├── __init__.py
│       ├── __main__.py       # Entry point
│       ├── cli.py            # CLI interface & argument parsing
│       ├── agent.py          # Core agent orchestration (model-agnostic)
│       ├── providers.py      # LLM provider abstraction layer
│       │                     # - LLMProvider (ABC)
│       │                     # - AnthropicProvider
│       │                     # - OpenAIProvider
│       │                     # - ProviderFactory
│       ├── tools.py          # Tool definitions (schema-driven)
│       ├── executor.py       # Action execution engine
│       └── permissions.py    # Permission system & policies
├── tests/                    # Unit & integration tests
├── pyproject.toml            # Modern Python packaging
├── LICENSE                   # MIT License
└── README.md
```

### Code Quality Standards

This project maintains high code quality standards:

| Tool           | Purpose              | Configuration                  |
| -------------- | -------------------- | ------------------------------ |
| **Ruff**       | Linting & Formatting | Modern, fast Python linter     |
| **MyPy**       | Static Type Checking | Strict mode enabled            |
| **Pytest**     | Testing Framework    | Coverage reporting included    |
| **Pre-commit** | Git Hooks            | (Coming soon) Automated checks |

All code follows:

- PEP 8 style guidelines
- Type hints on all functions
- Comprehensive docstrings (Google style)
- Maximum line length: 100 characters

## Development & Testing

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/clippy.git
cd clippy

# Create a virtual environment with uv
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate     # On Windows

# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Run the CLI in development
python -m clippy
```

### Code Quality Tools

Maintain code quality with these commands:

```bash
# Auto-format code (PEP 8 compliant)
uv run ruff format .

# Lint and check for issues
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .

# Type checking with MyPy
uv run mypy src/clippy
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage reporting
uv run pytest --cov=clippy --cov-report=html

# Run specific test file
uv run pytest tests/test_permissions.py

# Run tests matching a pattern
uv run pytest -k "test_provider"
```

**Testing Philosophy**:

- Unit tests for individual components (providers, executor, permissions)
- Integration tests for end-to-end workflows
- Mock external API calls to ensure tests are fast and reliable
- Aim for >80% code coverage

### Building and Publishing

```bash
# Build the package
uv build

# Publish to PyPI (requires credentials)
uv publish

# Or publish to TestPyPI first
uv publish --index-url https://test.pypi.org/simple/
```

## Safety & Security Features

clippy-code implements multiple layers of security to protect users and their systems:

### 1. **Permission System (Policy-Based Access Control)**

- Three-tier permission model: Auto-approved, Require-approval, Denied
- Configurable permission policies (extensible for custom rules)
- Principle of least privilege: Read-only operations auto-approved, write operations require confirmation

### 2. **User Approval Workflow**

- Interactive prompts for destructive operations
- Full visibility into what the agent wants to do before execution
- Abort option to immediately halt execution chain

### 3. **Interrupt Handling**

- Multi-level interrupt support (Ctrl+C):
  - During LLM API calls
  - During tool execution
  - During user input prompts
- Graceful cleanup without data corruption
- Exception handling preserves conversation state

### 4. **Input Validation**

- Schema validation for all tool inputs using Pydantic
- Path traversal prevention for file operations
- Command injection protection for shell execution

### 5. **Execution Boundaries**

- Command timeout limits (30 seconds default)
- Maximum iteration caps prevent infinite loops
- Resource usage monitoring (future enhancement)

### 6. **Conversation Isolation**

- Session-based conversation history
- `/reset` command to clear context
- No data persistence without explicit user action

## Troubleshooting

**API Key Not Found**

```
Error: ANTHROPIC_API_KEY not found in environment
```

→ Make sure you've set up your API key (see Installation step 3)

**Permission Denied**

```
Action denied by policy
```

→ The action is blocked by the permission system. Modify permissions if needed.

**Command Timeout**

```
Command timed out after 30 seconds
```

→ The command took too long. Consider breaking it into smaller tasks.

## Contributing

Contributions are welcome! Feel free to:

- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

## License

MIT License - see LICENSE file for details

## Extensibility

### Adding New LLM Providers

clippy-code's provider abstraction makes it straightforward to add support for new LLM services. Here's the process:

#### Step-by-Step Guide

**1. Create Provider Class**

Inherit from `LLMProvider` and implement the abstract methods:

```python
class GeminiProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize the Google Gemini client."""
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel('gemini-pro')

    def create_message(self, messages, system, tools, max_tokens, model, **kwargs):
        """Convert to Gemini format and make API call."""
        # Format conversion logic
        # API call
        # Response normalization
        return LLMResponse(...)

    def get_default_model(self) -> str:
        return "gemini-pro"

    def convert_tools_to_provider_format(self, tools):
        """Map clippy-code tool schema to Gemini function calling format."""
        # Conversion logic
        pass

    def convert_messages_to_provider_format(self, messages):
        """Map clippy-code message format to Gemini format."""
        # Conversion logic
        pass
```

**2. Register Provider**

Add to the factory in `providers.py`:

```python
class ProviderFactory:
    PROVIDERS = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,  # New provider
    }
```

**3. Add Dependency**

Update `pyproject.toml`:

```toml
[project.optional-dependencies]
gemini = ["google-generativeai>=0.3.0"]
```

**4. Update CLI** (optional)

Add provider choice to argument parser in `cli.py`.

#### Design Philosophy

The abstraction handles:

- ✅ **Response Normalization**: All providers return standardized `LLMResponse` objects
- ✅ **Tool Format Conversion**: Automatic mapping between clippy-code's tool schema and provider-specific formats
- ✅ **Message Format Conversion**: Handles differences in conversation history structure
- ✅ **Error Handling**: Consistent error responses across providers

### Adding New Tools

Tools follow a declarative pattern—define once, use everywhere:

```python
# 1. Add tool definition to tools.py
{
    "name": "run_tests",
    "description": "Run test suite for a project",
    "input_schema": {
        "type": "object",
        "properties": {
            "test_path": {"type": "string", "description": "Path to test directory"},
            "verbose": {"type": "boolean", "description": "Verbose output"}
        },
        "required": ["test_path"]
    }
}

# 2. Add execution logic to executor.py
def _execute_run_tests(self, test_path: str, verbose: bool = False) -> tuple:
    # Implementation
    return (success, message, result)

# 3. Map in executor dispatch
action_map = {
    # ...
    "run_tests": ActionType.RUN_TESTS,
}
```

This pattern ensures:

- **Type Safety**: Schema validation via Pydantic
- **Consistency**: Single source of truth for tool definitions
- **Maintainability**: Clear separation between definition and implementation

## Skills Demonstrated

This project showcases proficiency in:

### Software Engineering

- **Design Patterns**: Abstract Factory, Strategy, Dependency Injection, Repository
- **SOLID Principles**: Single Responsibility, Open/Closed, Dependency Inversion
- **Architectural Patterns**: Layered architecture, clean separation of concerns
- **API Design**: Creating intuitive, extensible interfaces

### Python Development

- **Modern Python**: Type hints, dataclasses, abstract base classes, Pydantic
- **Packaging**: Modern pyproject.toml, optional dependencies, entry points
- **Code Quality**: Ruff linting/formatting, MyPy type checking, pytest testing
- **CLI Development**: argparse, prompt_toolkit, rich terminal UI

### System Design

- **Abstraction Layers**: Provider-agnostic design for multiple backends
- **Error Handling**: Graceful degradation, user-friendly error messages
- **State Management**: Conversation history, session management
- **Configuration Management**: Multi-layer config (env, CLI, defaults)

### Product Thinking

- **User Experience**: Interactive mode, rich output, clear feedback
- **Safety & Security**: Permission system, approval workflows
- **Developer Experience**: Easy extension, clear documentation
- **Maintainability**: Clean code, comprehensive comments, modular design

## Future Roadmap

Potential enhancements that demonstrate forward-thinking:

- [ ] **Async/Await Support**: Concurrent tool execution and streaming responses
- [ ] **Plugin System**: Load custom tools from external packages
- [ ] **Configuration Files**: YAML/TOML-based permission policies
- [ ] **Streaming Output**: Real-time token streaming for faster UX
- [ ] **Memory/Context Management**: Vector DB integration for long-term memory
- [ ] **Additional Providers**: Gemini, Cohere, local models (Ollama)
- [ ] **Web Interface**: Optional web UI alongside CLI
- [ ] **Team Features**: Shared contexts, collaboration tools
- [ ] **Testing Coverage**: Comprehensive unit and integration tests
- [ ] **CI/CD Pipeline**: Automated testing, building, and deployment

## Acknowledgments

Built with:

- [Anthropic Claude API](https://www.anthropic.com/) - Powerful LLM with excellent tool use
- [OpenAI API](https://openai.com/) - Industry-leading language models
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal formatting
- [Prompt Toolkit](https://python-prompt-toolkit.readthedocs.io/) - Interactive CLI framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation and settings management

---

**Note**: This is a portfolio project demonstrating software engineering best practices, architectural thinking, and clean code principles. It's built to be both functional for end-users and exemplary for code reviewers.
