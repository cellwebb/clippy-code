# clippy-code Quick Start Guide

Get started with clippy-code in 5 minutes!

## 1. Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install clippy-code from PyPI
uv tool install clippy-code

# Or install from source
git clone https://github.com/yourusername/clippy.git
cd clippy
uv pip install -e .
```

## 2. Setup API Keys

For OpenAI (default provider):

```bash
echo "OPENAI_API_KEY=your_key_here" > .env
```

For other providers:

```bash
# Cerebras
echo "CEREBRAS_API_KEY=your_key_here" > .env

# Together AI
echo "TOGETHER_API_KEY=your_key_here" > .env

# Groq
echo "GROQ_API_KEY=your_key_here" > .env

# DeepSeek
echo "DEEPSEEK_API_KEY=your_key_here" > .env
```

For local models like Ollama, you typically don't need an API key:

```bash
# Just set the base URL in your environment or use the --base-url flag
export OPENAI_BASE_URL=http://localhost:11434/v1
```

### Optional: MCP Configuration

To use external tools via MCP (Model Context Protocol), create an `mcp.json` file:

```bash
# Create the clippy directory
mkdir -p ~/.clippy

# Copy the example configuration
cp mcp.example.json ~/.clippy/mcp.json

# Edit it with your API keys
# For example, to use Context7 for documentation retrieval:
# Set CTX7_API_KEY environment variable
```

## 3. First Command (One-Shot Mode)

```bash
clippy "create a hello world python script"
```

clippy-code will:

1. Show you what it plans to do
2. Ask for approval before writing files
3. Execute approved actions
4. Show you the results

## 4. Interactive Mode

```bash
clippy -i
```

Now you can have a conversation:

```
[You] ➜ create a simple calculator function

[clippy-code will think and respond...]

→ write_file
  path: calculator.py
  content: def add(a, b): ...

[?] Approve this action? [(y)es/(n)o/(a)llow]: yes

✓ Successfully wrote to calculator.py

[You] ➜ add tests for it

[clippy-code continues...]
```

## 5. Document Mode (Word-like Interface)

```bash
clippy -d
```

This mode provides a Textual-based UI with:

- A document area for conversations
- Toolbar buttons for common actions
- Visual status bar showing model/token info
- Approval dialogs with diff previews

## 6. Safety Controls

### Auto-Approved Actions

These run automatically without asking:

- Reading files
- Listing directories
- Searching for files
- Getting file info
- Reading multiple files
- Searching within files (grep)

### Requires Approval

You'll be asked before:

- Writing/modifying files
- Deleting files
- Creating directories
- Running shell commands
- Editing files line by line

### Approval Options

When prompted for approval, you can respond with:

- `(y)es` or `y` - Approve and execute the action
- `(n)o` or `n` - Reject and stop execution
- `(a)llow` or `a` - Approve and auto-approve this action type for the session
- Empty (just press Enter) - Reprompt for input

### Stopping Execution

- Type `(n)o` or `n` when asked for approval
- Press Ctrl+C during execution
- Use `/exit` to quit interactive mode

## 7. Common Usage Patterns

### Code Generation

```bash
clippy "create a REST API with Flask for user management"
```

### Code Review

```bash
clippy "review main.py and suggest improvements"
```

### Debugging

```bash
clippy "find the bug in utils.py causing the TypeError"
```

### Refactoring

```bash
clippy "refactor app.py to use dependency injection"
```

### Model Switching

During interactive sessions, switch models with:

```bash
/model list          # Show available models
/model groq          # Switch to Groq provider
/model deepseek      # Switch to DeepSeek provider
/model ollama        # Switch to Ollama (local) provider
```

## 8. Tips

1. **Be Specific**: The more context you provide, the better

   - Good: "create a Python function to validate email addresses using regex"
   - Better: "create a Python function to validate email addresses using regex, with type hints and docstrings"

2. **Review Before Approving**: Always check what clippy-code wants to do

   - Read the file path carefully
   - Review the content before approving writes

3. **Use Interactive Mode for Complex Tasks**:

   - Start with `clippy -i`
   - Build up context over multiple turns
   - Use `/reset` if you want to start fresh

4. **Auto-Approve for Safe Tasks** (use cautiously):

   ```bash
   clippy -y "read all Python files and create a summary"
   ```

5. **Use Document Mode for Better Visualization**:
   ```bash
   clippy -d  # Especially useful for longer coding sessions
   ```

## Troubleshooting

**Problem**: API key error
**Solution**: Make sure `.env` file exists with the appropriate API key (OPENAI_API_KEY, CEREBRAS_API_KEY, etc.)

**Problem**: clippy-code wants to modify the wrong file
**Solution**: Type `N` to reject, then provide more specific instructions

**Problem**: Execution seems stuck
**Solution**: Press Ctrl+C to interrupt, then try again with a simpler request

**Problem**: Want to use a local model
**Solution**: Ensure the service is running (e.g., Ollama) and set OPENAI_BASE_URL=http://localhost:11434/v1

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Experiment with different types of tasks
- Try different models and providers
- Customize permissions for your workflow
- Provide feedback to improve clippy-code!

Happy coding! 📎
