# Subagent Stuck Detection and Recovery

This document describes the stuck subagent detection and automatic recovery system in clippy-code.

## Overview

When running multiple subagents in parallel, sometimes one or more subagents can get stuck due to various reasons (e.g., long LLM responses, network issues, infinite loops). The stuck detection system monitors subagent progress and automatically handles stuck subagents while preserving work from completed ones.

## Features

- **Progress Monitoring**: Continuously monitors subagent execution via heartbeats
- **Stuck Detection**: Identifies subagents that haven't made progress or responded
- **Automatic Recovery**: Terminates stuck subagents and returns partial results
- **Configurable Timeouts**: Flexible timeout settings for different use cases
- **Detailed Reporting**: Provides clear information about what happened

## Basic Usage

Enable stuck detection when calling `run_parallel_subagents`:

```python
{
    "subagents": [
        {"task": "Analyze code", "subagent_type": "code_review"},
        {"task": "Write tests", "subagent_type": "testing"},
        {"task": "Update docs", "subagent_type": "documentation"}
    ],
    "stuck_detection": {
        "enabled": True,
        "stuck_timeout": 120,  # 2 minutes without progress
        "heartbeat_timeout": 60,  # 1 minute without heartbeat
        "overall_timeout": 600,  # 10 minutes total
        "auto_terminate": True,
        "check_interval": 10  # Check every 10 seconds
    }
}
```

## Configuration Options

### Core Settings

- **enabled**: Enable/disable stuck detection
- **stuck_timeout**: How long without progress before considering stuck (seconds)
- **heartbeat_timeout**: How long without heartbeat before considering stuck (seconds)
- **overall_timeout**: Maximum time for the entire parallel execution (seconds)
- **auto_terminate**: Automatically terminate stuck subagents
- **check_interval**: How often to check for stuck subagents (seconds)

### Default Values

```python
{
    "stuck_timeout": 120.0,      # 2 minutes without progress
    "heartbeat_timeout": 60.0,   # 1 minute without heartbeat
    "overall_timeout": 600.0,    # 10 minutes total
    "max_stuck_checks": 3,       # 3 checks before taking action
    "auto_terminate": True,      # Terminate stuck subagents
    "check_interval": 10.0,      # Check every 10 seconds
}
```

## Preset Configurations

### Aggressive (Quick Detection)
Use when performance is critical and tasks are simple:

```python
from src.clippy.agent.subagent_utils import create_stuck_detection_dict

stuck_detection = create_stuck_detection_dict(aggressive=True)
# Results in:
# {
#     "enabled": True,
#     "stuck_timeout": 60,
#     "heartbeat_timeout": 30,
#     "overall_timeout": 300,
#     "check_interval": 5
# }
```

### Conservative (Tolerant)
Use for complex tasks that might need more time:

```python
stuck_detection = create_stuck_detection_dict(conservative=True)
# Results in:
# {
#     "enabled": True,
#     "stuck_timeout": 300,
#     "heartbeat_timeout": 180,
#     "overall_timeout": 1800,
#     "check_interval": 15
# }
```

### Testing (Very Quick)
For automated testing where fast failure is desired:

```python
from src.clippy.agent.subagent_utils import get_quick_stuck_detection_settings

stuck_detection = get_quick_stuck_detection_settings()["testing"]
# Results in:
# {
#     "enabled": True,
#     "stuck_timeout": 30,
#     "heartbeat_timeout": 15,
#     "overall_timeout": 120,
#     "check_interval": 3
# }
```

## Smart Settings Suggestions

Get automatically suggested settings based on your task characteristics:

```python
from src.clippy.agent.subagent_utils import suggest_stuck_detection_settings

# Simple, reliable tasks
settings = suggest_stuck_detection_settings(
    task_complexity="simple",
    reliability="high"
)

# Complex, potentially unreliable tasks
settings = suggest_stuck_detection_settings(
    task_complexity="complex", 
    reliability="low"
)

# Performance-critical tasks
settings = suggest_stuck_detection_settings(performance_priority=True)
```

## Result Analysis

After parallel execution completes, analyze the results:

```python
from src.clippy.agent.subagent_utils import analyze_parallel_results

analysis = analyze_parallel_results(results)
print(f"Success rate: {analysis['success_rate']:.1%}")
print("Issues detected:", analysis['issues_detected'])
print("Recommendations:", analysis['recommendations'])
```

The analysis will identify:
- Success rate and failure patterns
- Subagents that got stuck or timed out
- Performance bottlenecks
- Recommendations for improvement

## How It Works

### 1. Monitoring Process
- A dedicated monitor thread tracks all active subagents
- Each subagent sends periodic "heartbeats" during execution
- The monitor checks for progress and response patterns

### 2. Stuck Detection Logic
A subagent is considered stuck when:
- No heartbeat received within `heartbeat_timeout`
- No progress (no iteration changes) within `stuck_timeout`
- Overall execution time exceeds `overall_timeout`
- Multiple consecutive stuck checks fail

### 3. Recovery Actions
When stuck is detected:
1. **Warning**: Log warning messages
2. **Interrupt**: Send interrupt signal to subagent
3. **Terminate**: If auto_terminate is enabled, force termination
4. **Recover**: Continue with other subagents and return partial results

### 4. Result Preservation
- Completed subagent results are preserved
- Stuck subagents return special "stuck" error results
- Overall execution continues with remaining work
- Detailed reporting explains what happened

## Example Scenarios

### Scenario 1: One Subagent Gets Stuck
```python
# 3 subagents, 1 gets stuck after 45 seconds
results = run_parallel_subagents(
    subagents=[...],
    stuck_detection={"enabled": True, "stuck_timeout": 60}
)

# Result:
# - 2 subagents completed successfully
# - 1 subagent marked as "stuck"
# - Partial results returned with clear status
```

### Scenario 2: Performance Optimization
```python
# Multiple quick tasks, fail fast on problems
results = run_parallel_subagents(
    subagents=[...],
    stuck_detection=create_stuck_detection_dict(aggressive=True)
)

# Result:
# - Problems detected within 30 seconds
# - Stuck subagents quickly terminated
# - Overall execution minimized
```

### Scenario 3: Complex Analysis Tasks
```python
# Long-running analysis tasks, be patient
results = run_parallel_subagents(
    subagents=[...],
    stuck_detection=create_stuck_detection_dict(conservative=True)
)

# Result:
# - Allows up to 30 minutes execution
# - Only intervenes on genuine problems
# - Best for complex, time-consuming tasks
```

## Monitoring Information

The system provides detailed monitoring information:

```python
# During execution, check current status
stuck = monitor.get_stuck_subagents()
stats = monitor.get_statistics()

print(f"Active: {stats['running']}, Completed: {stats['completed']}")
print(f"Stuck detected: {stats['stuck_detected']}")
print(f"Recovered: {stats['recovered']}")
```

## Best Practices

### 1. Choose Appropriate Timeouts
- **Simple tasks**: Use aggressive settings (30-60s timeouts)
- **Complex tasks**: Use conservative settings (5-30 min timeouts)
- **Unknown complexity**: Start with default, adjust based on results

### 2. Monitor and Adjust
```python
# Analyze first run
analysis = analyze_parallel_results(results)

# If many stuck:
if "stuck" in str(analysis):
    # Try conservative settings
    stuck_detection = create_stuck_detection_dict(conservative=True)

# If too slow:
if analysis.get("avg_execution_time", 0) > expected_time:
    # Try aggressive settings
    stuck_detection = create_stuck_detection_dict(aggressive=True)
```

### 3. Handle Results Properly
```python
for result in results["individual_results"]:
    if result["success"]:
        # Process successful result
        process_result(result["output"])
    elif result["failure_reason"] == "stuck":
        # Handle stuck case - maybe retry manually
        logger.warning(f"Subagent {result['name']} got stuck")
    else:
        # Handle other failures
        logger.error(f"Subagent {result['name']} failed: {result['error']}")
```

## Troubleshooting

### Subagents Keep Getting Stuck
1. **Increase timeouts**: Use conservative settings
2. **Check the tasks**: Are they overly complex or ambiguous?
3. **Network issues**: Check API connectivity and rate limits
4. **Prompt issues**: Review subagent prompts for clarity

### Stuck Detection Too Slow
1. **Decrease timeouts**: Use aggressive settings
2. **More frequent checks**: Lower `check_interval`
3. **Fewer stuck checks**: Lower `max_stuck_checks`

### Too Many False Positives
1. **Increase timeouts**: Subagents need more time
2. **Task partitioning**: Break complex tasks into smaller ones
3. **Individual timeouts**: Set per-subagent timeouts in addition to global

## Environment Variables

Configure defaults via environment variables:

```bash
export CLIPPY_STUCK_DETECTION_ENABLED=true
export CLIPPY_DEFAULT_STUCK_TIMEOUT=120
export CLIPPY_DEFAULT_HEARTBEAT_TIMEOUT=60
export CLIPPY_DEFAULT_OVERALL_TIMEOUT=600
export CLIPPY_AUTO_TERMINATE_STUCK=true
```

## Integration with Caching

Stuck detection works seamlessly with subagent caching:
- Stuck subagents won't cache bad results
- Completed subagents cache as normal
- Failed/stuck subagents can be retried with different settings

## Future Enhancements

Planned improvements:
- **Automatic retry**: Configure automatic retries for stuck subagents
- **Progressive timeouts**: Dynamically adjust timeouts based on task complexity
- **Machine learning detection**: Learn patterns to predict stuck subagents
- **Resource monitoring**: Detect stuck based on CPU/memory usage patterns
- **Graceful degradation**: Automatically reduce parallelism when issues detected