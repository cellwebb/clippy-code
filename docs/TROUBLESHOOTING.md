# clippy-code Troubleshooting Guide

Common issues, solutions, and debugging tips for clippy-code.

## 🔧 Quick Fixes

### Installation Issues

**Problem**: `uvx clippy-code` fails with "command not found"
```bash
# Solution: Install uv first
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or use pip installation
pip install clippy-code
```

**Problem**: Permission errors during installation
```bash
# Solution: Use user installation
pip install --user clippy-code

# Or use uvx which handles permissions automatically
uvx clippy-code --help
```

### API Key Issues

**Problem**: "API key not found" or authentication errors
```bash
# Check if .env file exists
ls -la .env

# Create .env file with appropriate key
echo "OPENAI_API_KEY=your_key_here" > .env

# Verify key is loaded
env | grep API_KEY
```

**Problem**: API key works in curl but not clippy-code
```bash
# Check for extra spaces or special characters
cat .env | tr -d '\n' | hexdump -C

# Recreate .env file cleanly
echo "OPENAI_API_KEY=clean_key_here" > .env
```

### Provider-Specific Issues

**OpenAI**:
```bash
# Verify key works
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# Check rate limits
echo "Current rate limits are visible in OpenAI dashboard"
```

**Anthropic**:
```bash
# Test key
curl -H "x-api-key: $ANTHROPIC_API_KEY" https://api.anthropic.com/v1/messages

# Note: Anthropic has stricter content policies
```

**Cerebras**:
```bash
# Test key
curl -H "Authorization: Bearer $CEREBRAS_API_KEY" https://api.cerebras.ai/v1/models

# Cerebras is great for code generation tasks
```

### Local Model Issues

**Problem**: Ollama connection refused
```bash
# Check if Ollama is running
ollama list

# Start Ollama if not running
ollama serve

# Test connection with curls
curl http://localhost:11434/api/tags

# Configure clippy-code
export OPENAI_BASE_URL=http://localhost:11434/v1
clippy --model ollama "test message"
```

**Problem**: LM Studio connection issues
```bash
# Check LM Studio server settings
# Ensure 'Server Mode' is enabled
# Note the port number (usually 1234)

# Configure clippy-code
export OPENAI_BASE_URL=http://localhost:1234/v1
clippy --model your-model-name "test message"
```

---

## 🚨 Runtime Issues

### Permission Denied Errors

**Problem**: "Permission denied" for file operations
```bash
# Check file permissions
ls -la /path/to/target/file

# Fix permissions if needed
chmod 644 target_file.py
chmod 755 target_directory/

# Or run from appropriate directory
cd /path/to/writable/directory
clippy "create files here"
```

**Problem**: Can't write to system directories
```bash
# clippy-code prevents writes to system directories for safety
# Instead:
clippy "create files in current directory or subdirectories"

# For system-wide installation:
sudo pip install clippy-code  # Not recommended
```

### Timeout Issues

**Problem**: Operations timing out
```bash
# Increase timeout
export CLIPPY_COMMAND_TIMEOUT=600
clippy "long-running operation"

# Or use timeout flag
clippy --timeout 600 "compile and test project"
```

**Problem**: Model responses are slow
```bash
# Try a faster model
clippy --model gpt-3.5-turbo "simple task"

# Or use fast_general subagent
clippy "delegate to fast_general subagent: quick search and summary"
```

### Memory Issues

**Problem**: Out of memory responses
```bash
# Reduce context length
clippy --max-tokens 1000 "task with limited response"

# Break into smaller tasks
clippy "step 1: analyze file structure"
clippy "step 2: review main components"
```

### Network Issues

**Problem**: Connection timeouts or SSL errors
```bash
# Test connectivity
curl -I https://api.openai.com/v1/models

# Check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY

# Disable SSL verification (not recommended for production)
export PYTHONHTTPSVERIFY=0
clippy "test message"
```

---

## 🤖 Subagent Issues

### Subagent Timeouts

**Problem**: Subagents take too long
```bash
# Increase global subagent timeout
export CLIPPY_SUBAGENT_TIMEOUT=900

# Or specify per-subagent timeout
clippy "delegate to subagent with timeout=600: complex task"
```

**Problem**: Too many concurrent subagents
```bash
# Reduce concurrency
export CLIPPY_MAX_CONCURRENT_SUBAGENTS=2

# Or run sequentially
clippy "run subagents sequentially: task1, task2, task3"
```

### Subagent Permissions

**Problem**: Subagent can't access required tools
```bash
# Check subagent type permissions
clippy "/subagent list"

# Use general subagent for full access
clippy "delegate to general subagent: needs write permissions"
```

---

## 🔍 Debugging Tools

### Enable Debug Logging

```bash
# Enable verbose output
clippy -v "task with debugging info"

# Enable debug logging
export CLIPPY_LOG_LEVEL=DEBUG
clippy "task"

# View logs in real-time
tail -f ~/.clippy/logs/clippy-*.log
```

### Check Configuration

```bash
# List available models
clippy "/model list"

# Check model configuration
clippy "/status"

# List MCP servers
clippy "/mcp list"

# Check subagent configuration
clippy "/subagent list"
```

### Test Individual Components

```bash
# Test file operations
clippy "read README.md"

# Test command execution
clippy "echo 'test command works'"

# Test model connection
clippy "say hello"

# Test subagent delegation
clippy "delegate to fast_general subagent: quick test"
```

---

## 💻 Environment-Specific Issues

### Windows

**Problem**: Path separator issues
```bash
# clippy-code handles paths automatically
# If issues persist, try forward slashes
clippy "create file at ./src/module.py"

# Or use PowerShell properly
cd .; clippy "create file in current directory"
```

**Problem**: Command not found in PowerShell
```bash
# Add to PATH manually
$env:PATH += ";C:\Users\$env:USERNAME\.local\bin"

# Or use full path
python -m clippy "test command"
```

### macOS

**Problem**: Python version conflicts
```bash
# Use python3 explicitly
python3 -m pip install clippy-code
python3 -m clippy "test command"

# Or use uv which handles versions
uvx clippy-code "test command"
```

**Problem**: Permissions on macOS Catalina+
```bash
# Allow app execution
xattr -d com.apple.quarantine $(which clippy-code)

# Or use uvx which avoids this issue
uvx clippy-code "test command"
```

### Linux

**Problem**: Package manager conflicts
```bash
# Use virtual environment
python3 -m venv clippy-env
source clippy-env/bin/activate
pip install clippy-code

# Or use uv for isolation
uvx clippy-code "test command"
```

---

## 🐛 Common Error Messages

### "No API key configured"

**Cause**: Missing or incorrect API key setup
```bash
# Fix: Set appropriate environment variable
echo "PROVIDER_API_KEY=your_key" > .env

# List of providers
# OPENAI_API_KEY, ANTHROPIC_API_KEY, CEREBRAS_API_KEY
# GROQ_API_KEY, MISTRAL_API_KEY, TOGETHER_API_KEY
```

### "Model not found"

**Cause**: Incorrect model name or provider
```bash
# Fix: Check available models
clippy "/model list"

# Use correct format
clippy --model openai:gpt-4 "task"
clippy --model anthropic:claude-3-sonnet "task"
```

### "Permission denied"

**Cause**: Trying to access restricted files or directories
```bash
# Fix: Work in appropriate directory
cd /path/to/project
clippy "create files here"

# Check permissions
ls -la
```

### "Command blocked by safety agent"

**Cause**: Dangerous command detected
```bash
# Fix: Use safer approach
clippy "list files instead of rm -rf"
clippy "create backup instead of direct modification"

# Or disable safety (not recommended)
clippy --yolo "dangerous command"
```

### "Subagent execution failed"

**Cause**: Subagent error or timeout
```bash
# Fix: Increase timeout or simplify task
export CLIPPY_SUBAGENT_TIMEOUT=900
clippy "delegate to subagent: simpler task"

# Check logs for details
tail -100 ~/.clippy/logs/clippy-*.log
```

---

## 🔄 Recovery Procedures

### Reset Configuration

```bash
# Reset model configuration
clippy "/model reset"

# Reset subagent configuration
clippy "/subagent reset"

# Clear MCP configuration
rm ~/.clippy/mcp.json

# Reset all (careful!)
rm -rf ~/.clippy/
```

### Clear Cache

```bash
# Clear safety cache
rm -rf ~/.clippy/safety_cache/

# Clear subagent cache
clypy "/subagent clear-cache"

# Clear all caches
rm -rf ~/.clippy/cache/
```

### Restart Sessions

```bash
# Clear conversation history
clippy "/reset"

# Start fresh session
clippy

# Or run one-shot command
uvx clippy-code "fresh start task"
```

---

## 📞 Getting Help

### Community Support

1. **GitHub Issues**: Report bugs at https://github.com/cellwebb/clippy-code/issues
2. **Discussions**: Ask questions in GitHub Discussions
3. **Documentation**: Check docs/ directory for detailed guides

### Self-Service Debugging

1. **Check logs**: `tail -f ~/.clippy/logs/clippy-*.log`
2. **Verify configuration**: `clippy "/status"`
3. **Test connectivity**: Use curl commands above
4. **Try minimal case**: `clippy "say hello"`

### When Reporting Issues

Include this information:
```bash
# System info
python --version
clippy --version
uname -a

# Configuration
echo "API Keys: $OPENAI_API_KEY $ANTHROPIC_API_KEY"
clippy "/status"

# Error details
export CLIPPY_LOG_LEVEL=DEBUG
clippy "reproduce issue"

# Logs
tail -200 ~/.clippy/logs/clippy-*.log
```

---

## 🎯 Prevention Tips

### Best Practices

1. **Always test with simple commands first**
2. **Use appropriate models for task complexity**
3. **Review commands before approving**
4. **Keep API keys secure and separate**
5. **Use virtual environments**
6. **Regular updates**: `pip install -U clippy-code`

### Environment Setup

```bash
# Recommended .env file structure
cat > .env << 'EOF'
# API Keys (one or more)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# clippy-code Settings
CLIPPY_LOG_LEVEL=INFO
CLIPPY_SHOW_COMMAND_OUTPUT=false
CLIPPY_COMMAND_TIMEOUT=300

# Optional: Model preferences
DEFAULT_MODEL=openai:gpt-4
EOF
```

### Regular Maintenance

```bash
# Update clippy-code
pip install -U clippy-code

# Clear old logs
find ~/.clippy/logs/ -name "*.log" -mtime +7 -delete

# Clean cache occasionally
rm -rf ~/.clippy/cache/*
```

---

## 🆘 Emergency Procedures

### If Everything Fails

1. **Use uvx** to bypass any installation issues:
   ```bash
   uvx clippy-code --help
   ```

2. **Try different provider**:
   ```bash
   clippy --model cerebras:llama-3.1-70b "test"
   ```

3. **Minimal reproduction**:
   ```bash
   clippy "echo 'minimal test'"
   ```

4. **Fresh installation**:
   ```bash
   pip uninstall clippy-code
   pip install clippy-code
   ```

### Emergency Commands

```bash
# Force reset all settings
rm -rf ~/.clippy/

# Test with no configuration
clippy --help

# Use system python as fallback
/usr/bin/python3 -m pip install clippy-code
/usr/bin/python3 -m clippy "emergency test"
```

Remember: Most issues are related to API keys, network connectivity, or permissions. Start with those basics before diving into complex debugging! 🚀