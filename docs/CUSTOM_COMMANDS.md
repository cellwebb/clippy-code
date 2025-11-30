# Custom Slash Commands

Clippy-code supports a powerful custom slash command system that allows you to define your own commands through configuration files. This feature enables you to create shortcuts for common tasks, integrate with external tools, and personalize your workflow.

## Quick Start

### Interactive Method (Recommended)

The easiest way to create and manage custom commands is using the interactive wizards:

1. **Create a new custom command:**
   ```
   /custom add
   ```
   Follow the prompts to select the command type, name, and configuration.

2. **Edit an existing command:**
   ```
   /custom edit <command-name>
   ```

3. **Delete a command:**
   ```
   /custom delete <command-name>
   ```

4. **List all commands:**
   ```
   /custom list
   ```

### Manual Method (Advanced Users)

For advanced users who prefer to edit JSON files directly:

1. **See an example configuration:**
   ```
   /custom example
   ```

2. **Edit the configuration file directly:**
   ```
   /custom config
   ```

3. **Reload your commands:**
   ```
   /custom reload
   ```

## Configuration File

Custom commands are defined in `~/.clippy/custom_commands.json`. The file uses the following structure:

```json
{
  "commands": {
    "command_name": {
      "type": "shell|text|template|function",
      "description": "Human-readable description",
      "options": "..."
    }
  }
}
```

## Project-Level vs Global Commands

Custom commands can be defined at two levels:

1. **Global commands** (`~/.clippy/custom_commands.json`): Available in all projects
2. **Project-level commands** (`./.clippy/custom_commands.json`): Available only in the current directory

When both exist, clippy-code merges them with **project commands taking precedence**. This allows you to:
- Share project-specific commands with your team (via git)
- Override global commands on a per-project basis
- Keep personal commands separate from team commands

**Example workflow:**
```bash
# Global command for personal use
~/.clippy/custom_commands.json:
{
  "commands": {
    "deploy": {
      "type": "shell",
      "description": "Deploy to my personal server",
      "command": "ssh myserver 'cd /app && git pull'"
    }
  }
}

# Project-level command (override)
./.clippy/custom_commands.json:
{
  "commands": {
    "deploy": {
      "type": "shell",
      "description": "Deploy to production",
      "command": "./scripts/deploy.sh {args}"
    }
  }
}
```

In this example, when you run `/deploy` in this project directory, it will use the project-specific deployment script instead of the global one.

## Command Types

### Shell Commands (`type: "shell"`)

Execute shell commands with optional argument substitution.

```json
{
  "git": {
    "type": "shell",
    "description": "Execute git commands safely",
    "command": "git {args}",
    "working_dir": ".",
    "timeout": 30,
    "dry_run": false,
    "dangerous": false
  }
}
```

**Options:**
- `command` (required): Shell command template. Use `{args}` for argument substitution
- `working_dir`: Directory to run the command in (default: current directory)
- `timeout`: Command timeout in seconds (default: 30)
- `dry_run`: Show command without executing (default: false)
- `dangerous`: Allow potentially dangerous commands (default: false)

**Usage:** `/git status`, `/git log --oneline -10`

### Text Commands (`type: "text"`)

Display static text with simple variable substitution.

```json
{
  "whoami": {
    "type": "text",
    "description": "Show current user and directory",
    "text": "👋 User: {user}\n📁 Directory: {cwd}",
    "formatted": true,
    "hidden": false
  }
}
```

**Options:**
- `text` (required): Text to display
- `formatted`: Enable Rich markup (default: true)
- `hidden`: Hide from command list (default: false)

**Available variables:** `{args}`, `{cwd}`, `{user}`

### Template Commands (`type: "template"`)

Display formatted text with extended variable support.

```json
{
  "todo": {
    "type": "template",
    "description": "Quick todo list template",
    "template": "📝 TODO List ({user} @ {cwd})\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{args}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
    "formatted": true
  }
}
```

**Options:**
- `template` (required): Text template
- `formatted`: Enable Rich markup (default: true)
- `hidden`: Hide from command list (default: false)

**Available variables:** `{args}`, `{cwd}`, `{user}`, `{model}`, `{provider}`, `{message_count}`

### Function Commands (`type: "function"`)

Call Python functions for complex behavior.

```json
{
  "stats": {
    "type": "function",
    "description": "Show session statistics",
    "function": "clippy.cli.custom_commands.show_session_stats"
  }
}
```

**Options:**
- `function` (required): Module.function to call
- `hidden`: Hide from command list (default: false)

Functions receive `args`, `agent`, and `console` parameters and should return a `CommandResult`.

## Management Commands

### `/custom add`
Interactive wizard to create a new custom command. Prompts you through:
- Choosing scope (project or global)
- Entering command name with validation
- Selecting command type (shell, text, template, function)
- Configuring type-specific options
- Setting description and visibility

### `/custom edit <command-name>`
Interactive wizard to edit an existing custom command. Loads current configuration as defaults and guides you through modifying any settings.

### `/custom delete <command-name>`
Delete a custom command with confirmation. If the command exists in multiple scopes (project and global), asks which one to delete.

### `/custom list`
List all configured custom commands with their details, type, and scope.

### `/custom reload`
Reload custom commands from the configuration files. Use this after manually editing configuration files.

### `/custom config [editor]`
Open the configuration file directly in your preferred editor (for advanced users).
- Uses `$EDITOR` or `$VISUAL` environment variable
- Defaults to `nano` if not set
- Alternative: `/custom config vim` or `/custom config code`

### `/custom example`
Display a comprehensive example configuration showing all command types.

### `/custom help`
Show help for custom command management.

## Security

### Dangerous Commands
By default, commands containing potentially dangerous operations are blocked:
- `rm`, `sudo`, `chmod`, `chown`, `dd`, `mkfs`, `format`

To allow dangerous commands, set `"dangerous": true` in the configuration:

```json
{
  "deploy": {
    "type": "shell",
    "description": "Deploy application",
    "command": "./deploy.sh {args}",
    "dangerous": true,
    "working_dir": ".",
    "timeout": 120
  }
}
```

### Best Practices
1. Use `dry_run: true` during development to see what would be executed
2. Set appropriate timeouts for long-running commands
3. Limit access to dangerous commands
4. Use absolute paths for critical commands
5. Validate input when calling Python functions

## Examples

### Development Workflow
```json
{
  "test": {
    "type": "shell",
    "description": "Run tests",
    "command": "pytest tests/ -v",
    "working_dir": "."
  },
  "lint": {
    "type": "shell", 
    "description": "Run linting",
    "command": "ruff check . && ruff format .",
    "working_dir": "."
  },
  "build": {
    "type": "shell",
    "description": "Build the project",
    "command": "python -m build",
    "working_dir": "."
  }
}
```

### Productivity Tools
```json
{
  "meeting": {
    "type": "template",
    "description": "Create meeting notes template",
    "template": "📋 Meeting Notes ({user} - {cwd})\n\n📅 Date: {args}\n\n🎯 Agenda:\n- \n\n💬 Discussion:\n\n✅ Action Items:\n- \n\n📝 Notes:\n"
  },
  "link": {
    "type": "text",
    "description": "Show current session URL",
    "text": "🔗 Current session: https://github.com/project/issues/{args}",
    "formatted": true
  }
}
```

### System Information
```json
{
  "sysinfo": {
    "type": "shell",
    "description": "Show system information",
    "command": "uname -a && df -h && free -h",
    "dry_run": false
  },
  "env": {
    "type": "shell",
    "description": "Show environment variables",
    "command": "env | grep -E '^USER|^HOME|^PATH|^PWD' | sort",
    "dry_run": false
  }
}
```

## Advanced Usage

### Custom Functions
Create your own Python functions in a module and reference them:

```python
# ~/.clippy/my_functions.py
def project_tasks(args: str, agent, console) -> str:
    """Custom function to show project tasks."""
    # Your custom logic here
    console.print("🎯 Project Tasks:")
    console.print("- Review documentation")
    console.print("- Write tests") 
    console.print("- Deploy changes")
    return "continue"
```

```json
{
  "tasks": {
    "type": "function",
    "description": "Show project tasks",
    "function": "my_functions.project_tasks"
  }
}
```

### Conditional Commands
Use shell scripts for conditional logic:

```json
{
  "deploy": {
    "type": "shell",
    "description": "Deploy if tests pass",
    "command": "if pytest; then deploy.sh {args}; else echo 'Tests failed'; fi",
    "working_dir": ".",
    "timeout": 300
  }
}
```

## Troubleshooting

### Command Not Found
1. Check spelling: `/help` to see available commands
2. Reload commands: `/custom reload`
3. Verify configuration: `/custom list`

### Permission Denied
1. Check file permissions on the configuration
2. Ensure shells scripts are executable
3. Verify working directory exists

### Commands Not Applied
1. Reload after editing: `/custom reload`
2. Check JSON syntax: `python -m json.tool ~/.clippy/custom_commands.json`
3. Verify command type and required options

## Integration with Other Tools

Custom commands work seamlessly with:
- **MCP Servers**: Use custom commands to quickly access MCP tools
- **Subagents**: Create commands that delegate to specialized subagents  
- **Models**: Switch models based on the task using custom commands
- **File Operations**: Create shortcuts for common file operations

Examples:
```json
{
  "clean": {
    "type": "shell", 
    "description": "Clean up temporary files",
    "command": "find . -name '*.pyc' -delete && find . -name '__pycache__' -type d -delete"
  },
  "switch-agent": {
    "type": "function",
    "description": "Switch to specialized agent",
    "function": "my_utils.switch_to_agent"
  }
}
```

This custom command system makes clippy-code infinitely extensible, allowing you to create your ideal AI assistant workflow! 🚀
