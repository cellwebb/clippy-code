# clippy-code Quick Start Guide

Get started with clippy-code in 5 minutes!

## 1. Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install from PyPI
pip install clippy-code

# Or run directly without installation (recommended)
uvx clippy-code "create a hello world python script"

# Or install from source
git clone https://github.com/cellwebb/clippy-code.git
cd clippy-code
uv pip install -e .
```

## 2. Setup API Keys

clippy-code supports many LLM providers through OpenAI-compatible APIs:

```bash
# OpenAI (default)
echo "OPENAI_API_KEY=your_key_here" > .env

# Or choose from many supported providers:
echo "ANTHROPIC_API_KEY=your_key_here" > .env
echo "CEREBRAS_API_KEY=your_key_here" > .env
echo "CHUTES_API_KEY=your_key_here" > .env
echo "GOOGLE_API_KEY=your_key_here" > .env
echo "GROQ_API_KEY=your_key_here" > .env
echo "MINIMAX_API_KEY=your_key_here" > .env
echo "MISTRAL_API_KEY=your_key_here" > .env
echo "OPENROUTER_API_KEY=your_key_here" > .env
echo "SYNTHETIC_API_KEY=your_key_here" > .env
echo "TOGETHER_API_KEY=your_key_here" > .env
echo "ZAI_API_KEY=your_key_here" > .env
echo "CLAUDE_CODE_ACCESS_TOKEN=your_token_here" > .env  # Claude Code OAuth
```

For local models like Ollama or LM Studio, you typically don't need an API key:

```bash
# Just set the base URL in your environment or use the --base-url flag
export OPENAI_BASE_URL=http://localhost:11434/v1
```

### Optional: MCP Configuration

To use external tools via MCP (Model Context Protocol), create an `mcp.json` file:

```bash
# Create the clippy directory
mkdir -p ~/.clippy

# Copy the example configuration (if you have the source)
cp mcp.example.json ~/.clippy/mcp.json

# Or create it manually with a basic setup
cat > ~/.clippy/mcp.json << 'EOF'
{
  "mcp_servers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp", "--api-key", "${CTX7_API_KEY}"]
    }
  }
}
EOF

# Set environment variables for any MCP servers
echo "CTX7_API_KEY=your_context7_key_here" >> .env
```

Then use `/mcp list` in interactive mode to see available servers and tools.

## 3. First Command (One-Shot Mode)

```bash
# If installed via pip
clippy "create a hello world python script"

# Or run directly without installation
uvx clippy-code "create a hello world python script"
```

clippy-code will:

1. Show you what it plans to do
2. Ask for approval before writing files
3. Execute approved actions
4. Show you the results

## 4. Interactive Mode

```bash
# If installed via pip
clippy

# Or run directly without installation  
uvx clippy-code
```

Interactive mode provides a rich conversational experience with advanced features:

- Tab completion for commands and file paths
- Command history with up/down arrows
- Double-ESC to interrupt execution
- Slash commands for model switching and configuration
- Real-time streaming responses

Here's how a typical interactive session looks:

```
[You] ➜ create a simple calculator function

[clippy-code will think and respond...]

→ write_file
  path: calculator.py
  content: def add(a, b): ...

[?] Approve this action? [(y)es/(n)o/(a)llow]: y

✅ Successfully wrote to calculator.py

[You] ➜ add tests for it

[clippy-code continues with test generation...]
```

### Key Interactive Features

1. **Smart Completion**: Tab completion works for:

   - File paths and directory names
   - Slash commands and their arguments
   - Model names and provider names

2. **Command History**: Use up/down arrows to navigate previous commands

3. **Interruption Control**:

   - Single ESC: Shows you're thinking
   - Double ESC: Immediately stops current execution
   - Ctrl+C: Also interrupts execution

4. **Rich Slash Commands**: Full set of commands for:

   - Model management (`/model list`, `/model add`, etc.)
   - Permission control (`/auto list`, `/auto revoke`)
   - MCP server management (`/mcp list`, `/mcp tools`)
   - Session control (`/status`, `/compact`, `/reset`)
   - Subagent configuration (`/subagent list`, `/subagent set`)

5. **Real-time Feedback**: See responses as they're being generated, not just at the end

## 5. Safety Controls

### Auto-Approved Actions

These run automatically without asking:

- `read_file` - Read file contents
- `list_directory` - List directory contents  
- `search_files` - Search with glob patterns
- `get_file_info` - Get file metadata
- `read_files` - Read multiple files at once
- `grep` - Search patterns in files

### Requires Approval

You'll be asked before:

- `write_file` - Write files with syntax validation
- `delete_file` - Delete files
- `create_directory` - Create directories
- `execute_command` - Run shell commands
- `edit_file` - Edit files by line (insert/replace/delete/append)
- `delegate_to_subagent` - Create specialized subagents
- `run_parallel_subagents` - Run multiple subagents concurrently

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

## 6. Common Usage Patterns

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
/model use cerebras qwen-3-coder-480b  # Try a model without saving
/model add cerebras qwen-3-coder-480b --name "q3c"  # Save a model configuration
/model q3c           # Switch to a saved model
/model ollama        # Switch to Ollama (local) provider
```

### Provider Management

You can also add custom providers:

```bash
/provider list       # Show all available providers
/provider add        # Add a new custom provider
/provider remove     # Remove a custom provider
```

## 7. Tips

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

5. **Extra Command Line Options**:

   You can use additional flags for more control:

   ```bash
   # Verbose logging with retry information
   clippy -v "debug this issue"

   # Specify a custom base URL for providers
   clippy --base-url https://api.custom-provider.com/v1 "write code"

   # YOLO mode - auto-approve everything without prompts (use with extreme caution!)
   clippy --yolo "delete all log files"
   ```

6. **Use uvx for Easier Testing**:
   ```bash
   uvx clippy-code --model groq "debug this function"
   ```

## Troubleshooting

**Problem**: API key error
**Solution**: Make sure `.env` file exists with the appropriate API key. Each provider has its own environment variable:
- `OPENAI_API_KEY` for OpenAI
- `ANTHROPIC_API_KEY` for Claude
- `CEREBRAS_API_KEY` for Cerebras
- `CHUTES_API_KEY` for Chutes.ai
- `GOOGLE_API_KEY` for Gemini
- `GROQ_API_KEY` for Groq
- `MINIMAX_API_KEY` for MiniMax
- `MISTRAL_API_KEY` for Mistral
- `OPENROUTER_API_KEY` for OpenRouter
- `SYNTHETIC_API_KEY` for Synthetic.new
- `TOGETHER_API_KEY` for Together AI
- `ZAI_API_KEY` for Z.AI
- `CLAUDE_CODE_ACCESS_TOKEN` for Claude Code OAuth
- And many more!

**Problem**: clippy-code wants to modify the wrong file
**Solution**: Type `n` to reject, then provide more specific instructions

**Problem**: Execution seems stuck
**Solution**: Press Ctrl+C to interrupt, double-ESC to stop immediately, then try again with a simpler request

**Problem**: Want to use a local model
**Solution**: Ensure the service is running (e.g., Ollama) and set:
```bash
export OPENAI_BASE_URL=http://localhost:11434/v1
clippy --model ollama
```

**Problem**: Installation issues
**Solution**: Try using `uvx` to run without installation:
```bash
uvx clippy-code "your command here"
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out [CONTRIBUTING.md](CONTRIBUTING.md) if you want to contribute
- Set up [MCP integration](docs/MCP.md) for external tools
- Experiment with different models and providers
- Try the `/subagent` commands for specialized tasks
- Customize permissions for your workflow
- Provide feedback to improve clippy-code!

Happy coding! 📎
