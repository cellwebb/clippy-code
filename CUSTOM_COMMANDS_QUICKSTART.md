# 📎 Custom Slash Commands - Quick Start Guide

Welcome to your incredibly powerful custom slash command system! This feature lets you create personal shortcuts, integrate external tools, and automate your workflow.

## 🚀 Get Started in 3 Minutes

### 1. See What's Possible
```bash
/custom example
```

### 2. Create Your First Command
```bash
/custom edit
```
Add this to your config:
```json
{
  "commands": {
    "hello": {
      "type": "text",
      "description": "Say hello with style",
      "text": "👋 Hello {user}! Welcome to {cwd}"
    }
  }
}
```

### 3. Use Your Command!
```bash
/hello
```

## 🎯 Popular Command Ideas

### 📝 Productivity Commands
```json
{
  "todo": {
    "type": "template",
    "description": "Quick todo list",
    "template": "📝 TODO ({user} @ {cwd})\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{args}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  },
  "note": {
    "type": "template", 
    "description": "Quick note taking",
    "template": "📓 Note ({user}): {args}\n📍 {cwd}\n⏰ {model} session"
  }
}
```

### 🔧 Development Commands
```json
{
  "test": {
    "type": "shell",
    "description": "Run project tests", 
    "command": "pytest tests/ -v",
    "dry_run": false
  },
  "lint": {
    "type": "shell",
    "description": "Check and format code",
    "command": "ruff check . && ruff format ."
  }
}
```

### 📊 System Commands
```json
{
  "stats": {
    "type": "function",
    "description": "Show session statistics", 
    "function": "clippy.cli.custom_commands.show_session_stats"
  },
  "whoami": {
    "type": "text",
    "description": "Show current context",
    "text": "👋 User: {user}\n📁 Directory: {cwd}\n🤖 Model: {model}"
  }
}
```

## 🛠️ Command Types Explained

### Shell Commands (`type: "shell"`)
Execute shell commands safely with argument substitution.
```json
{
  "git": {
    "type": "shell",
    "command": "git {args}",
    "dry_run": false,      // Set true to preview without executing
    "timeout": 30,        // Command timeout in seconds
    "dangerous": false    // Allow dangerous operations
  }
}
```

### Text Commands (`type: "text"`)  
Display static text with basic variables.
```json
{
  "welcome": {
    "type": "text",
    "text": "Welcome {user}! Your current directory is {cwd}",
    "formatted": true     // Enable rich text formatting
  }
}
```

### Template Commands (`type: "template"`)
Advanced templating with more variables.
```json
{
  "report": {
    "type": "template", 
    "template": "Report by {user} using {model} with {message_count} messages",
    "formatted": true
  }
}
```

### Function Commands (`type: "function"`)
Call Python functions for complex behavior.
```json
{
  "deploy": {
    "type": "function",
    "function": "my_tools.deploy_function"
  }
}
```

## 📋 Command Management

### List All Commands
```bash
/custom list
```

### Edit Configuration
```bash
/custom edit           # Opens in your default editor
/custom edit vim       # Use specific editor
```

### Reload Changes
```bash
/custom reload
```

### Show Help
```bash
/custom help
```

## ✨ Advanced Features

### Security Features
- Dangerous commands (rm, sudo, etc.) are blocked by default
- Set `"dangerous": true` to enable specific commands
- Use `"dry_run": true` to preview commands

### Variable Substitution
Available variables in templates:
- `{args}` - Command arguments
- `{user}` - Current username
- `{cwd}` - Current working directory
- `{model}` - Current AI model
- `{provider}` - Current provider
- `{message_count}` - Number of messages

### Rich Formatting
Enable beautiful output with colors and styling:
```json
{
  "colorful": {
    "type": "text",
    "text": "[bold green]Success![/bold green] Task completed.",
    "formatted": true
  }
}
```

## 🎪 Real Examples

### Project Bootstrap
```bash
/bootstrap my-new-project
```
```json
{
  "bootstrap": {
    "type": "shell",
    "description": "Create new project structure",
    "command": "mkdir {args} && cd {args} && npm init -y && mkdir src tests docs",
    "dangerous": false
  }
}
```

### Quick API Testing
```bash
/api-test GET https://api.example.com/users
```
```json
{
  "api-test": {
    "type": "shell", 
    "description": "Quick API request testing",
    "command": "curl -X {args} -w '\\n\\nHTTP Status: %{http_code}\\nTime: %{time_total}s\\n'",
    "timeout": 10
  }
}
```

### Daily Standup Notes
```bash
/standup Working on user authentication, fixed login bug, need to review PRs
```
```json
{
  "standup": {
    "type": "template",
    "description": "Daily standup notes format",
    "template": "📋 Daily Standup ({user}) - {model}\\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n✅ Yesterday: {args}\\n🎯 Today: \\n🚧 Blockers: \\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  }
}
```

## 🎉 Integration with clippy-code

Custom commands work seamlessly with all clippy-code features:

- **MCP Servers**: Create shortcuts to access specific MCP tools
- **Subagents**: Commands that delegate to specialized agents
- **Models**: Quick model switching for different tasks  
- **File Operations**: Streamlined file management
- **Project Management**: Commands for your specific workflows

## Get Creative! 💡

Here are some ideas to inspire you:

### Fun Commands
```json
{
  "fortune": {
    "type": "shell",
    "command": "echo 'You will have a great coding session! 🚀'"
  },
  "coffee": {
    "type": "text", 
    "text": "☕ Time for a coffee break, {user}! You've earned it."
  }
}
```

### Learning Tools
```json
{
  "learn": {
    "type": "template",
    "template": "📚 Learning Topic: {args}\\n\\n🔗 Resources:\\n• Documentation\\n• Examples\\n• Tutorials\\n\\n📝 Notes:"
  }
}
```

### Automation Helpers
```json
{
  "backup": {
    "type": "shell",
    "command": "cp -r src backup_$(date +%Y%m%d_%H%M%S) && echo '✅ Backup completed!'"
  }
}
```

## 🛡️ Best Practices

1. **Start Simple**: Begin with text commands, then expand
2. **Use Dry Run**: Test shell commands with `"dry_run": true` first
3. **Secure Commands**: Only enable `"dangerous": true` when necessary
4. **Clear Naming**: Use descriptive command names
5. **Good Descriptions**: Helpful descriptions appear in `/help`
6. **Test Thoroughly**: Use `/custom reload` after changes

---

🎊 **Congratulations!** You now have an incredibly flexible command system that can adapt to your exact workflow. The possibilities are endless – start creating your perfect AI assistant experience today!

**Remember**: Edit `~/.clippy/custom_commands.json` and run `/custom reload` to apply changes. Happy customizing! 📎✨