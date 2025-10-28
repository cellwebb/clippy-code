# Subagent System Documentation

This document provides comprehensive documentation for clippy-code's subagent system, which enables complex task decomposition, parallel execution, and specialized AI agents.

## Overview

The subagent system allows the main ClippyAgent to delegate complex subtasks to specialized AI agents, each with their own:

- **Specialized system prompts** optimized for specific task types
- **Filtered tool access** to ensure appropriate permissions
- **Isolated conversation history** for focused context
- **Independent execution** with timeout and iteration limits
- **Parallel processing** capabilities for independent tasks

## Available Subagent Types

### General Purpose

#### `general`

- **Purpose**: General-purpose tasks with full tool access
- **Tools**: All standard tools available
- **Max Iterations**: 25
- **Model**: Inherits from parent agent
- **Use Case**: When you need a generalist assistant with full capabilities

#### `fast_general`

- **Purpose**: Quick tasks requiring fast response
- **Tools**: Read-only tools (read_file, list_directory, search_files, get_file_info, grep)
- **Max Iterations**: 10
- **Model**: gpt-3.5-turbo (optimized for speed)
- **Use Case**: Simple lookups, file searches, quick information gathering

#### `power_analysis`

- **Purpose**: Deep analysis of complex systems
- **Tools**: All standard tools available
- **Max Iterations**: 40
- **Model**: claude-3-opus-20240229 (maximum capability)
- **Use Case**: Architecture analysis, complex design decisions, comprehensive reviews

### Specialized Tasks

#### `code_review`

- **Purpose**: Code quality analysis and review
- **Tools**: Read-only (read_file, read_files, grep, search_files, list_directory, get_file_info)
- **Max Iterations**: 15
- **Model**: Inherits from parent agent
- **Use Case**: Security analysis, code quality checks, best practices review

#### `testing`

- **Purpose**: Test generation and quality assurance
- **Tools**: Testing-focused (read_file, write_file, execute_command, search_files, grep, list_directory, get_file_info, create_directory)
- **Max Iterations**: 30
- **Model**: Inherits from parent agent
- **Use Case**: Unit test creation, integration testing, test coverage analysis

#### `refactor`

- **Purpose**: Code improvement and restructuring
- **Tools**: Refactoring tools (read_file, read_files, write_file, edit_file, search_files, grep, list_directory, get_file_info, create_directory)
- **Max Iterations**: 30
- **Model**: Inherits from parent agent
- **Use Case**: Code cleanup, performance optimization, design pattern implementation

#### `documentation`

- **Purpose**: Documentation creation and maintenance
- **Tools**: Documentation tools (read_file, read_files, write_file, search_files, grep, list_directory, get_file_info, create_directory)
- **Max Iterations**: 20
- **Model**: Inherits from parent agent
- **Use Case**: API docs, README files, code comments, tutorials

## Using Subagents

### Single Subagent Delegation

Use the `delegate_to_subagent` tool to create a single specialized subagent:

```python
{
    "task": "Review the authentication module for security vulnerabilities",
    "subagent_type": "code_review",
    "context": {
        "focus": "security",
        "exclude_patterns": ["test_*.py", "migrations/"],
        "critical_files": ["auth.py", "models.py"]
    },
    "timeout": 600,
    "max_iterations": 20
}
```

### Parallel Subagent Execution

Use the `run_parallel_subagents` tool to execute multiple subagents concurrently:

```python
{
    "subagents": [
        {
            "task": "Write comprehensive unit tests for the user service",
            "subagent_type": "testing",
            "context": {"module": "user_service", "coverage_target": 90}
        },
        {
            "task": "Generate API documentation for endpoints",
            "subagent_type": "documentation",
            "context": {"format": "openapi", "include_examples": True}
        },
        {
            "task": "Analyze database query performance",
            "subagent_type": "power_analysis",
            "context": {"focus": "performance", "slow_query_threshold": 100}
        }
    ],
    "max_concurrent": 3,
    "fail_fast": False,
    "aggregate_results": True
}
```

## Visual Indicators

Subagent activity is clearly marked with visual indicators to distinguish it from main agent operations:

### Console Output Prefixes

All subagent messages and tool calls are prefixed with `[subagent_type:name]` in cyan:

```
[code_review:security_check] Reading file: auth.py
[testing:test_gen] Writing file: test_auth.py
[general:task_1] Executing command: npm test
```

### Status Messages

#### Starting

```
╭─ Starting Subagent: security_check (code_review)
│ Task: Analyze authentication code for security vulnerabilities
╰─
```

#### Completion

```
✓ Subagent Complete: security_check (2.34s, 12 iterations)
```

#### Timeout

```
⏱ Subagent Timeout: slow_task (exceeded 300s limit)
```

#### Failure

```
✗ Subagent Failed: analysis_task (RuntimeError: Analysis incomplete)
```

### Benefits

- **Clear Attribution**: Immediately see which agent (main or subagent) is performing actions
- **Easy Debugging**: Track subagent execution flow and identify bottlenecks
- **Status Visibility**: Understand subagent progress and completion status
- **Type Identification**: Know which specialized subagent type is being used



If you encounter issues with subagent approvals, check the logs:

```bash
# List recent log files (newest first)
ls -lt ~/.clippy/logs/

# View the most recent log file
tail -100 ~/.clippy/logs/clippy-*.log | tail -100

# Or view a specific session's log
tail -100 ~/.clippy/logs/clippy-2025-10-20-143022.log
```

**Note**: Each clippy session creates a new timestamped log file. The system automatically keeps the 20 most recent log files and removes older ones.

Look for:

- `Error creating approval dialog:` - Issue during dialog initialization
- `Error mounting approval dialog:` - Issue during rendering
- Errors are also displayed in the conversation log for visibility

## Configuration

### Environment Variables

Configure subagent behavior using these environment variables:

```bash
# Parallel execution limits
export CLIPPY_MAX_CONCURRENT_SUBAGENTS=5

# Default timeout for all subagents (seconds)
export CLIPPY_SUBAGENT_TIMEOUT=600

# Result caching
export CLIPPY_SUBAGENT_CACHE_ENABLED=true
export CLIPPY_SUBAGENT_CACHE_SIZE=200
export CLIPPY_SUBAGENT_CACHE_TTL=7200

# Hierarchical execution
export CLIPPY_MAX_SUBAGENT_DEPTH=4
```

### Runtime Configuration

You can also configure subagents at runtime:

```python
# In your agent code
manager = SubAgentManager(
    parent_agent=agent,
    permission_manager=permission_manager,
    executor=executor,
    max_concurrent=5,
    enable_cache=True,
    enable_chaining=True
)

# Adjust cache settings
manager.get_cache_statistics()
manager.clear_cache()
manager.disable_cache()

# Adjust chaining settings
manager.get_chain_statistics()
manager.interrupt_chain("subagent_name")
```

### Model Configuration

Configure which model each subagent type uses with the `/subagent` command:

```bash
# List current configurations for all subagent types
/subagent list

# Set a specific model for a subagent type
/subagent set fast_general gpt-3.5-turbo
/subagent set power_analysis claude-3-opus-20240229
/subagent set code_review hf:zai-org/GLM-4.6

# Clear model override (revert to inheriting from parent)
/subagent clear fast_general

# Reset all model overrides
/subagent reset
```

**Model Selection Priority:**

1. **Explicit model in config** - If you pass a model when creating a subagent, that takes highest priority
2. **Type-specific override** - Model set via `/subagent set` for that subagent type
3. **Parent model** - Inherits the model from the parent agent (default)

**Configuration Storage:**
Model overrides are stored in `~/.clippy/subagent_config.json` and persist across sessions.

**Use Cases:**

- Use faster, cheaper models for simple tasks (`fast_general` → `gpt-3.5-turbo`)
- Use more capable models for complex analysis (`power_analysis` → `claude-3-opus-20240229`)
- Use specialized models per task type (e.g., coding models for refactoring)

## Advanced Features

### Result Caching

The subagent system includes intelligent result caching to avoid re-executing identical tasks:

- **Cache Key**: Generated from task description, subagent type, and context
- **TTL Support**: Configurable time-to-live for cached results
- **LRU Eviction**: Automatically removes oldest entries when cache is full
- **Statistics**: Track cache hit rates and memory usage

```python
# Check cache before creating subagent
cached_result = manager.check_cache(
    task="Review auth.py for security issues",
    subagent_type="code_review",
    context={"focus": "security"}
)

if cached_result:
    # Use cached result
    return cached_result
else:
    # Execute subagent and cache result
    result = subagent.run()
    manager.store_cache(task, subagent_type, result.to_dict(), context)
```

### Hierarchical Chaining

Subagents can spawn their own subagents for complex task decomposition:

- **Depth Limits**: Configurable maximum nesting depth (default: 3)
- **Tree Visualization**: Visual representation of execution hierarchy
- **Result Aggregation**: Combines results from parent and child subagents
- **Isolation**: Each level has isolated context and permissions

```python
# Example: Code review subagent spawns testing subagent
code_review_result = await manager.execute_chain(root_node)

# Visualize the execution tree
tree_viz = manager.visualize_chain("code_reviewer")
print(tree_viz)
```

## Best Practices

### Task Design

1. **Be Specific**: Clear, focused tasks perform better than vague requests
2. **Provide Context**: Include relevant files, focus areas, and constraints
3. **Set Appropriate Timeouts**: Complex tasks need more time, simple tasks should be quick
4. **Choose Right Type**: Match subagent type to task requirements

### Performance Optimization

1. **Use Caching**: Enable caching for repetitive tasks
2. **Parallel Execution**: Run independent subtasks concurrently
3. **Model Selection**: Use faster models for simple tasks, powerful models for complex analysis
4. **Iteration Limits**: Set reasonable iteration limits to prevent infinite loops

### Error Handling

1. **Fail Fast**: Use `fail_fast: True` for critical dependencies
2. **Result Aggregation**: Enable aggregation to see all results, even partial failures
3. **Timeout Management**: Set appropriate timeouts for task complexity
4. **Monitoring**: Track subagent statistics to identify bottlenecks

## Examples

### Example 1: Code Security Analysis

```python
# Main agent delegates to security specialist
{
    "task": "Perform comprehensive security analysis of the authentication system",
    "subagent_type": "code_review",
    "context": {
        "focus": "security",
        "checklist": [
            "SQL injection vulnerabilities",
            "Authentication bypass",
            "Session management",
            "Password hashing",
            "Input validation"
        ],
        "files": ["auth.py", "models.py", "views/auth.py"]
    },
    "timeout": 900,
    "max_iterations": 25
}
```

### Example 2: Parallel Test Generation

```python
# Generate tests for multiple modules in parallel
{
    "subagents": [
        {
            "task": "Generate unit tests for user management module",
            "subagent_type": "testing",
            "context": {
                "module": "user_management",
                "test_types": ["unit", "integration"],
                "coverage_target": 85
            }
        },
        {
            "task": "Generate API endpoint tests",
            "subagent_type": "testing",
            "context": {
                "module": "api",
                "test_types": ["endpoint", "authentication"],
                "coverage_target": 80
            }
        },
        {
            "task": "Generate database model tests",
            "subagent_type": "testing",
            "context": {
                "module": "models",
                "test_types": ["model", "migration"],
                "coverage_target": 90
            }
        }
    ],
    "max_concurrent": 3,
    "aggregate_results": True
}
```

### Example 3: Documentation and Refactoring

```python
# Sequential workflow: document then refactor
{
    "subagents": [
        {
            "task": "Document the current API structure and identify areas for improvement",
            "subagent_type": "documentation",
            "context": {"output_format": "markdown", "include_examples": True}
        },
        {
            "task": "Refactor API endpoints based on documentation analysis",
            "subagent_type": "refactor",
            "context": {
                "focus": "consistency",
                "apply_patterns": ["repository", "service"],
                "preserve_functionality": True
            }
        }
    ],
    "max_concurrent": 1,  # Sequential execution
    "aggregate_results": True
}
```

## Monitoring and Debugging

### Statistics

Monitor subagent performance:

```python
# Get execution statistics
stats = manager.get_statistics()
print(f"Success rate: {stats['success_rate']:.2%}")
print(f"Average execution time: {stats['avg_execution_time']:.2f}s")

# Get cache statistics
cache_stats = manager.get_cache_statistics()
print(f"Cache hit rate: {cache_stats.get('hit_rate', 0):.2%}")

# Get chain statistics
chain_stats = manager.get_chain_statistics()
print(f"Active chains: {chain_stats['active_chains']}")
```

### Debugging

Debug subagent execution:

```python
# View active subagents
active = manager.get_active_subagents()
for subagent in active:
    print(f"{subagent.config.name}: {subagent.get_status()}")

# View chain visualization
if manager.enable_chaining:
    for chain_name in manager.get_active_chains():
        print(manager.visualize_chain(chain_name))

# Interrupt problematic subagents
manager.interrupt_subagent("misbehaving_subagent")
```

## Troubleshooting

### Common Issues

1. **Subagent Timeouts**: Increase timeout or break down complex tasks
2. **Memory Usage**: Reduce cache size or enable cache cleanup
3. **Permission Errors**: Check tool permissions for subagent type
4. **Model Errors**: Verify model availability and API keys

### Performance Tuning

1. **Cache Optimization**: Adjust TTL and size based on usage patterns
2. **Concurrency Limits**: Balance between speed and resource usage
3. **Model Selection**: Use cost-effective models for appropriate tasks
4. **Iteration Limits**: Prevent infinite loops while allowing sufficient iterations

## API Reference

### SubAgentManager

```python
class SubAgentManager:
    def create_subagent(config: SubAgentConfig) -> SubAgent
    def run_sequential(subagents: List[SubAgent]) -> List[SubAgentResult]
    def run_parallel(subagents: List[SubAgent], max_concurrent: int) -> List[SubAgentResult]
    def get_statistics() -> Dict[str, Any]
    def get_cache_statistics() -> Dict[str, Any]
    def clear_cache() -> None
    def interrupt_subagent(name: str) -> bool
```

### SubAgentConfig

```python
@dataclass
class SubAgentConfig:
    name: str
    task: str
    subagent_type: str
    system_prompt: str | None = None
    allowed_tools: List[str] | None = None
    model: str | None = None
    max_iterations: int = 25
    timeout: int = 300
    context: Dict[str, Any] = field(default_factory=dict)
```

### SubAgentResult

```python
@dataclass
class SubAgentResult:
    success: bool
    output: str
    error: str | None
    iterations_used: int
    tokens_used: Dict[str, int]
    tools_executed: List[str]
    execution_time: float
    metadata: Dict[str, Any]
```

## Contributing

When contributing to the subagent system:

1. **Add Tests**: Include unit and integration tests for new features
2. **Update Documentation**: Keep this file and API docs current
3. **Consider Performance**: Optimize for memory usage and execution speed
4. **Error Handling**: Provide clear error messages and graceful failures
5. **Backward Compatibility**: Ensure changes don't break existing workflows
