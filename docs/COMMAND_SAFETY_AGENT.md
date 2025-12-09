# Command Safety Agent

The command safety agent is a specialized security layer that provides intelligent analysis of shell commands before they are executed. Unlike traditional pattern-based filtering, it uses LLM-powered analysis to understand command context and intent, providing more nuanced and comprehensive protection against dangerous operations.

## Overview

The command safety agent is **not** a regular subagent that users can call directly. It's an internal security mechanism that:

- Is automatically invoked whenever `execute_command` is used
- Analyzes commands in full context (including working directory)
- Uses conservative security policies to "err on the side of caution"
- Blocks commands that could cause harm, data loss, or security issues
- Works alongside existing pattern-based safety checks

## How It Works

### Integration Points

1. **Executor Integration**: The safety checker is integrated into `ActionExecutor` when an LLM provider is available
2. **Pre-execution Analysis**: Commands are analyzed before reaching the actual `execute_command` function
3. **Context-aware**: Considers both the command string and working directory
4. **Fail-safe**: If the safety check fails, commands are blocked by default

### Safety Agent Behavior

The safety agent follows these principles:

- **Ultra-conservative**: Better to block a safe command than allow a dangerous one
- **Context-aware**: Same command may be safe in one directory but dangerous in another
- **LLM-powered**: Uses language model intelligence to understand command semantics
- **Comprehensive**: Blocks categories beyond simple patterns

## Blocked Command Categories

The safety agent blocks commands that:

### Destructive Operations
- Delete files/directories (`rm`, `rmdir`, `shred`) especially recursive operations
- Format disks or filesystems (`mkfs`, `fdisk`, `format`)
- Overwrite critical files with redirects

### System File Modifications
- Modify files in `/etc/`, `/boot/`, `/sys/`, `/proc/`
- Change kernel modules
- Modify sensitive system file permissions (`chmod`, `chown`)

### Software Installation
- Install software without explicit consent (`apt`, `yum`, `pip`, `npm`, `cargo`)
- Package manager operations

### Network Security Risks
- Download and execute code (`curl | bash`, `wget | sh`)
- Network attacks or scanning (`nmap`, `netcat`)
- Access or compromise credentials/API keys

### Privilege Escalation
- Commands with `sudo` unless clearly necessary and safe
- System disruption (fork bombs, killing system processes)

### File System Attacks
- Overwrite block devices (`dd` to `/dev/sda`)
- Modify `/dev/null` or other special files

## Configuration

### Automatic Setup

When using clippy-code with an LLM provider, the safety agent is automatically enabled:

```python
# In ActionExecutor.__init__
llm_provider = LLMProvider(api_key="...", model="gpt-4")
executor = ActionExecutor(permission_manager, llm_provider=llm_provider)
```

### Manual Updates

The LLM provider can be updated after initialization:

```python
executor.set_llm_provider(new_provider)
```

This is automatically called when:
- Agent switches models using `/model` command
- Agent loads saved conversations

### Fallback Behavior

If no LLM provider is available, the system falls back to basic pattern matching:
- Existing dangerous pattern detection still works
- No LLM-powered analysis is performed
- Commands execute if they don't match known dangerous patterns

## Safety Agent Prompt

The safety agent uses a highly specialized system prompt that:

- Emphasizes extreme caution
- Provides clear examples of blocked vs allowed commands
- Requires exact "ALLOW:" or "BLOCK:" response format
- Includes working directory context in analysis

Example of the system prompt structure:
```
You are a specialized shell command security agent...
ERR ON THE SIDE OF CAUTION...
You must BLOCK commands that:
- Delete files/directories...
Respond with EXACTLY one line:
ALLOW: [brief reason if safe] or
BLOCK: [specific security concern]
```

## Testing the Safety Agent

### Unit Tests

The safety agent includes comprehensive tests covering:

- Safe commands being allowed
- Dangerous commands being blocked
- LLM failure handling (fail-safe blocking)
- Working directory context awareness
- Integration with executor

### Example Test

```python
def test_dangerous_command_blocked():
    mock_provider = Mock()
    mock_provider.get_streaming_response.return_value = ["BLOCK: Too dangerous"]
    
    executor = ActionExecutor(permission_manager, llm_provider=mock_provider)
    success, message, result = executor.execute(
        "execute_command", {"command": "rm -rf .", "working_dir": "."}
    )
    
    assert success is False
    assert "blocked by safety agent" in message.lower()
```

## Performance Considerations

### Latency

The safety check adds minimal overhead:
- Typically < 1 second for LLM analysis
- Parallelizable with other security checks
- No impact on non-command tools

### Fail-safe Operation

- If LLM provider is unavailable, falls back to pattern matching
- Network failures or timeouts result in command blocking
- No risk of executing commands due to safety check failures

## Security vs Convenience

The safety agent prioritizes security over convenience:

- False positives (blocking safe commands) are preferred over false negatives
- Users can override with YOLO mode if needed (at their own risk)
- Patterns and prompts are conservative by design

## Future Enhancements

Potential improvements being considered:

### Enhanced Context
- Git repository awareness (don't delete .git)
- Project file analysis (don't delete important source files)
- User permission context

### Learning Capabilities
- User feedback integration
- Adaptive risk assessment
- Personalized safety profiles

### Expanded Coverage
- Container security awareness
- Cloud service specific protections
- CI/CD pipeline safety

## Troubleshooting

### Commands Being Blocked Unexpectedly

1. **Check the error message**: It includes the safety agent's reasoning
2. **Verify working directory**: Same command may be safe in different contexts
3. **Review command construction**: Try safer alternatives
4. **Use YOLO mode**: For trusted environments (use with caution)

### Safety Check Failures

If safety checks are failing completely:

1. **Check LLM provider status**: Ensure API keys are valid
2. **Network connectivity**: Verify internet access for API calls
3. **Provider configuration**: Check model availability and settings
4. **Fallback to pattern mode**: System will work without LLM if needed

## Limitations

- **Not perfect**: May have false positives
- **Context dependent**: Same command在不同目录可能有不同风险评估
- **LLM dependent**: Requires working LLM provider for enhanced protection
- **English commands**: Optimized for English command analysis

## Contributing

When improving the safety agent:

1. **Test thoroughly**: Use comprehensive test cases
2. **Stay conservative**: Don't reduce safety checks
3. **Document changes**: Update prompts and examples
4. **考虑安全性**: Always prioritize security over convenience