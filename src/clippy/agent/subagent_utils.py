"""Utility functions for subagent management and monitoring."""

import logging
from typing import Any

from .subagent_monitor import StuckDetectionConfig

logger = logging.getLogger(__name__)


def create_stuck_detection_config(
    enabled: bool = True,
    aggressive: bool = False,
    conservative: bool = False,
    custom_settings: dict[str, Any] | None = None,
) -> StuckDetectionConfig:
    """
    Create a StuckDetectionConfig with preset or custom settings.

    Args:
        enabled: Whether stuck detection is enabled
        aggressive: Use aggressive (shorter timeout) settings
        conservative: Use conservative (longer timeout) settings
        custom_settings: Override specific settings

    Returns:
        Configured StuckDetectionConfig
    """
    if aggressive and conservative:
        raise ValueError("Cannot specify both aggressive and conservative")

    if aggressive:
        # Aggressive settings - detect problems quickly
        base_config = {
            "stuck_timeout": 60.0,  # 1 minute without progress
            "heartbeat_timeout": 30.0,  # 30 seconds without heartbeat
            "overall_timeout": 300.0,  # 5 minutes overall
            "max_stuck_checks": 2,  # Fewer checks before action
            "auto_retry": True,
            "max_retries": 2,
            "auto_terminate": True,
            "check_interval": 5.0,  # Check every 5 seconds
        }
    elif conservative:
        # Conservative settings - allow more time
        base_config = {
            "stuck_timeout": 300.0,  # 5 minutes without progress
            "heartbeat_timeout": 180.0,  # 3 minutes without heartbeat
            "overall_timeout": 1800.0,  # 30 minutes overall
            "max_stuck_checks": 5,  # More checks before action
            "auto_retry": True,
            "max_retries": 3,
            "auto_terminate": True,
            "check_interval": 15.0,  # Check every 15 seconds
        }
    else:
        # Default balanced settings
        base_config = {
            "stuck_timeout": 120.0,  # 2 minutes without progress
            "heartbeat_timeout": 60.0,  # 1 minute without heartbeat
            "overall_timeout": 600.0,  # 10 minutes overall
            "max_stuck_checks": 3,
            "auto_retry": True,
            "max_retries": 2,
            "auto_terminate": True,
            "check_interval": 10.0,
        }

    # Apply custom overrides
    if custom_settings:
        base_config.update(custom_settings)

    # Build config with proper type conversion
    config = StuckDetectionConfig(
        stuck_timeout=float(base_config["stuck_timeout"]),
        heartbeat_timeout=float(base_config["heartbeat_timeout"]),
        max_stuck_checks=int(base_config["max_stuck_checks"]),
        overall_timeout=float(base_config["overall_timeout"]),
        auto_retry=bool(base_config["auto_retry"]),
        max_retries=int(base_config["max_retries"]),
        auto_terminate=bool(base_config["auto_terminate"]),
        check_interval=float(base_config["check_interval"]),
    )
    return config


def create_stuck_detection_dict(
    enabled: bool = True,
    aggressive: bool = False,
    conservative: bool = False,
    custom_settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a dictionary representation for the run_parallel_subagents tool.

    Args:
        enabled: Whether stuck detection is enabled
        aggressive: Use aggressive (shorter timeout) settings
        conservative: Use conservative (longer timeout) settings
        custom_settings: Override specific settings

    Returns:
        Dictionary ready to pass to run_parallel_subagents
    """
    config = create_stuck_detection_config(enabled, aggressive, conservative, custom_settings)
    return {
        "enabled": enabled,
        "stuck_timeout": config.stuck_timeout,
        "heartbeat_timeout": config.heartbeat_timeout,
        "overall_timeout": config.overall_timeout,
        "auto_terminate": config.auto_terminate,
        "check_interval": config.check_interval,
        "max_stuck_checks": config.max_stuck_checks,
    }


def get_quick_stuck_detection_settings() -> dict[str, Any]:
    """
    Get quick settings for common stuck detection scenarios.

    Returns:
        Dictionary with preset configurations
    """
    return {
        "disabled": {"enabled": False},
        "conservative": create_stuck_detection_dict(conservative=True),
        "balanced": create_stuck_detection_dict(aggressive=False, conservative=False),
        "aggressive": create_stuck_detection_dict(aggressive=True),
        "testing": create_stuck_detection_dict(
            aggressive=True,
            custom_settings={
                "stuck_timeout": 30.0,
                "heartbeat_timeout": 15.0,
                "overall_timeout": 120.0,
                "check_interval": 3.0,
            },
        ),
    }


def analyze_parallel_results(results: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze results from parallel subagent execution.

    Args:
        results: Results dictionary from run_parallel_subagents

    Returns:
        Analysis dictionary with insights
    """
    if not isinstance(results, dict) or "individual_results" not in results:
        return {"error": "Invalid results format"}

    individual = results["individual_results"]
    issues_detected: list[str] = []
    recommendations: list[str] = []

    analysis: dict[str, Any] = {
        "total_subagents": len(individual),
        "success_rate": results.get("total_successful", 0) / len(individual) if individual else 0,
        "issues_detected": issues_detected,
        "recommendations": recommendations,
    }

    # Check for common issues
    if results.get("total_stuck", 0) > 0:
        stuck_count = results["total_stuck"]
        analysis["issues_detected"].append(
            f"{stuck_count} subagent(s) got stuck and were terminated"
        )
        if stuck_count > len(individual) // 2:
            analysis["recommendations"].append(
                "Consider using conservative stuck detection settings or longer timeouts"
            )
        else:
            analysis["recommendations"].append(
                "Stuck detection successfully preserved work from other subagents"
            )

    if results.get("total_timeout", 0) > 0:
        timeout_count = results["total_timeout"]
        analysis["issues_detected"].append(f"{timeout_count} subagent(s) timed out")
        analysis["recommendations"].append("Consider increasing individual subagent timeouts")

    if results.get("total_exception", 0) > 0:
        exception_count = results["total_exception"]
        analysis["issues_detected"].append(f"{exception_count} subagent(s) failed with exceptions")

    # Performance analysis
    total_time = results.get("total_execution_time", 0)
    if total_time > 600:  # More than 10 minutes
        analysis["recommendations"].append("Consider breaking down the task into smaller subtasks")

    # Check execution patterns
    execution_times = [r.get("execution_time", 0) for r in individual]
    if execution_times:
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)

        # Check if one subagent dominated the execution time
        if max_time > avg_time * 3:
            slowest_subagent = max(individual, key=lambda r: r.get("execution_time", 0))
            analysis["issues_detected"].append(
                f"Subagent '{slowest_subagent.get('name', 'unknown')}' took "
                + f"{max_time:.1f}s vs average {avg_time:.1f}s"
            )
            analysis["recommendations"].append(
                "Consider optimizing the slow subagent or running it separately"
            )

    return analysis


def suggest_stuck_detection_settings(
    task_complexity: str = "medium",
    reliability: str = "medium",
    performance_priority: bool = False,
) -> dict[str, Any]:
    """
    Suggest stuck detection settings based on task characteristics.

    Args:
        task_complexity: "simple", "medium", or "complex"
        reliability: "high", "medium", or "low" (how reliable the subagents are)
        performance_priority: Whether performance is more important than completion

    Returns:
        Recommended stuck detection settings
    """
    # Base settings on complexity and reliability
    if task_complexity == "simple" and reliability == "high":
        # Fast tasks that usually work well
        return create_stuck_detection_dict(
            aggressive=True, custom_settings={"overall_timeout": 180.0}
        )
    elif task_complexity == "complex" and reliability == "low":
        # Complex, potentially unreliable tasks
        return create_stuck_detection_dict(
            conservative=True,
            custom_settings={"overall_timeout": 2400.0},  # 40 minutes
        )
    elif performance_priority:
        # Performance is critical, fail fast
        return create_stuck_detection_dict(
            aggressive=True, custom_settings={"auto_terminate": True, "max_stuck_checks": 2}
        )
    else:
        # Standard balanced approach
        return create_stuck_detection_dict()
