# MCP Documentation for clippy-code

## Overview

clippy-code supports the Model Context Protocol (MCP) for dynamically discovering and using external tools. MCP enables external services to expose tools that can be used by the agent without requiring changes to the core codebase.

## Configuration

### Creating the Configuration File

Create an `mcp.json` configuration file in your home directory (`~/.clippy/mcp.json`) or project directory (`.clippy/mcp.json`):

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
      "env": {
        "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}"
      }
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "mcp-sequential-thinking"]
    }
  }
}
```

### Server Configuration

Each MCP server can have the following properties:

- `command`: The command to run (required)
- `args`: Array of command arguments (required)
- `env`: Additional environment variables (optional)
- `cwd`: Working directory for the server (optional)

### Environment Variables

Use `${VAR_NAME}` syntax to reference environment variables in your configuration:

```json
{
  "mcp_servers": {
    "my-server": {
      "command": "node",
      "args": ["server.js"],
      "env": {
        "API_KEY": "${MY_API_KEY}",
        "DATABASE_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

## Available MCP Commands

### `/mcp list`
Show configured MCP servers and their connection status.

### `/mcp tools [server]`
List available tools from MCP servers. If `server` is specified, only show tools from that server.

### `/mcp refresh`
Refresh connections to MCP servers and reload tool catalogs.

### `/mcp allow <server>`
Mark an MCP server as trusted for the current session. Trusted servers have their tools auto-approved.

### `/mcp revoke <server>`
Revoke trust for an MCP server. Tools from this server will require approval.

## Security

### Trust System

clippy-code implements a trust system for MCP servers:

- **New servers**: Require explicit trust before tools can be used
- **Trusted servers**: Tools are auto-approved but can still be blocked
- **Permission integration**: MCP tools respect the same permission system as built-in tools

### Safety Considerations

- Only use MCP servers from sources you trust
- Review server commands and arguments carefully
- Keep API keys secure using environment variables
- Regularly review which servers are trusted

## Example Configurations

### Context7 (Documentation Retrieval)

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

### Perplexity AI (Web Search)

```json
{
  "mcp_servers": {
    "perplexity": {
      "command": "npx",
      "args": ["-y", "server-perplexity-ask"],
      "env": {
        "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}"
      }
    }
  }
}
```

### Local MCP Server

```json
{
  "mcp_servers": {
    "local-tools": {
      "command": "python",
      "args": ["-m", "my_mcp_server"],
      "cwd": "/path/to/server"
    }
  }
}
```

## Troubleshooting

### Server Won't Connect

1. Check that the command and arguments are correct
2. Ensure all required environment variables are set
3. Verify that any required dependencies are installed
4. Use `/mcp list` to check connection status

### Tools Not Available

1. Run `/mcp refresh` to reload tool catalogs
2. Check server logs for errors
3. Verify the server is properly configured

### Permission Issues

1. Use `/mcp allow <server>` to trust a server
2. Check that MCP tool permissions aren't blocked in configuration
3. Review the specific tool being requested

## Developing MCP Servers

For information on developing your own MCP servers, see:
- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP SDK Documentation](https://github.com/modelcontextprotocol/servers)

## Integration with clippy-code

MCP tools integrate seamlessly with clippy-code's existing features:

- **Permission System**: MCP tools respect auto-approval and manual approval settings
- **Tool Execution**: Same format and error handling as built-in tools
- **Conversation Context**: MCP results are included in conversation history
- **Subagent Support**: MCP tools can be used by subagents

## Examples in Use

### Web Search with Perplexity

```
[You] ➜ search the web for latest python 3.12 features

[clippy-code] I'll search the web for the latest Python 3.12 features using the Perplexity MCP server.

→ perplexity-ask
  query: "latest python 3.12 features"

[?] Approve this action? [(y)es/(n)o/(a)llow]: y

✓ Found information about Python 3.12 features...
```

### Documentation Lookup with Context7

```
[You] ➜ explain how to use context managers in python

[clippy-code] I'll look up Python context manager documentation using Context7.

→ context7
  topic: "python context managers"

[?] Approve this action? [(y)es/(n)o/(a)llow]: y

✓ Retrieved comprehensive documentation...
```