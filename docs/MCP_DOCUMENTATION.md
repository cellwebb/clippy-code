# MCP (Model Context Protocol) Documentation for clippy-code

📎 Model Context Protocol (MCP) integration allows clippy-code to dynamically discover and use tools from external MCP servers. This enables extending the agent's capabilities without modifying the core codebase.

## What is MCP?

The Model Context Protocol (MCP) is an open specification that enables applications to expose tools to AI models in a standardized way. MCP servers can provide various capabilities like:

- File system operations
- Database access
- API integrations
- Specialized domain tools
- Custom business logic

## How MCP Works in clippy-code

When clippy-code starts, it:

1. Looks for MCP configuration files
2. Connects to configured MCP servers
3. Discovers available tools from each server
4. Maps MCP tool schemas to OpenAI-compatible format
5. Makes these tools available during agent iterations

MCP tools are automatically integrated with clippy-code's permission system. By default, MCP tools require user approval before execution, but you can trust specific servers to auto-approve their tools.

## MCP Configuration

To use MCP servers, create an `mcp.json` configuration file. The configuration can be placed in:

1. `$HOME/.clippy/mcp.json` (user-level configuration - highest priority)
2. `$PWD/.clippy/mcp.json` (project-level configuration)

The configuration file uses JSON format with the following structure:

```json
{
  "mcp_servers": {
    "server-id": {
      "command": "executable-command",
      "args": ["argument1", "argument2", "..."],
      "env": {
        "ENV_VAR_NAME": "environment-variable-value"
      },
      "cwd": "/working/directory",
      "timeout_s": 30
    }
  }
}
```

### Configuration Fields

- `server-id`: A unique identifier for the MCP server (you can use any name)
- `command`: The executable command to start the MCP server
- `args`: Array of command-line arguments to pass to the server
- `env`: Optional dictionary of environment variables to set for the server process
- `cwd`: Optional working directory for the server process
- `timeout_s`: Optional timeout in seconds for server operations (default: 30)

**Note**: Stderr output from MCP servers is automatically redirected to clippy's debug logs to keep your terminal clean. This means progress indicators and debug messages won't clutter your terminal, but they're still available in the logs if needed for debugging.

### Environment Variable Substitution

You can use environment variable substitution in your MCP configuration using the syntax `${VAR_NAME}`:

```json
{
  "mcp_servers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp", "--api-key", "${CTX7_API_KEY}"]
    },
    "perplexity-ask": {
      "command": "npx",
      "args": ["-y", "server-perplexity-ask"],
      "env": { "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}" }
    }
  }
}
```

## MCP Commands in Interactive Mode

Once configured, you can manage MCP servers using these slash commands in interactive/document mode:

- `/mcp list` - List configured MCP servers and their connection status
- `/mcp tools [server]` - List tools available from MCP servers (all servers or specific one)
- `/mcp refresh` - Refresh connections to MCP servers and update tool catalogs
- `/mcp allow <server>` - Mark an MCP server as trusted for this session (auto-approves its tools)
- `/mcp revoke <server>` - Revoke trust for an MCP server

## Examples

### Example 1: Context7 Integration

```json
{
  "mcp_servers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp", "--api-key", "${CTX7_API_KEY}"]
    }
  }
}
```

Once configured, you can use Context7 tools like retrieving documentation for libraries:

```
/mcp allow context7  # Trust the context7 server
```

### Example 2: Perplexity Ask Integration

```json
{
  "mcp_servers": {
    "perplexity-ask": {
      "command": "npx",
      "args": ["-y", "server-perplexity-ask"],
      "env": { "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}" }
    }
  }
}
```

### Example 3: Custom Local MCP Server

```json
{
  "mcp_servers": {
    "local-tools": {
      "command": "python",
      "args": ["./tools/mcp_server.py"],
      "cwd": "/path/to/project",
      "timeout_s": 60
    }
  }
}
```

## Trust System

For security, MCP tools require explicit user approval before execution. However, you can mark servers as trusted:

```
/mcp allow server-name  # Auto-approve all tools from this server
/mcp revoke server-name  # Remove trust for this server
```

Trusted servers have their tools auto-approved for the current session.

## Error Handling

MCP integration includes comprehensive error handling:

- Connection failures are gracefully handled
- Tool execution errors are properly reported
- Schema mapping errors are logged but don't crash the application
- Timeout handling for long-running operations

When an MCP tool fails, you'll see detailed error messages that help identify the issue.

## Developing Custom MCP Servers

To create a custom MCP server for use with clippy-code:

1. Implement the MCP protocol specification
2. Expose your tools using the standardized MCP interface
3. Configure clippy-code to connect to your server
4. Test integration using the `/mcp` commands

Many MCP servers are available as npm packages that can be easily integrated:

- `@upstash/context7-mcp` - Context7 documentation retrieval
- `server-perplexity-ask` - Perplexity API integration
- And many more community-developed tools

## Best Practices

1. **Security**: Only trust MCP servers you control or explicitly trust
2. **Timeouts**: Set appropriate timeouts for your tools
3. **Error Handling**: Implement proper error handling in your MCP tools
4. **Documentation**: Provide clear descriptions for your MCP tools
5. **Schema Validation**: Use proper JSON Schema for tool input validation

## Troubleshooting

If MCP tools aren't appearing:

1. Check your `mcp.json` configuration file syntax
2. Verify the server executable is available in your PATH
3. Check that environment variables are properly set
4. Use `/mcp refresh` to retry connections
5. Look for error messages in the console output

If MCP tools fail to execute:

1. Ensure the server process is running correctly
2. Check for network or permission issues
3. Verify API keys and authentication
4. Check clippy's debug logs (`~/.clippy/logs/`) for stderr output from the MCP server - all MCP server stderr is automatically logged there
