# CLIppy 📎

A powerful CLI coding agent powered by Claude that helps you with software development tasks. CLIppy provides both interactive and one-shot modes with a robust permission system to keep you in control.

## Features

- **🤖 AI-Powered**: Uses Claude's advanced AI to understand and execute coding tasks
- **🔄 Two Modes**: Interactive REPL mode or one-shot command execution
- **🛡️ Permission System**: Fine-grained control over what actions can be auto-approved
- **🚫 Interrupt Anytime**: Press Ctrl+C to stop execution when something goes wrong
- **📝 Rich Output**: Beautiful terminal UI with syntax highlighting
- **🔧 Extensible**: Easy to customize permissions and add new tools

## Installation

### From PyPI (Recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install CLIppy
uv tool install clippy-ai

# Or use pipx
pipx install clippy-ai
```

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/clippy.git
cd clippy

# Install with uv
uv pip install -e .

# Or install with dev dependencies
uv pip install -e ".[dev]"
```

### Setup API Key

```bash
# Option 1: Create a .env file in the project directory
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env

# Option 2: Create a global config in your home directory
echo "ANTHROPIC_API_KEY=your_api_key_here" > ~/.clippy.env

# Option 3: Export as environment variable
export ANTHROPIC_API_KEY=your_api_key_here
```

Get your API key from [Anthropic Console](https://console.anthropic.com/)

## Usage

### One-Shot Mode

Execute a single task and exit:

```bash
# Simple task
clippy "create a hello world python script"

# More complex task
clippy "refactor the main.py file to use async/await"

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
- `/exit` or `/quit` - Exit CLIppy
- Press Ctrl+C during execution to interrupt

## Permission System

CLIppy has a built-in permission system to keep you safe:

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

When CLIppy wants to perform an action that requires approval, you'll see:

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

CLIppy has access to these tools:

| Tool | Description | Auto-Approved |
|------|-------------|---------------|
| `read_file` | Read file contents | ✅ |
| `write_file` | Write/modify files | ❌ |
| `delete_file` | Delete files | ❌ |
| `list_directory` | List directory contents | ✅ |
| `create_directory` | Create directories | ❌ |
| `execute_command` | Run shell commands | ❌ |
| `search_files` | Search with glob patterns | ✅ |
| `get_file_info` | Get file metadata | ✅ |

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

- `ANTHROPIC_API_KEY` - Your Anthropic API key (required)
- `CLIPPY_MODEL` - Model to use (default: claude-3-5-sonnet-20241022)
- `CLIPPY_MAX_TOKENS` - Max tokens for responses (default: 4096)

### Custom Permissions (Coming Soon)

You'll be able to customize permission levels via a config file.

## Development

### Project Structure

```
clippy/
├── src/
│   └── clippy/
│       ├── __init__.py
│       ├── __main__.py       # Entry point
│       ├── cli.py            # CLI interface
│       ├── agent.py          # AI agent logic
│       ├── tools.py          # Tool definitions
│       ├── executor.py       # Action executor
│       └── permissions.py    # Permission system
├── pyproject.toml            # Project config & dependencies
├── LICENSE                   # MIT License
└── README.md
```

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

### Code Quality

```bash
# Format code with ruff
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
uv run mypy src/clippy
```

### Running Tests

```bash
# Run tests with pytest
uv run pytest

# With coverage
uv run pytest --cov=clippy --cov-report=html
```

### Building and Publishing

```bash
# Build the package
uv build

# Publish to PyPI (requires credentials)
uv publish

# Or publish to TestPyPI first
uv publish --index-url https://test.pypi.org/simple/
```

## Safety Features

1. **Permission System**: Control what CLIppy can do automatically
2. **Approval Workflow**: Review and approve destructive actions
3. **Interrupt Handling**: Press Ctrl+C to stop execution at any time
4. **Conversation Reset**: Clear context with `/reset` in interactive mode
5. **Execution Timeout**: Commands timeout after 30 seconds

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

## Acknowledgments

Built with:
- [Anthropic Claude API](https://www.anthropic.com/)
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Prompt Toolkit](https://python-prompt-toolkit.readthedocs.io/) - Interactive CLI
