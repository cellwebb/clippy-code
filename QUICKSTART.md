# code-with-clippy Quick Start Guide

Get started with code-with-clippy in 5 minutes!

## 1. Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install code-with-clippy from PyPI
uv tool install code-with-clippy

# Or install from source
git clone https://github.com/yourusername/clippy.git
cd clippy
uv pip install -e .

# Set up your API key
echo "OPENAI_API_KEY=your_key_here" > .env
```

## 2. First Command (One-Shot Mode)

```bash
clippy "create a hello world python script"
```

code-with-clippy will:

1. Show you what it plans to do
2. Ask for approval before writing files
3. Execute approved actions
4. Show you the results

## 3. Interactive Mode

```bash
clippy -i
```

Now you can have a conversation:

```
[You] ➜ create a simple calculator function

[code-with-clippy will think and respond...]

→ write_file
  path: calculator.py
  content: def add(a, b): ...

[?] Approve this action? [y/N/stop]: y

✓ Successfully wrote to calculator.py

[You] ➜ add tests for it

[code-with-clippy continues...]
```

## 4. Safety Controls

### Auto-Approved Actions

These run automatically without asking:

- Reading files
- Listing directories
- Searching for files
- Getting file info

### Requires Approval

You'll be asked before:

- Writing/modifying files
- Deleting files
- Creating directories
- Running shell commands

### Stopping Execution

- Type `stop` when asked for approval
- Press Ctrl+C during execution
- Use `/exit` to quit interactive mode

## 5. Common Usage Patterns

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

## 6. Tips

1. **Be Specific**: The more context you provide, the better

   - Good: "create a Python function to validate email addresses using regex"
   - Better: "create a Python function to validate email addresses using regex, with type hints and docstrings"

2. **Review Before Approving**: Always check what code-with-clippy wants to do

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

## Troubleshooting

**Problem**: API key error
**Solution**: Make sure `.env` file exists with `OPENAI_API_KEY=...`

**Problem**: code-with-clippy wants to modify the wrong file
**Solution**: Type `N` to reject, then provide more specific instructions

**Problem**: Execution seems stuck
**Solution**: Press Ctrl+C to interrupt, then try again with a simpler request

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Experiment with different types of tasks
- Customize permissions for your workflow
- Provide feedback to improve code-with-clippy!

Happy coding! 📎
