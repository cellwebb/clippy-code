# Claude Code OAuth Authentication

clippy-code now supports Claude Code OAuth authentication, allowing users with Claude Code subscriptions to access their models without requiring an Anthropic API key.

## Overview

Claude Code OAuth provides an alternative authentication method that:
- Uses your Claude Code subscription instead of Anthropic API credits
- Supports the latest Claude models (Sonnet, Opus, etc.)
- Works with the OAuth flow for secure token management
- Automatically handles token refresh and storage

## Quick Start

### 1. Authenticate with Claude Code

```bash
# Start the OAuth authentication flow
uv run python -m clippy auth

# Run in quiet mode (minimal output)
uv run python -m clippy auth --quiet

# Specify log level
uv run python -m clippy auth --log-level DEBUG
```

The authentication process will:
1. Open a browser window to Claude's OAuth page
2. Ask you to sign in and authorize clippy-code
3. Capture the OAuth callback and exchange codes
4. Save the access token to `~/.clippy/.env`

### 2. Check Authentication Status

```bash
uv run python -m clippy auth-status
```

This will show whether you have a valid Claude Code OAuth token configured.

### 3. Use Claude Code Models

```bash
# Interactive mode with Claude Code Sonnet
uv run python -m clippy --model claude-code:claude-sonnet-4-5

# One-shot mode
uv run python -m clippy --model claude-code:claude-opus-4-5 "Explain quantum computing"

# Save as a named model for easier access
uv run python -m clippy
> /model add claude-code claude-sonnet-4-5 --name claude-sonnet --default
```

## Features

### Authentication Commands

- `clippy auth` - Start OAuth authentication flow
- `clippy auth-status` - Check authentication status
- `clippy auth --quiet` - Silent authentication mode
- `clippy auth --log-level DEBUG` - Debug authentication

### Model Integration

- Seamlessly integrates with existing model system
- Works with `/model add`, `/model list`, `/model` commands
- Supports all Claude Code models (Sonnet, Opus, Haiku)
- Automatic token management and refresh

### Security

- PKCE OAuth flow for secure authentication
- Local token storage in `~/.clippy/.env`
- Environment variable priority for flexibility
- Scoped permissions (API creation, profile, inference)

## Usage Examples

```bash
# Authenticate and start using Claude Code
uv run python -m clippy auth
uv run python -m clippy --model claude-code:claude-sonnet-4-5

# Add Claude Code models to your collection
uv run python -m clippy
> /model add claude-code claude-sonnet-4-5 --name claude-sonnet --default
> /model add claude-code claude-opus-4-5 --name claude-opus

# Use in scripts
export CLAUDE_CODE_ACCESS_TOKEN=$(cat ~/.clippy/.env | grep CLAUDE_CODE_ACCESS_TOKEN | cut -d'=' -f2)
uv run python -m clippy --model claude-code:claude-sonnet-4-5 "Your prompt here"
```

## Troubleshooting

### Common Issues

1. **"No Claude Code OAuth token found"**
   - Run `uv run python -m clippy auth` to authenticate

2. **Authentication fails**
   - Check network connection
   - Disable ad blockers temporarily
   - Try authentication again

3. **Browser doesn't open**
   - Copy URL from terminal manually
   - Open in browser to complete flow

4. **Token not found in environment**
   - Export from file: `source ~/.clippy/.env`
   - Or set manually: `export CLAUDE_CODE_ACCESS_TOKEN=your_token`

### Debug Mode

```bash
uv run python -m clippy auth --log-level DEBUG
```

For more detailed troubleshooting, see the full documentation or open an issue on GitHub.