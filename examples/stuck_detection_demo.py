#!/usr/bin/env python3
"""
Demo script showing the stuck subagent detection and recovery features.

This example demonstrates various ways to configure stuck detection
when running parallel subagents.
"""

import os
import sys

# Add the src directory to the path so we can import clippy modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from clippy.agent.subagent_utils import (
    analyze_parallel_results,
    create_stuck_detection_dict,
    get_quick_stuck_detection_settings,
    suggest_stuck_detection_settings,
)


def example_basic_stuck_detection():
    """Example of basic stuck detection configuration."""

    print("=== Basic Stuck Detection ===")

    # Simple enable/disable
    config = {
        "enabled": True,
        "stuck_timeout": 120,  # 2 minutes without progress
        "heartbeat_timeout": 60,  # 1 minute without heartbeat
        "overall_timeout": 600,  # 10 minutes total
        "auto_terminate": True,
        "check_interval": 10,  # Check every 10 seconds
    }

    print("Basic configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()


def example_preset_configurations():
    """Example of using preset configurations."""

    print("=== Preset Configurations ===")

    presets = get_quick_stuck_detection_settings()

    for name, config in presets.items():
        print(f"{name.title()} settings:")
        print(f"  enabled: {config['enabled']}")
        if config["enabled"]:
            print(f"  stuck_timeout: {config['stuck_timeout']}s")
            print(f"  heartbeat_timeout: {config['heartbeat_timeout']}s")
            print(f"  overall_timeout: {config['overall_timeout']}s")
        else:
            print("  stuck detection disabled")
        print()


def example_aggressive_vs_conservative():
    """Example comparing aggressive vs conservative settings."""

    print("=== Aggressive vs Conservative ===")

    aggressive = create_stuck_detection_dict(aggressive=True)
    conservative = create_stuck_detection_dict(conservative=True)

    print("Aggressive (fail-fast):")
    print(f"  stuck_timeout: {aggressive['stuck_timeout']}s")
    print(f"  heartbeat_timeout: {aggressive['heartbeat_timeout']}s")
    print(f"  overall_timeout: {aggressive['overall_timeout']}s")
    print(f"  check_interval: {aggressive['check_interval']}s")

    print("\nConservative (patient):")
    print(f"  stuck_timeout: {conservative['stuck_timeout']}s")
    print(f"  heartbeat_timeout: {conservative['heartbeat_timeout']}s")
    print(f"  overall_timeout: {conservative['overall_timeout']}s")
    print(f"  check_interval: {conservative['check_interval']}s")
    print()


def example_smart_suggestions():
    """Example of getting smart setting suggestions."""

    print("=== Smart Setting Suggestions ===")

    scenarios = [
        ("Simple, reliable tasks", {"task_complexity": "simple", "reliability": "high"}),
        ("Complex, unreliable tasks", {"task_complexity": "complex", "reliability": "low"}),
        ("Performance critical", {"performance_priority": True}),
        ("Balanced approach", {}),  # Default
    ]

    for description, params in scenarios:
        settings = suggest_stuck_detection_settings(**params)
        print(f"{description}:")
        print(f"  stuck_timeout: {settings['stuck_timeout']}s")
        print(f"  overall_timeout: {settings['overall_timeout']}s")
        if params.get("performance_priority"):
            print(f"  max_stuck_checks: {settings['max_stuck_checks']}")
        print()


def example_parallel_subagent_call():
    """Example of how to call run_parallel_subagents with stuck detection."""

    print("=== Parallel Subagent Call Example ===")

    # Example stuck detection config
    stuck_detection = create_stuck_detection_dict(
        aggressive=True,
        custom_settings={
            "overall_timeout": 300,  # 5 minutes max
            "check_interval": 5,  # Check every 5 seconds
        },
    )

    print("Example parallel subagent call:")
    print("  subagents: 3 tasks (codegen, testing, documentation)")
    print("  max_concurrent: 3")
    print("  stuck_detection:")
    print(f"    enabled: {stuck_detection['enabled']}")
    print(f"    stuck_timeout: {stuck_detection['stuck_timeout']}s")
    print(f"    overall_timeout: {stuck_detection['overall_timeout']}s")
    print(f"    check_interval: {stuck_detection['check_interval']}s")
    print()


def example_result_analysis():
    """Example of analyzing results from parallel execution."""

    print("=== Result Analysis Example ===")

    # Mock results from a parallel execution
    mock_results = {
        "individual_results": [
            {
                "name": "codegen_sub_1",
                "task": "Analyze code for security issues",
                "success": True,
                "execution_time": 85.0,
                "failure_reason": None,
            },
            {
                "name": "testing_sub_1",
                "task": "Generate unit tests",
                "success": False,
                "execution_time": 120.0,
                "failure_reason": "stuck",
            },
            {
                "name": "docs_sub_1",
                "task": "Update documentation",
                "success": True,
                "execution_time": 65.0,
                "failure_reason": None,
            },
        ],
        "total_successful": 2,
        "total_failed": 1,
        "total_stuck": 1,
        "total_timeout": 0,
        "total_exception": 0,
        "total_execution_time": 270.0,
        "stuck_detection_enabled": True,
    }

    analysis = analyze_parallel_results(mock_results)

    print("Analysis of parallel execution results:")
    print(f"  Total subagents: {analysis['total_subagents']}")
    print(f"  Success rate: {analysis['success_rate']:.1%}")
    print("\nIssues detected:")
    for issue in analysis["issues_detected"]:
        print(f"  • {issue}")
    print("\nRecommendations:")
    for rec in analysis["recommendations"]:
        print(f"  • {rec}")
    print()


def example_monitoring_scenario():
    """Example of a real-world monitoring scenario."""

    print("=== Real-world Monitoring Scenario ===")

    print("Scenario: Running 5 subagents to refactor different parts of a large codebase")
    print()

    # Choose appropriate settings based on the scenario
    settings = suggest_stuck_detection_settings(
        task_complexity="complex",  # Codebase refactoring is complex
        reliability="medium",  # Medium reliability for refactoring tasks
        performance_priority=False,  # Completion is more important than speed
    )

    print("Recommended stuck detection settings:")
    timeout_min = settings["stuck_timeout"] / 60
    heartbeat_min = settings["heartbeat_timeout"] / 60
    overall_min = settings["overall_timeout"] / 60
    print(f"  stuck_timeout: {settings['stuck_timeout']}s ({timeout_min:.1f} minutes)")
    print(f"  heartbeat_timeout: {settings['heartbeat_timeout']}s ({heartbeat_min:.1f} minutes)")
    print(f"  overall_timeout: {settings['overall_timeout']}s ({overall_min:.1f} minutes)")
    print(f"  check_interval: {settings['check_interval']}s")
    print(f"  auto_terminate: {settings['auto_terminate']}")
    print()

    print("Rationale:")
    print("• Conservative timeouts for complex refactoring tasks")
    print("• Frequent enough checking to detect genuine problems early")
    print("• Auto-terminate to preserve work from other subagents")
    print()

    # Example of what monitoring would show during execution
    print("Example monitoring output during execution:")
    print("  [INFO] Started monitoring 5 subagents")
    print("  [INFO] Subagent 'refactor_auth' completed successfully (45s)")
    print("  [INFO] Subagent 'refactor_api' completed successfully (67s)")
    print("  [WARNING] Subagent 'refactor_ui' appears stuck (no progress for 120s) - check 1/3")
    print("  [WARNING] Subagent 'refactor_ui' appears stuck (no progress for 180s) - check 2/3")
    print("  [ERROR] Taking action on stuck subagent 'refactor_ui': no progress for 300s")
    print("  [INFO] Interrupting stuck subagent 'refactor_ui'")
    print("  [INFO] Subagent 'refactor_database' completed successfully (89s)")
    print("  [INFO] Parallel execution completed: 4 succeeded, 1 stuck")
    print()


if __name__ == "__main__":
    print("📎 Clippy-code Stuck Detection Demo")
    print("=" * 50)
    print()

    example_basic_stuck_detection()
    example_preset_configurations()
    example_aggressive_vs_conservative()
    example_smart_suggestions()
    example_parallel_subagent_call()
    example_result_analysis()
    example_monitoring_scenario()

    print("✅ Demo completed! The stuck detection system helps you:")
    print("   • Detect when subagents get stuck")
    print("   • Preserve work from completed subagents")
    print("   • Get detailed reporting about what happened")
    print("   • Choose appropriate settings for your use case")
    print()
    print("📎 I'm practically paperclip-shaped with excitement about this improvement!")
