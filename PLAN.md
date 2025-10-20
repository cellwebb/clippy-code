# Subagent Implementation Plan

## Overview

This document outlines the plan for implementing a subagent system in clippy-code. Subagents are specialized agent instances that can be spawned by the main agent to handle specific subtasks, enabling more complex, modular, and efficient task execution.

## Motivation

### Current Limitations

1. **Monolithic execution**: Single agent handles all tasks sequentially within a 50-iteration loop
2. **No parallelization**: Can't run multiple independent tasks concurrently
3. **Context pollution**: All tasks share the same conversation history
4. **No specialization**: Same system prompt and tools for all types of tasks
5. **Difficult debugging**: Hard to isolate specific subtask failures

### Benefits of Subagents

1. **Task delegation**: Main agent can delegate complex subtasks to specialized subagents
2. **Parallel execution**: Multiple subagents can work on independent tasks concurrently
3. **Context isolation**: Each subagent has its own conversation history
4. **Specialization**: Different system prompts, tools, and models for different task types
5. **Better error handling**: Failures in subagents don't crash the main agent
6. **Improved debugging**: Isolated logs and traces for each subagent
7. **Token efficiency**: Subagents only see relevant context for their task

## Architecture Design

### Core Components

#### 1. SubAgent Class (`src/clippy/agent/subagent.py`)

```python
class SubAgent:
    """
    A specialized agent instance for handling specific subtasks.

    Attributes:
        name: Unique identifier for this subagent
        task: The task this subagent is responsible for
        system_prompt: Specialized system prompt (optional)
        allowed_tools: Subset of tools available to this subagent
        model: Model to use (can differ from main agent)
        conversation_history: Isolated conversation history
        parent_agent: Reference to the main agent (for context if needed)
    """
```

Key methods:

- `run(task: str) -> SubAgentResult`: Execute the subagent's task
- `get_status() -> SubAgentStatus`: Get current execution status
- `interrupt()`: Interrupt the subagent's execution
- `get_result() -> SubAgentResult`: Get the final result

#### 2. SubAgentManager (`src/clippy/agent/subagent_manager.py`)

```python
class SubAgentManager:
    """
    Manages lifecycle and coordination of subagents.

    Responsibilities:
        - Create and track subagent instances
        - Coordinate parallel execution
        - Aggregate results from multiple subagents
        - Handle subagent failures and retries
        - Manage resource limits (max concurrent subagents)
    """
```

Key methods:

- `create_subagent(config: SubAgentConfig) -> SubAgent`
- `run_sequential(subagents: list[SubAgent]) -> list[SubAgentResult]`
- `run_parallel(subagents: list[SubAgent], max_concurrent: int) -> list[SubAgentResult]`
- `get_active_subagents() -> list[SubAgent]`
- `terminate_all()`

#### 3. SubAgent Tool (`src/clippy/tools/delegate_to_subagent.py`)

```python
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "delegate_to_subagent",
        "description": (
            "Delegate a complex subtask to a specialized subagent. "
            "Use this when you need to handle a well-defined subtask that would benefit from "
            "isolated context, specialized prompting, or parallel execution."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Clear description of the task for the subagent to complete"
                },
                "subagent_type": {
                    "type": "string",
                    "enum": ["general", "code_review", "testing", "refactor", "documentation"],
                    "description": "Type of specialized subagent to use"
                },
                "allowed_tools": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tools the subagent is allowed to use (optional)"
                },
                "context": {
                    "type": "object",
                    "description": "Additional context to provide to the subagent (optional)"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 300)",
                    "default": 300
                }
            },
            "required": ["task", "subagent_type"]
        }
    }
}
```

#### 4. Subagent Types & Configurations

Define specialized subagent types in `src/clippy/agent/subagent_types.py`:

```python
SUBAGENT_TYPES = {
    "general": {
        "system_prompt": "You are a helpful AI assistant focused on completing the given task efficiently.",
        "allowed_tools": "all",  # All standard tools
        "model": None,  # Use parent model
        "max_iterations": 25,
    },
    "code_review": {
        "system_prompt": (
            "You are a code review specialist. Focus on code quality, best practices, "
            "security issues, and potential bugs. Provide actionable feedback."
        ),
        "allowed_tools": ["read_file", "read_files", "grep", "search_files", "list_directory"],
        "model": None,
        "max_iterations": 15,
    },
    "testing": {
        "system_prompt": (
            "You are a testing specialist. Write comprehensive tests, identify edge cases, "
            "and ensure good test coverage. Follow testing best practices."
        ),
        "allowed_tools": [
            "read_file", "write_file", "execute_command", "search_files", "grep"
        ],
        "model": None,
        "max_iterations": 30,
    },
    "refactor": {
        "system_prompt": (
            "You are a refactoring specialist. Improve code structure, readability, and "
            "maintainability while preserving functionality. Follow DRY and SOLID principles."
        ),
        "allowed_tools": [
            "read_file", "read_files", "write_file", "edit_file", "search_files", "grep"
        ],
        "model": None,
        "max_iterations": 30,
    },
    "documentation": {
        "system_prompt": (
            "You are a documentation specialist. Write clear, comprehensive documentation "
            "with examples. Focus on helping users understand the code and how to use it."
        ),
        "allowed_tools": [
            "read_file", "read_files", "write_file", "search_files", "grep", "list_directory"
        ],
        "model": None,
        "max_iterations": 20,
    },
}
```

### Data Flow

```
Main Agent
    |
    |- User requests complex task
    |
    |- Agent decides to delegate subtask
    |
    |- Calls delegate_to_subagent tool
    |
    v
SubAgentManager
    |
    |- Creates SubAgent instance with specialized config
    |
    |- SubAgent runs in isolated context
    |     - Has own conversation history
    |     - Uses specialized system prompt
    |     - Has restricted tool access
    |     - Max iteration limit
    |
    |- SubAgent completes or fails
    |
    |- Returns SubAgentResult to manager
    |
    v
Main Agent
    |
    |- Receives tool result with subagent output
    |
    |- Integrates result into main conversation
    |
    |- Continues with next steps
```

### SubAgentResult Structure

```python
@dataclass
class SubAgentResult:
    """Result from a subagent execution."""

    success: bool
    output: str  # Final response from subagent
    error: str | None  # Error message if failed
    iterations_used: int  # How many iterations the subagent took
    tokens_used: dict[str, int]  # Token usage statistics
    tools_executed: list[str]  # List of tools used
    execution_time: float  # Time in seconds
    metadata: dict[str, Any]  # Additional metadata
```

## Implementation Steps

### Phase 1: Core Subagent Infrastructure (Week 1)

#### Step 1.1: Create SubAgent Class

- File: `src/clippy/agent/subagent.py`
- Implement basic SubAgent class extending or wrapping ClippyAgent
- Add isolated conversation history
- Add specialized system prompt support
- Add tool filtering logic
- Add iteration tracking and limits

#### Step 1.2: Create SubAgentManager

- File: `src/clippy/agent/subagent_manager.py`
- Implement subagent lifecycle management
- Add sequential execution support
- Add basic error handling
- Add result aggregation

#### Step 1.3: Define Subagent Types

- File: `src/clippy/agent/subagent_types.py`
- Define SUBAGENT_TYPES configuration
- Add configuration validation
- Add helper functions for loading configs

#### Step 1.4: Update Core Agent

- Modify `src/clippy/agent/core.py` to integrate SubAgentManager
- Add `self.subagent_manager` to ClippyAgent
- Pass necessary dependencies to manager

### Phase 2: Tool Integration (Week 2)

#### Step 2.1: Create delegate_to_subagent Tool

- File: `src/clippy/tools/delegate_to_subagent.py`
- Implement tool schema (TOOL_SCHEMA)
- Implement execution logic
- Add to tool catalog in `src/clippy/tools/__init__.py`

#### Step 2.2: Add to Executor

- Update `src/clippy/executor.py`
- Add `ActionType.DELEGATE_TO_SUBAGENT` enum
- Implement `execute_delegate_to_subagent()` method
- Add to action_map

#### Step 2.3: Permission Configuration

- Update `src/clippy/permissions.py`
- Add `DELEGATE_TO_SUBAGENT` to permission config
- Default: REQUIRE_APPROVAL (user should approve subagent creation)
- Consider adding auto-approval for certain subagent types

### Phase 3: Parallel Execution (Week 3)

#### Step 3.1: Add Async Support

- Update SubAgentManager with async/await support
- Implement `run_parallel()` method using asyncio
- Add max_concurrent_subagents limit
- Add resource pooling for API calls

#### Step 3.2: Add run_parallel_subagents Tool

- File: `src/clippy/tools/run_parallel_subagents.py`
- Schema for running multiple subagents in parallel
- Coordinate execution through SubAgentManager
- Return aggregated results

#### Step 3.3: Status Monitoring

- Add subagent status tracking
- Implement progress reporting
- Add `/subagents` command to CLI for viewing active subagents
- Display subagent activity in document mode

### Phase 4: Advanced Features (Week 4)

#### Step 4.1: Context Sharing

- Add mechanism for subagents to access parent context (read-only)
- Implement context filtering (what info to share)
- Add context summarization for large parent histories

#### Step 4.2: Result Caching

- Cache subagent results for similar tasks
- Implement cache invalidation logic
- Add `/subagent cache clear` command

#### Step 4.3: Subagent Chaining

- Allow subagents to spawn their own subagents (with depth limit)
- Implement hierarchical result aggregation
- Add visualization of subagent tree

#### Step 4.4: Model Selection per Subagent

- Allow different models for different subagent types
- Add to SUBAGENT_TYPES config
- E.g., fast model for simple tasks, powerful model for complex ones

### Phase 5: Testing & Documentation (Week 5)

#### Step 5.1: Unit Tests

- `tests/agent/test_subagent.py` - Test SubAgent class
- `tests/agent/test_subagent_manager.py` - Test manager
- `tests/tools/test_delegate_to_subagent.py` - Test tool
- Mock LLM calls, test isolation and result handling

#### Step 5.2: Integration Tests

- `tests/integration/test_subagent_workflow.py`
- Test end-to-end subagent delegation
- Test parallel execution
- Test error scenarios

#### Step 5.3: Documentation

- Update CLAUDE.md with subagent architecture
- Update AGENTS.md with usage examples
- Create SUBAGENTS.md with detailed guide
- Add examples to README.md

#### Step 5.4: Examples

- Create `examples/subagent_code_review.py`
- Create `examples/subagent_parallel_testing.py`
- Create `examples/subagent_refactoring.py`

## Usage Examples

### Example 1: Code Review with Subagent

```python
# Main agent receives: "Review all Python files in src/ for code quality issues"

# Agent uses delegate_to_subagent tool:
{
    "task": "Review Python files in src/ directory for code quality, security, and best practices",
    "subagent_type": "code_review",
    "context": {
        "focus_areas": ["security", "performance", "maintainability"],
        "exclude_patterns": ["**/test_*.py", "**/__pycache__/**"]
    }
}

# Subagent gets specialized prompt and limited tools (read-only)
# Subagent analyzes files and returns detailed review
# Main agent presents results to user
```

### Example 2: Parallel Test Generation

```python
# Main agent receives: "Generate tests for all modules in src/clippy/"

# Agent creates multiple testing subagents in parallel:
subagents = [
    {"task": "Write tests for src/clippy/agent/core.py", "subagent_type": "testing"},
    {"task": "Write tests for src/clippy/executor.py", "subagent_type": "testing"},
    {"task": "Write tests for src/clippy/permissions.py", "subagent_type": "testing"},
]

# SubAgentManager runs them concurrently (e.g., max 3 at a time)
# Results aggregated and presented to user
# Main agent handles any conflicts or issues
```

### Example 3: Refactoring with Context Isolation

```python
# Main agent receives: "Refactor the tools module to reduce duplication"

# Agent delegates to refactor subagent:
{
    "task": "Analyze tools in src/clippy/tools/ and refactor to extract common patterns",
    "subagent_type": "refactor",
    "allowed_tools": ["read_file", "read_files", "write_file", "edit_file", "search_files"],
    "timeout": 600  # Give more time for complex refactoring
}

# Subagent works in isolation, doesn't pollute main conversation
# Returns refactored code with explanation
# Main agent reviews and applies changes
```

## Configuration

### Environment Variables

```bash
# Maximum concurrent subagents
CLIPPY_MAX_CONCURRENT_SUBAGENTS=3

# Subagent timeout (seconds)
CLIPPY_SUBAGENT_TIMEOUT=300

# Enable subagent result caching
CLIPPY_SUBAGENT_CACHE_ENABLED=true

# Maximum subagent nesting depth
CLIPPY_MAX_SUBAGENT_DEPTH=2
```

### Config File (`~/.clippy.env` or `.env`)

```bash
CLIPPY_MAX_CONCURRENT_SUBAGENTS=5
CLIPPY_SUBAGENT_TIMEOUT=600
CLIPPY_SUBAGENT_CACHE_ENABLED=true
CLIPPY_MAX_SUBAGENT_DEPTH=3
```

## CLI Commands

```bash
# View active subagents
/subagents

# View subagent history
/subagents history

# Clear subagent cache
/subagents cache clear

# Configure subagent settings
/subagents config max_concurrent 5
/subagents config timeout 600
```

## Permission System Integration

### Permission Levels for Subagents

1. **AUTO_APPROVE**:

   - Read-only subagent types (e.g., code_review with only read tools)
   - Documentation subagents reading existing files

2. **REQUIRE_APPROVAL**:

   - Subagents that can write/modify files (testing, refactor)
   - Subagents that can execute commands
   - Subagents running in parallel (batch approval)

3. **DENY**:
   - Subagents attempting to spawn too many children (depth > limit)
   - Subagents requesting unauthorized tools

### Approval UX

```
┌─ Subagent Request ─────────────────────────────────┐
│ Type: testing                                       │
│ Task: Write tests for src/clippy/agent/core.py    │
│ Tools: read_file, write_file, execute_command     │
│ Est. iterations: ~15                               │
│ Timeout: 300s                                      │
├────────────────────────────────────────────────────┤
│ Approve? [y/n/v(view config)] _                   │
└────────────────────────────────────────────────────┘
```

## Error Handling

### Subagent Failure Scenarios

1. **Timeout**: Subagent exceeds time limit

   - Main agent receives timeout error
   - Partial results returned if available
   - Main agent can retry or adjust approach

2. **Iteration Limit**: Subagent reaches max iterations

   - Return partial results with warning
   - Main agent can continue or spawn new subagent

3. **Tool Permission Denied**: Subagent tries unauthorized tool

   - Subagent execution stops
   - Error reported to main agent
   - Main agent can grant permission or adjust task

4. **API Error**: LLM API fails during subagent execution
   - Retry logic (same as main agent)
   - Fallback to simpler model if configured
   - Report error to main agent on final failure

### Error Propagation

```python
SubAgentResult(
    success=False,
    output="",
    error="Subagent exceeded iteration limit (25 iterations)",
    iterations_used=25,
    tokens_used={...},
    tools_executed=["read_file", "write_file", ...],
    execution_time=45.2,
    metadata={
        "failure_reason": "max_iterations",
        "last_action": "write_file",
        "partial_output": "Generated 3 out of 5 test files..."
    }
)
```

## Testing Strategy

### Unit Tests

- Test SubAgent in isolation with mocked LLM
- Test SubAgentManager lifecycle operations
- Test tool schema and execution
- Test permission checks

### Integration Tests

- Test end-to-end subagent delegation
- Test parallel execution with multiple subagents
- Test error handling and recovery
- Test conversation history isolation

### Performance Tests

- Measure overhead of subagent creation
- Test parallel execution efficiency
- Benchmark token usage with/without subagents
- Test memory usage with many concurrent subagents

## Migration & Backward Compatibility

- Subagents are opt-in via the `delegate_to_subagent` tool
- Existing functionality unchanged
- Main agent loop still works as before
- Users can disable subagent feature via config if needed

## Future Enhancements

### Phase 6+: Advanced Features

1. **Subagent Templates**: User-defined subagent types via config
2. **Streaming Results**: Stream subagent output to user in real-time
3. **Subagent Collaboration**: Multiple subagents sharing context
4. **Learning from Results**: Improve subagent selection based on past success
5. **Resource Quotas**: Token/cost limits per subagent
6. **Subagent Marketplace**: Community-shared subagent configurations
7. **Visual Debugger**: Web UI for visualizing subagent execution tree

## Risks & Mitigations

| Risk                 | Impact | Mitigation                                 |
| -------------------- | ------ | ------------------------------------------ |
| Increased complexity | Medium | Keep API simple, good docs, clear examples |
| Token cost explosion | High   | Strict limits, monitoring, user approval   |
| Debugging difficulty | Medium | Detailed logging, visualization tools      |
| Performance overhead | Low    | Async execution, resource pooling          |
| Permission confusion | Medium | Clear UX, sensible defaults, documentation |

## Success Metrics

1. **Functionality**: Can handle complex multi-step tasks efficiently
2. **Performance**: Parallel execution shows speedup vs sequential
3. **Usability**: Users find subagent delegation intuitive
4. **Reliability**: <5% subagent failure rate in normal usage
5. **Adoption**: >30% of complex tasks use subagent delegation

## Timeline Summary

- **Week 1**: Core infrastructure (SubAgent, SubAgentManager, types)
- **Week 2**: Tool integration (delegate_to_subagent, executor, permissions)
- **Week 3**: Parallel execution (async support, parallel tool)
- **Week 4**: Advanced features (context sharing, caching, chaining)
- **Week 5**: Testing & documentation (tests, docs, examples)

**Total**: ~5 weeks for full implementation

## Open Questions

1. Should subagents share the same API key/quota as main agent, or have separate limits?
2. What's the optimal default for max_concurrent_subagents?
3. Should we support custom subagent types defined in user config?
4. How to handle subagent results that conflict with each other?
5. Should subagents have access to parent conversation history (read-only)?
6. What telemetry/analytics should we collect for subagent usage?

## Next Steps

1. Review and refine this plan with stakeholders
2. Create detailed technical specs for Phase 1
3. Set up project tracking (GitHub issues/project board)
4. Begin implementation of Phase 1
5. Create MVP with basic subagent support for testing
