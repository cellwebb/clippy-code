#!/usr/bin/env python3
"""
Demonstration script for PR-level analysis in clippy.

This script shows how to use the new git_analyzer and pr_manager tools
to analyze the exact scenario described:

main M (monolith)
 -> primary feature F
   -> subfeatureA
   -> subfeatureB

mobile (react native)
  -> primary feature F'1

Analyzing commits in B as they might affect:
- F (parent feature)
- A (sibling subfeature)
- M (main monolith)
- F'1 (mobile feature)
"""

import json
import sys
from pathlib import Path

# Add src to path so we can import clippy modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from clippy.tools.git_analyzer import git_analyzer
from clippy.tools.pr_manager import pr_manager


def demonstrate_b_branch_analysis(use_llm=False):
    """
    Demonstrate analysis of subfeatureB changes and their impact on:
    - subfeatureA (sibling)
    - featureF (parent)
    - main (monolith)
    - mobile/F1 (parallel mobile development)
    """

    print("📎 Clippy PR Analysis Demo!")
    print("=" * 60)
    print("Scenario: Analyzing subfeatureB changes for cross-branch impacts")
    print()

    # Configure your repository path here
    repo_path = "."  # Change to your git repository path

    # Define the branch structure
    base_branch = "main"  # M - main monolith
    feature_branch = "feature/subfeatureB"  # B - source of changes

    # Context branches to analyze impact on
    context_branches = [
        "feature/subfeatureA",  # A - sibling subfeature
        "feature/primaryFeatureF",  # F - parent feature
        "mobile/primaryFeatureF1",  # F'1 - mobile parallel feature
    ]

    print("🔍 Analyzing cross-branch impacts...")
    print(f"Source: {feature_branch}")
    print(f"Target: {base_branch}")
    print(f"Context branches: {', '.join(context_branches)}")
    print()

    # 1. Comprehensive git analysis
    print("=" * 40)
    print("1. GIT ANALYSIS")
    print("=" * 40)

    intelligence_level = "smart" if use_llm else "fast"
    print(f"🧠 Using intelligence level: {intelligence_level}")
    print()

    success, message, git_result = git_analyzer(
        base_branch=base_branch,
        feature_branch=feature_branch,
        compare_branches=context_branches,
        repo_path=repo_path,
        analysis_depth="files",
        include_semantic_analysis=True,
        intelligence_level=intelligence_level,
    )

    if success:
        print("✅ Git analysis completed!\n")

        # Display summary
        if "summary" in git_result:
            print("📊 IMPACT SUMMARY:")
            print(git_result["summary"])
            print()

        # Display impacts on each branch
        print("🎯 BRANCH IMPACTS:")
        for branch, impact in git_result.get("impacts", {}).items():
            risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                impact.get("risk_level", "low"), "⚪"
            )
            print(f"  {branch}: {risk_emoji} {impact.get('risk_level', 'unknown').upper()}")
            print(f"    Files affected: {impact.get('file_count', 0)}")
            print(f"    Lines modified: {impact.get('line_count', 0)}")
            print(f"    Areas impacted: {', '.join(impact.get('affected_areas', []))}")
            print()

        # Display collision analysis
        if git_result.get("collisions"):
            print("⚠️  COLLISION RISKS:")
            for collision in git_result["collisions"]:
                branch = collision["branch"]
                analysis = collision["analysis"]
                risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    analysis.get("collision_risk", "low"), "⚪"
                )
                print(
                    f"  {branch}: {risk_emoji} {analysis.get('collision_risk', 'unknown').upper()}"
                )
                print(f"    Conflicting files: {len(analysis.get('conflicting_files', []))}")
                if analysis.get("divergence_point"):
                    print(f"    Divergence point: {analysis['divergence_point'][:8]}...")
                print()

        # Display semantic analysis if available
        if "semantic_analysis" in git_result:
            semantic = git_result["semantic_analysis"]
            print("🧠 SEMANTIC ANALYSIS:")
            print(f"  Impact score: {semantic.get('semantic_impact_score', 0):.2f}")
            if semantic.get("api_changes"):
                print(f"  API changes: {len(semantic['api_changes'])}")
            if semantic.get("data_model_changes"):
                print(f"  Data model changes: {len(semantic['data_model_changes'])}")
            if semantic.get("dependency_changes"):
                print(f"  Dependency changes: {len(semantic['dependency_changes'])}")
            print()

        # Display LLM analysis if available
        if "llm_analysis" in git_result and "error" not in git_result["llm_analysis"]:
            llm_analysis = git_result["llm_analysis"]
            print("🤖 LLM-ENHANCED ANALYSIS:")
            print(f"  Intelligence level: {llm_analysis.get('intelligence_level', 'unknown')}")
            print(f"  Model used: {llm_analysis.get('model_used', 'unknown')}")

            # Show breaking changes
            code_analysis = llm_analysis.get("code_analysis", {})
            if code_analysis.get("breaking_changes"):
                print("  🚨 BREAKING CHANGES DETECTED:")
                for change in code_analysis["breaking_changes"][:3]:  # Top 3
                    severity = change.get("severity", "unknown")
                    file = change.get("file", "unknown")
                    desc = change.get("description", "unknown")
                    emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")
                    print(f"    {emoji} {file}: {desc}")

            # Show coordination requirements
            if "business_impact" in llm_analysis:
                business = llm_analysis["business_impact"]
                risk = business.get("business_risk", "unknown")
                if risk != "low":
                    emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(risk, "⚪")
                    print(f"  🏢 Business risk: {emoji} {risk.upper()}")

            print()

        # Display recommendations
        if git_result.get("recommendations"):
            print("💡 RECOMMENDATIONS:")
            for rec in git_result["recommendations"]:
                print(f"  {rec}")
            print()

    else:
        print(f"❌ Git analysis failed: {message}")
        return

    # 2. PR Management validation
    print("=" * 40)
    print("2. PR MANAGEMENT VALIDATION")
    print("=" * 40)

    success, message, pr_result = pr_manager(
        action="validate",
        source_branch=feature_branch,
        target_branch=base_branch,
        context_branches=context_branches,
        repo_path=repo_path,
        safety_level="moderate",  # Options: strict, moderate, permissive
        include_tests=True,
        intelligence_level=intelligence_level,
    )

    if success:
        print("✅ PR validation completed!\n")

        # Overall safety assessment
        overall_safe = pr_result.get("overall_safe", False)
        score = pr_result.get("score", 0)
        max_score = pr_result.get("max_score", 10)

        status_icon = "✅" if overall_safe else "⚠️"
        print(f"{status_icon} OVERALL SAFETY: {'SAFE' if overall_safe else 'REQUIRES ATTENTION'}")
        print(f"   Score: {score:.1f}/{max_score}")
        print()

        # Show check results
        print("🔍 SAFETY CHECKS:")
        for check_name, passed in pr_result.get("checks", {}).items():
            icon = "✅" if passed else "❌"
            print(f"  {icon} {check_name}")
        print()

        # Show blockers
        if pr_result.get("blocking_issues"):
            print("🚫 BLOCKING ISSUES:")
            for issue in pr_result["blocking_issues"]:
                print(f"  • {issue}")
            print()

        # Show recommendations
        if pr_result.get("recommendations"):
            print("💡 RECOMMENDATIONS:")
            for rec in pr_result["recommendations"]:
                print(f"  • {rec}")
            print()

        # Display LLM PR analysis if available
        if "llm_pr_analysis" in pr_result and "error" not in pr_result["llm_pr_analysis"]:
            llm_pr_analysis = pr_result["llm_pr_analysis"]
            print("🤖 LLM-ENHANCED PR ANALYSIS:")
            print(f"  Intelligence level: {llm_pr_analysis.get('intelligence_level', 'unknown')}")

            # Show commit quality
            commit_quality = llm_pr_analysis.get("commit_quality", {})
            if commit_quality:
                quality = commit_quality.get("overall_quality", "unknown")
                score = commit_quality.get("score", 0)
                quality_emoji = {"excellent": "🌟", "good": "✅", "fair": "🟡", "poor": "🔴"}.get(
                    quality, "⚪"
                )
                print(
                    f"  📝 Commit quality: {quality_emoji} {quality.capitalize()} "
                    + f"(Score: {score:.1f}/10)"
                )

            # Show enhanced recommendations
            enhanced_recs = llm_pr_analysis.get("enhanced_recommendations", [])
            if enhanced_recs:
                print("  🧠 Enhanced insights:")
                for rec in enhanced_recs[:3]:  # Top 3
                    print(f"    {rec}")

            print()

    else:
        print(f"❌ PR validation failed: {message}")

    # 3. Collision-focused analysis
    print("=" * 40)
    print("3. DETAILED COLLISION ANALYSIS")
    print("=" * 40)

    success, message, collision_result = pr_manager(
        action="collision_check",
        source_branch=feature_branch,
        target_branch=base_branch,
        context_branches=context_branches,
        repo_path=repo_path,
    )

    if success:
        print("✅ Collision analysis completed!\n")

        overall_severity = collision_result.get("collision_severity", "low")
        severity_emoji = {"critical": "🚨", "high": "🔴", "medium": "🟡", "low": "🟢"}.get(
            overall_severity, "⚪"
        )
        print(f"{severity_emoji} OVERALL COLLISION SEVERITY: {overall_severity.upper()}")
        print()

        collisions = collision_result.get("collision_analysis", {})
        for branch, analysis in collisions.items():
            severity = analysis.get("severity", "low")
            severity_icon = {"critical": "🚨", "high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                severity, "⚪"
            )

            print(f"  {branch}: {severity_icon} {severity.upper()}")
            print(f"    Merge complexity: {analysis.get('merge_complexity', 'unknown')}")
            print(f"    Conflicting files: {len(analysis.get('conflicting_files', []))}")

            if analysis.get("conflicting_files"):
                print("    Conflicting file list:")
                for file in analysis["conflicting_files"][:5]:  # Show first 5
                    print(f"      - {file}")
                if len(analysis["conflicting_files"]) > 5:
                    print(f"      ... and {len(analysis['conflicting_files']) - 5} more")

            if analysis.get("recommendations"):
                print("    Recommendations:")
                for rec in analysis["recommendations"]:
                    print(f"      • {rec}")
            print()

    print("=" * 60)
    print("📎 Analysis complete! 📎")
    print("Use this information to make informed decisions about")
    print("whether to proceed with merging subfeatureB changes.")
    print("=" * 60)


def interactive_analysis():
    """Interactive mode for custom branch analysis."""
    print("📎 Interactive PR Analysis Mode")
    print("=" * 40)

    repo_path = input("Enter repository path (default: .): ").strip() or "."
    source_branch = input("Enter source/feature branch: ").strip()
    target_branch = input("Enter target branch: ").strip()

    context_input = input("Enter context branches (comma-separated, or leave empty): ").strip()
    context_branches = [b.strip() for b in context_input.split(",")] if context_input else []

    safety_level = (
        input("Safety level (strict/moderate/permissive, default: moderate): ").strip()
        or "moderate"
    )

    print(f"\n🔍 Analyzing {source_branch} → {target_branch}...")
    if context_branches:
        print(f"Context branches: {', '.join(context_branches)}")

    # Ask if user wants LLM enhancement
    use_llm_input = input("Use LLM enhancement? (y/N, default: N): ").strip().lower()
    use_llm = use_llm_input in ["y", "yes"]
    intelligence_level = "smart" if use_llm else "fast"

    print(f"\n🔍 Analyzing {source_branch} → {target_branch}...")
    print(f"🧠 Intelligence level: {intelligence_level}")
    if context_branches:
        print(f"Context branches: {', '.join(context_branches)}")

    success, message, result = pr_manager(
        action="analyze",
        source_branch=source_branch,
        target_branch=target_branch,
        context_branches=context_branches,
        repo_path=repo_path,
        safety_level=safety_level,
        intelligence_level=intelligence_level,
    )

    if success:
        # Save detailed results to file
        output_file = (
            f"pr_analysis_{source_branch.replace('/', '_')}_{target_branch.replace('/', '_')}.json"
        )
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n✅ Analysis saved to {output_file}")

        # Show brief summary
        if "summary" in result:
            print(f"\n📊 Summary:\n{result['summary']}")
    else:
        print(f"\n❌ Analysis failed: {message}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "interactive":
            interactive_analysis()
        elif sys.argv[1] == "llm":
            demonstrate_b_branch_analysis(use_llm=True)
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Clippy PR Analysis Demo")
            print("========================")
            print("Usage:")
            print("  python examples/pr_analysis_demo.py           # Fast, rule-based analysis")
            print("  python examples/pr_analysis_demo.py llm      # Smart, LLM-enhanced analysis")
            print("  python examples/pr_analysis_demo.py interactive  # Interactive mode")
            print()
    else:
        demonstrate_b_branch_analysis()
