# Advanced Configuration Guide

Deep dive into customizing clippy-code for optimal performance and specific workflows.

## 🎛️ Configuration Overview

### Configuration Precedence

clippy-code uses a layered configuration system:

1. **Command-line flags** (highest priority)
2. **Environment variables**
3. **Configuration files** (`~/.clippy/`)
4. **Default values** (lowest priority)

### Configuration Locations

```
~/.clippy/
├── config.json           # Main configuration
├── models.json           # Saved model configurations
├── mcp.json              # MCP server configuration
├── subagent_config.json  # Subagent model overrides
├── logs/                 # Session logs
├── cache/                # Cached results
└── safety_cache/         # Command safety cache
```

## 🤖 Model Configuration

### Provider Configuration

clippy-code supports any OpenAI-compatible provider. Configure with environment variables or custom providers:

#### Built-in Providers

```bash
# OpenAI (default)
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://api.openai.com/v1

# Anthropic Claude
export ANTHROPIC_API_KEY=sk-ant-...

# Cerebras
export CEREBRAS_API_KEY=...

# Together AI
export TOGETHER_API_KEY=...

# Groq
export GROQ_API_KEY=...

# Mistral
export MISTRAL_API_KEY=...

# Google Gemini
export GOOGLE_API_KEY=...

# And many more...
```

#### Custom Providers

```bash
# Add custom provider
clippy "/provider add"

# Example: Local Ollama
# Base URL: http://localhost:11434/v1
# API Key: (not required for local models)
```

### Model Optimization

#### Performance vs Quality Trade-offs

```bash
# Fastest (for simple tasks)
clippy --model gpt-3.5-turbo "simple file search"

# Balanced (good for coding)
clippy --model groq:llama-3.1-70b "code refactoring"

# Highest quality (for complex analysis)
clippy --model claude-3-opus-20240229 "architecture review"

# Cost-effective (large tasks)
clippy --model cerebras:llama-3.1-70b "bulk processing"
```

#### Model Selection by Task Type

| Task Type | Recommended Models | Notes |
|-----------|-------------------|-------|
| **Simple queries** | gpt-3.5-turbo, groq:llama-3.1-8b | Fast, cheap |
| **Code generation** | gpt-4, claude-3-sonnet, cerebras:llama-3.1-70b | Good balance |
| **Complex analysis** | claude-3-opus, gpt-4-turbo | Highest quality |
| **Large processing** | cerebras:llama-3.1-70b, together:mixtral | Cost effective |
| **Local processing** | ollama:codellama, lm-studio models | No API costs |

### Model Switching Strategies

#### Context-Aware Switching

```bash
# Interactive configuration
clippy "/model add fast gpt-3.5-turbo --name 'quick'" 
clippy "/model add code claude-3-sonnet --name 'coding'"
clippy "/model add analysis claude-3-opus --name 'deep'"

# Use in workflows
clippy "/model quick; perform quick search"
clippy "/model coding; generate complex code"
clippy "/model analysis; review architecture"
```

#### Automatic Model Selection

```json
// ~/.clippy/config.json
{
  "model_preferences": {
    "simple_tasks": "gpt-3.5-turbo",
    "code_generation": "claude-3-sonnet",
    "analysis": "claude-3-opus",
    "bulk_processing": "cerebras:llama-3.1-70b"
  },
  "auto_switch": true
}
```

## 🔌 MCP (Model Context Protocol) Integration

### Advanced MCP Configuration

#### Multi-Server Setup

```json
// ~/.clippy/mcp.json
{
  "mcp_servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/project"],
      "env": {
        "FILESYSTEM_ROOT": "/path/to/project"
      }
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git", "--repository", "."]
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "${DATABASE_URL}"
      }
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp", "--api-key", "${CTX7_API_KEY}"]
    }
  }
}
```

#### Server-Specific Configuration

```json
{
  "mcp_servers": {
    "custom-tools": {
      "command": "python",
      "args": ["-m", "my_mcp_server"],
      "cwd": "/path/to/mcp/server",
      "env": {
        "PYTHONPATH": "/path/to/mcp/server",
        "CUSTOM_CONFIG": "/path/to/config.json"
      }
    }
  }
}
```

### MCP Security Configuration

#### Trust Management

```bash
# Review available servers
clippy "/mcp list"

# Trust specific servers (auto-approve their tools)
clippy "/mcp allow filesystem"
clippy "/mcp allow git"
clippy "/mcp allow brave-search"

# Revoke trust
clippy "/mcp revoke postgres"

# View trusted servers
clippy "/mcp list --trusted"
```

#### Security Best Practices

```json
{
  "mcp_security": {
    "require_trust": true,
    "auto_trust_local": false,
    "audit_tools": true,
    "tool_timeout": 60,
    "sandbox_paths": [
      "/safe/directory",
      "${HOME}/projects"
    ]
  }
}
```

## 🤖 Subagent Optimization

### Performance Tuning

#### Concurrency Management

```bash
# Global configuration
export CLIPPY_MAX_CONCURRENT_SUBAGENTS=5
export CLIPPY_SUBAGENT_TIMEOUT=600
export CLIPPY_MAX_SUBAGENT_DEPTH=3

# Runtime adjustment
clippy "/subagent set max_concurrent 8"
clippy "/subagent set timeout 900"
```

#### Model Assignments

```bash
# Optimize by subagent type
clippy "/subagent set fast_general gpt-3.5-turbo"
clippy "/subagent set code_review claude-3-sonnet"
clippy "/subagent set power_analysis claude-3-opus-20240229"
clippy "/subagent set testing gpt-4"
clippy "/subagent set refact cerebras:llama-3.1-70b"
clippy "/subagent set documentation gpt-4-turbo"
```

#### Cache Optimization

```bash
# Enable aggressive caching for repetitive tasks
export CLIPPY_SUBAGENT_CACHE_ENABLED=true
export CLIPPY_SUBAGENT_CACHE_SIZE=500
export CLIPPY_SUBAGENT_CACHE_TTL=7200

# Clear cache when needed
clippy "/subagent clear-cache"
```

### Advanced Subagent Patterns

#### Hierarchical Workflows

```python
# Example: Complex code review workflow
{
  "task": "Perform comprehensive codebase analysis",
  "subagent_type": "power_analysis",
  "context": {
    "delegate_tasks": [
      {
        "task": "Security audit",
        "subagent_type": "code_review",
        "focus": "security"
      },
      {
        "task": "Performance analysis",
        "subagent_type": "power_analysis", 
        "focus": "performance"
      },
      {
        "task": "Generate regression tests",
        "subagent_type": "testing",
        "focus": "regression"
      }
    ]
  }
}
```

#### Specialized Toolsets

```bash
# Create subagent with custom tools
clippy "delegate to subagent with tools=read_file,write_file,grep: specialized task"

# Filter tools by category
clippy "delegate to code_review subagent: security analysis without write permissions"
```

## 🔧 Performance Optimization

### Memory Management

#### Context Optimization

```bash
# Reduce context window for tokens efficiency
clippy --max-tokens 2000 "simple task"

# Enable conversation compaction
clippy "/set compact_threshold 0.8"
clippy "/set compact_ratio 0.5"
```

#### Streaming Configuration

```bash
# Enable token streaming for faster feedback
export CLIPPY_STREAM_RESPONSES=true

# Configure buffer size
export CLIPPY_STREAM_BUFFER_SIZE=50
```

### Network Optimization

#### Connection Pooling

```json
{
  "network": {
    "pool_connections": 10,
    "pool_maxsize": 20,
    "pool_timeout": 30,
    "retry_attempts": 3,
    "retry_backoff": 1.5
  }
}
```

#### Proxy Configuration

```bash
# HTTP/HTTPS proxy
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=https://proxy.company.com:8443

# SOCKS proxy
export ALL_PROXY=socks5://proxy.company.com:1080

# Bypass proxy for local connections
export NO_PROXY=localhost,127.0.0.1,.local
```

### Caching Strategies

#### Multi-Level Caching

```json
{
  "cache": {
    "enable_disk_cache": true,
    "disk_cache_size": "1GB",
    "enable_memory_cache": true,
    "memory_cache_size": "512MB",
    "cache ttl": 3600,
    "compression": true
  }
}
```

#### Selective Caching

```bash
# Cache by operation type
export CLIPPY_CACHE_READ_OPERATIONS=true
export CLIPPY_CACHE_WRITE_OPERATIONS=false
export CLIPPY_CACHE_MCP_OPERATIONS=true
```

## 🛡️ Security Configuration

### Command Safety

#### Safety Level Configuration

```json
{
  "command_safety": {
    "level": "strict",  // loose, moderate, strict, paranoid
    "require_llm_check": true,
    "fallback_to_rules": true,
    "cache_decisions": true,
    "safety_cache_ttl": 3600
  }
}
```

#### Custom Safety Rules

```json
{
  "custom_safety_rules": [
    {
      "pattern": "rm -rf",
      "action": "block",
      "message": "Recursive deletion not allowed"
    },
    {
      "pattern": "curl | bash",
      "action": "require_approval",
      "message": "Downloading and executing code requires approval"
    }
  ]
}
```

### File System Security

#### Path Restrictions

```json
{
  "security": {
    "allowed_roots": [
      ".",
      "${HOME}/projects",
      "/tmp/clippy-work"
    ],
    "blocked_patterns": [
      "/etc",
      "/boot",
      "/proc",
      "/sys",
      "*/.ssh"
    ],
    "max_file_size": "10MB",
    "allowed_extensions": [
      ".py", ".js", ".ts", ".md", ".txt", ".json", ".yaml"
    ]
  }
}
```

#### Permission Configuration

```json
{
  "permissions": {
    "auto_approve": [
      "read_file",
      "list_directory",
      "search_files",
      "get_file_info",
      "grep"
    ],
    "require_approval": [
      "write_file",
      "delete_file",
      "create_directory",
      "execute_command",
      "edit_file"
    ],
    "deny": [
      "system_modification",
      "network_attacks"
    ]
  }
}
```

## 🌍 Environment-Specific Configuration

### Development Environment

```json
{
  "profile": "development",
  "models": {
    "default": "gpt-4",
    "fallback": "claude-3-sonnet"
  },
  "logging": {
    "level": "DEBUG",
    "include_tool_calls": true,
    "show_timing":true
  },
  "features": {
    "auto_save": true,
    "interactive_help": true,
    "syntax_highlighting": true
  }
}
```

### Production Environment

```json
{
  "profile": "production",
  "models": {
    "default": "gpt-4-turbo",
    "timeout": 60
  },
  "security": {
    "level": "strict",
    "audit_log": true,
    "require_approval": true
  },
  "performance": {
    "cache_enabled": true,
    "batch_operations": true
  }
}
```

### CI/CD Environment

```json
{
  "profile": "ci",
  "models": {
    "default": "gpt-3.5-turbo",
    "max_tokens": 1000
  },
  "automation": {
    "auto_approve_safe": true,
    "non_interactive": true,
    "fail_fast": true
  },
  "output": {
    "format": "json",
    "minimal": true
  }
}
```

## 🔍 Monitoring and Debugging

### Logging Configuration

```json
{
  "logging": {
    "level": "INFO",
    "handlers": [
      {
        "type": "console",
        "format": "simple"
      },
      {
        "type": "file",
        "path": "~/.clippy/logs/clippy-{timestamp}.log",
        "rotation": "daily",
        "retention": 30,
        "format": "detailed"
      }
    ],
    "loggers": {
      "clippy": "INFO",
      "subagent": "DEBUG",
      "mcp": "WARN",
      "safety": "INFO"
    }
  }
}
```

### Metrics Collection

```json
{
  "metrics": {
    "enabled": true,
    "collect": [
      "response_time",
      "token_usage",
      "tool_execution",
      "subagent_performance",
      "cache_hit_rate"
    ],
    "export": {
      "prometheus": {
        "enabled": true,
        "port": 9090
      },
      "file": {
        "path": "~/.clippy/metrics.json"
      }
    }
  }
}
```

### Performance Profiling

```bash
# Enable profiling
export CLIPPY_PROFILE=true
export CLIPPY_PROFILE_OUTPUT=~/.clippy/profiles/

# Profile specific operations
clippy --profile="deep_analysis" "complex task"

# Analyze profiles
python -m clippy.tools.analyze_profile ~/.clippy/profiles/latest.json
```

## 🎯 Workflow Automation

### Configuration Templates

```json
{
  "templates": {
    "code_review": {
      "model": "claude-3-sonnet",
      "subagent": "code_review",
      "permissions": "read_only",
      "timeout": 300
    },
    "feature_development": {
      "model": "gpt-4",
      "subagent": "general",
      "permissions": "full",
      "timeout": 600
    },
    "debugging": {
      "model": "gpt-4-turbo",
      "tools": ["read_file", "grep", "search_files"],
      "verbosity": "high"
    }
  }
}
```

### Custom Commands

```bash
# Create custom command aliases
alias clippy-review='clippy --template=code_review "Review current changes"'
alias clippy-feature='clippy --template=feature_development'
alias clippy-debug='clippy --template=debugging'

# Shell functions for common workflows
clippy-test-coverage() {
  clippy "Generate comprehensive tests for $(git diff --name-only HEAD~1 | tr '\n' ' ')"
}

clippy-security-audit() {
  clippy --subagent=code_review --focus=security "Audit security of current codebase"
}
```

## 🔧 Configuration Management

### Environment Switching

```bash
# Save configurations by environment
clippy "/config save development"
clippy "/config save production"
clippy "/config save testing"

# Switch between environments
clippy "/config load production"
clippy "/config load development"

# List available configurations
clippy "/config list"
```

### Configuration Validation

```bash
# Validate current configuration
clippy "/config validate"

# Check model availability
clippy "/config check-models"

# Test MCP connections
clippy "/config test-mcp"

# Verify permissions security
clippy "/config audit-security"
```

### Backup and Restore

```bash
# Backup configuration
clippy "/config backup"

# Restore from backup
clippy "/config restore backup-2024-01-15"

# Export configuration
clippy "/config export > my-config.json"

# Import configuration
clippy "/config import my-config.json"
```

## 🚀 Performance Tuning Checklist

### High-Impact Optimizations

1. **Model Selection**: Use appropriate models for task complexity
2. **Subagent Configuration**: Optimize concurrency and timeouts
3. **Caching**: Enable appropriate caching strategies
4. **Network**: Optimize connection settings and proxies
5. **Context Management**: Use conversation compaction

### Monitoring Metrics

1. **Response Time**: Keep under 10 seconds for interactive use
2. **Token Efficiency**: Aim for <1000 tokens for simple tasks
3. **Cache Hit Rate**: Target >50% for repetitive operations
4. **Subagent Success Rate**: Maintain >90% completion
5. **Memory Usage**: Monitor for memory leaks in long sessions

### Regular Maintenance

```bash
# Weekly cleanup
find ~/.clippy/logs/ -name "*.log" -mtime +7 -delete
find ~/.clippy/cache/ -type f -mtime +30 -delete
clippy "/subagent clear-expired-cache"

# Monthly optimization
clippy "/config optimize"
clippy "/model update-presets"
clippy "/mcp refresh-servers"
```

This advanced configuration guide helps you squeeze maximum performance and customize clippy-code for your specific workflow needs. Remember to test configuration changes gradually and monitor their impact! 🎯