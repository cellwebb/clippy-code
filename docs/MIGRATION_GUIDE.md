# Migration Guide

Coming to clippy-code from other tools? This guide helps you transition smoothly.

## From Other AI Coding Assistants

### From GitHub Copilot

#### What's Different
- Interactive vs Inline: clippy-code is conversational, not just inline completion
- Full Project Scope: Can analyze entire codebases, not just current file
- Explicit Control: You approve every action before execution
- Multi-Provider: Works with any OpenAI-compatible model

#### Migration Steps

1. **Install clippy-code**:
   ```bash
   pip install clippy-code
   # or use without installation
   uvx clippy-code "initial test"
   ```

2. **API Key Setup**:
   ```bash
   # If you have OpenAI API key
   echo "OPENAI_API_KEY=your_key" > .env
   
   # Or try other providers
   echo "ANTHROPIC_API_KEY=your_key" > .env
   ```

3. **Basic Workflow Comparison**:
   
   | Copilot | clippy-code |
   |---------|-------------|
   | `// Generate function` | `clippy "generate a function that..."` |
   | Auto-complete | Interactive conversation |
   | Inline suggestions | Full file creation |
   | Limited context | Project-wide analysis |

#### Usage Examples

**Instead of**: Waiting for Copilot suggestions
```bash
# Copilot style - inline
def process_data(data):
    # <cursor waits for suggestion>
```

**Use clippy-code**:
```bash
clippy "Create a function processdata that validates input, handles errors, and returns structured results"

# Or in interactive mode
clippy
[You] ➜ create a process_data function with input validation and error handling
```

### From Cursor/Shadcn/ui

#### Key Differences
- Terminal-based: clippy-code runs in terminal, not VS Code extension
- Language Agnostic: Works with any programming language
- Customizable: Can use any model provider
- Safety-First: Built-in permission system

#### Migration Path

1. **Replace Inline Commands**:
   ```bash
   # Cursor style (in editor)
   # /fix: optimize this function
   
   # clippy-code style
   clippy "optimize this function for performance and readability"
   ```

2. **Project-Level Operations**:
   ```bash
   # Instead of file-by-file fixes
   clippy "Review entire codebase for performance bottlenecks"
   ```

3. **Batch Operations**:
   ```bash
   # Generate tests for all modules
   clippy "Create comprehensive test suite for the entire project"
   ```

### From Tabnine/CodeLlama

#### Advantages of clippy-code
- Full Conversations: Not just code completion
- File Operations: Can read, write, edit files
- Command Execution: Can run terminal commands
- Subagent System: Specialized AI agents

#### Transition Strategy

1. **Keep Using for Completion**: Tabnine can still handle basic completions
2. **Use clippy-code for Complex Tasks**:
   ```bash
   # Architecture decisions
   clippy "Analyze this codebase and suggest microservices migration"
   
   # Documentation
   clippy "Generate comprehensive API documentation"
   
   # Testing
   clippy "Create integration tests for the user authentication flow"
   ```

### From ChatGPT/Claude Web Interface

#### Key Benefits
- Direct File Access: No copy-pasting needed
- Context Awareness: Understands your project structure
- Execution: Actually runs the code it generates
- Tool Integration: Uses external tools and APIs

#### Quick Start

1. **Replace Copy-Paste Workflows**:
   ```bash
   # Instead of: Copy code to ChatGPT, get response, paste back
   clippy "Debug authentication issue in auth.py"
   ```

2. **Leverage File System**:
   ```bash
   # Analyze multiple files
   clippy "Review src/models/ and src/views/ for consistent error handling"
   ```

3. **Use Subagents**:
   ```bash
   # Specialized assistance
   clippy "delegate to code_review subagent: security audit"
   ```

## From Traditional Development Tools

### From IDE Features

#### Code Generation
```bash
# IDE template generator
clippy "Create a REST API template with FastAPI, including models, routes, and tests"

# IDE refactoring tools
clippy "Refactor this class to use dependency injection pattern"
```

#### Debugging
```bash
# Instead of debugger breakpoints
clippy "Find the bug causing TypeError in user_service.py"

# Instead of print debugging
clippy "Add comprehensive logging to the authentication flow"
```

### From Command-Line Tools

#### Replace Multiple Tools
```bash
# Instead of grep + sed + find
clippy "Find all TODO comments and convert to GitHub issues"

# Instead of manual file creation
clippy "Set up a complete Python project structure with proper packaging"
```

#### Enhanced Scripting
```bash
# Shell scripts + AI
clippy "Create a deployment script that handles backups, migrations, and health checks"
```

## Language-Specific Migration

### Python Developers

#### From Poetry/Pip
```bash
# Modern Python setup with uv
clippy "Convert this requirements.txt project to use pyproject.toml with uv"

# Package management
clippy "Set up proper Python packaging with entry points and CLI scripts"
```

#### From Django Management Commands
```bash
# Enhanced Django workflows
clippy "Create Django migration for new User Profile model with proper indices"
```

### JavaScript/Node.js Developers

#### From npm/yarn
```bash
# Modern JavaScript setup
clippy "Create a Node.js project with TypeScript, ESLint, Prettier, and Jest"

# Package.json management
clippy "Optimize package.json dependencies and add proper scripts"
```

#### From Create React App
```bash
# Custom React setup
clippy "Set up a modern React project with Vite, TypeScript, and Tailwind CSS"
```

### Rust Developers

#### From Cargo
```bash
# Rust project setup
clippy "Create a Rust library with proper error handling, tests, and documentation"

# Performance optimization
clippy "Optimize this Rust code for better memory usage and performance"
```

## Configuration Migration

### API Keys and Providers

```bash
# Multiple providers example
cat > .env << 'EOF'
# Primary provider
OPENAI_API_KEY=your_openai_key

# Backup providers
ANTHROPIC_API_KEY=your_anthropic_key
CEREBRAS_API_KEY=your_cerebras_key
GROQ_API_KEY=your_groq_key

# Local models
OLLAMA_BASE_URL=http://localhost:11434/v1
EOF
```

### Model Selection

```bash
# Save preferred configurations
clippy "/model add fast gpt-3.5-turbo --name 'quick'"
clippy "/model add balanced claude-3-sonnet --name 'coding'"
clippy "/model add powerful claude-3-opus --name 'analysis'"

# Use in workflows
clippy "/model quick; perform simple search"
clippy "/model coding; implement feature"
clippy "/model analysis; review architecture"
```

## Workflow Migration

### Development Workflow Comparison

| Traditional | clippy-code |
|-------------|-------------|
| Manual project setup | Automated scaffolding |
| Copy-paste from docs | Direct file creation |
| Manual testing | Auto-generated tests |
| Multiple tools | Single conversational interface |
| Context switching | Continuous conversation |

### Git Integration

```bash
# Replace manual Git workflows
clippy "Create a proper gitignore for this Python project"
clippy "Generate conventional commit messages for staged changes"
clippy "Review this pull request and suggest improvements"
```

### Testing Migration

```bash
# From manual test writing
clippy "Create comprehensive unit tests for all public methods in UserService"

# From manual test running
clippy "Run tests and fix any failing tests automatically"
```

## Advanced Migration Strategies

### Gradual Adoption

1. **Start Small**:
   ```bash
   # Basic tasks first
   clippy "Add type hints to this file"
   clippy "Generate documentation for this module"
   ```

2. **Expand Usage**:
   ```bash
   # Move to project-level tasks
   clippy "Review entire project for security issues"
   ```

3. **Full Integration**:
   ```bash
   # Complex workflows
   clippy "Set up CI/CD pipeline with GitHub Actions"
   ```

### Team Migration

#### Shared Configuration
```bash
# Team-wide settings
cat > .clippy-team.json << 'EOF'
{
  "default_model": "claude-3-sonnet",
  "code_review_model": "claude-3-opus",
  "testing_model": "gpt-4",
  "safety_level": "strict",
  "team_standards": {
    "require_tests": true,
    "require_docs": true,
    "code_style": "black,ruff"
  }
}
EOF
```

#### Team Workflows
```bash
# Code review process
clippy "delegate to code_review subagent: review PR #123 following team standards"

# Documentation
clippy "Update API docs for new endpoints following team template"
```

### CI/CD Integration

#### GitHub Actions Example
```yaml
name: clippy-code Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install clippy-code
        run: pip install clippy-code
      
      - name: Auto-review changes
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          clippy -y "Review changed files for issues and create PR comments"
```

## Troubleshooting Migration

### Common Issues

#### Performance Concerns
```bash
# If responses are slow
clippy --model groq:llama-3.1-8b "try faster model for simple tasks"

# If token usage is high
clippy "/compact 0.7"  # Reduce context
clippy --max-tokens 1000 "limit response length"
```

#### Permission Issues
```bash
# If actions are blocked
clippy "/status"  # Check permissions
clippy "/auto list"  # Review auto-approved actions

# For risky operations
clippy --yolo "action you're confident about"
```

#### Model Compatibility
```bash
# Try different providers
clippy --provider anthropic "test task"
clippy --provider cerebras "test task"
clippy --provider groq "test task"
```

### Getting Help

```bash
# Built-in help
clippy "/help"

# Check status
clippy "/status"

# Review logs
tail -f ~/.clippy/logs/clippy-*.log
```

## Learning Resources

### Documentation Path

1. **Start with**: [Quick Start Guide](QUICKSTART.md)
2. **Then explore**: [Visual Tutorial](docs/VISUAL_TUTORIAL.md)
3. **Advanced topics**: [Use Cases](docs/USE_CASES.md)
4. **Optimization**: [Performance Guide](docs/PERFORMANCE_GUIDE.md)

### Practice Projects

```bash
# Beginner project
clippy "Create a simple CLI tool with argparse and proper error handling"

# Intermediate project
clippy "Build a REST API with FastAPI, including tests and documentation"

# Advanced project
clippy "Set up a microservices architecture with Docker, testing, and CI/CD"
```

## Success Metrics

Track your migration success:

1. **Time to First Success**: How quickly you get useful results
2. **Task Completion Rate**: Percentage of tasks completed successfully
3. **Productivity Gain**: Time saved compared to previous workflow
4. **Code Quality**: Improvement in code quality and maintainability
5. **Team Adoption**: How quickly team members adopt the new workflow

By following this migration guide, you can smoothly transition to clippy-code and start enjoying its powerful features!