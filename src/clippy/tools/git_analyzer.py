"""Git repository analysis tool for PR-level impact assessment."""

from pathlib import Path
from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "git_analyzer",
        "description": (
            "Analyze git changes across branches for PR-level impact assessment. "
            "Detects potential collisions and impacts on other branches/contexts. "
            "Optional LLM enhancement for deeper analysis of breaking changes and "
            "coordination needs."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "base_branch": {
                    "type": "string",
                    "description": (
                        "The main/base branch to compare against (e.g., 'main', 'master', 'M')"
                    ),
                },
                "feature_branch": {
                    "type": "string",
                    "description": (
                        "The feature branch being analyzed (e.g., 'feature/subfeatureB')"
                    ),
                },
                "compare_branches": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "List of additional branches to compare against "
                        "(e.g., ['feature/subfeatureA', 'mobile/F1'])"
                    ),
                },
                "repo_path": {
                    "type": "string",
                    "description": "Path to the git repository (defaults to current directory)",
                    "default": ".",
                },
                "analysis_depth": {
                    "type": "string",
                    "enum": ["commits", "files", "functions", "full"],
                    "description": (
                        "Depth of analysis: 'commits' (basic), 'files' (file-level changes), "
                        "'functions' (function-level analysis), 'full' (deep semantic analysis)"
                    ),
                    "default": "files",
                },
                "include_semantic_analysis": {
                    "type": "boolean",
                    "description": (
                        "Whether to perform semantic impact analysis "
                        "(requires more processing time)"
                    ),
                    "default": True,
                },
                "intelligence_level": {
                    "type": "string",
                    "enum": ["fast", "smart", "deep"],
                    "description": (
                        "Intelligence level: 'fast' (rule-based, no LLM), "
                        "'smart' (LLM-enhanced key analysis), "
                        "'deep' (comprehensive LLM analysis with coordination planning)"
                    ),
                    "default": "fast",
                },
                "llm_model": {
                    "type": "string",
                    "description": (
                        "Specific LLM model to use for analysis (uses default if not specified)"
                    ),
                    "default": None,
                },
            },
            "required": ["base_branch", "feature_branch"],
        },
    },
}


def git_analyzer(
    base_branch: str,
    feature_branch: str,
    compare_branches: list[str] | None = None,
    repo_path: str = ".",
    analysis_depth: str = "files",
    include_semantic_analysis: bool = True,
    intelligence_level: str = "fast",
    llm_model: str | None = None,
) -> tuple[bool, str, Any]:
    """
    Analyze git changes across branches for PR-level impact assessment.

    This function helps your friend's use case by:
    - Analyzing how commits in feature_branch might affect base_branch
    - Detecting potential collisions with compare_branches
    - Identifying semantic changes that could impact other contexts

    Intelligence levels:
    - 'fast': Rule-based analysis only (no LLM, quick and free)
    - 'smart': LLM-enhanced breaking change detection and coordination analysis
    - 'deep': Comprehensive LLM analysis with coordination planning and business impact
    """
    import os
    import subprocess

    try:
        # Validate repository path
        repo_path_obj = Path(repo_path).resolve()
        if not os.path.exists(repo_path_obj):
            return False, f"Repository path does not exist: {repo_path}", None

        # Check if it's a git repository
        git_dir = repo_path_obj / ".git"
        if not git_dir.exists():
            return False, f"Not a git repository: {repo_path}", None

        # Initialize result structure
        analysis_result: dict[str, Any] = {
            "repository": str(repo_path_obj),
            "base_branch": base_branch,
            "feature_branch": feature_branch,
            "compare_branches": compare_branches or [],
            "analysis_depth": analysis_depth,
            "intelligence_level": intelligence_level,
            "timestamp": str(subprocess.check_output(["date"], cwd=repo_path_obj).decode().strip()),
            "impacts": {},
            "collisions": [],
            "recommendations": [],
            "llm_enhanced": intelligence_level in ["smart", "deep"],
        }

        # Helper function to run git commands
        def run_git(command: list[str]) -> tuple[bool, str, str]:
            try:
                result = subprocess.run(
                    ["git"] + command, cwd=repo_path_obj, capture_output=True, text=True, timeout=30
                )
                return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
            except subprocess.TimeoutExpired:
                return False, "", "Command timed out"
            except Exception as e:
                return False, "", str(e)

        # Verify branches exist
        for branch in [base_branch, feature_branch] + (compare_branches or []):
            success, _, stderr = run_git(["rev-parse", "--verify", f"origin/{branch}"])
            if not success:
                success, _, stderr = run_git(["rev-parse", "--verify", branch])
                if not success:
                    return False, f"Branch '{branch}' not found in repository", None

        # Get changes in feature branch relative to base
        success, diff_output, _ = run_git(
            ["diff", f"{base_branch}...{feature_branch}", "--name-status"]
        )
        if not success:
            return False, f"Failed to get diff between {base_branch} and {feature_branch}", None

        # Parse file changes
        file_changes = {}
        for line in diff_output.split("\n"):
            if line.strip():
                parts = line.split("\t")
                if len(parts) >= 2:
                    status = parts[0]
                    filepath = parts[1]
                    file_changes[filepath] = status

        analysis_result["changed_files"] = file_changes

        # Analyze impacts on base branch
        base_impact = analyze_branch_impact(
            repo_path_obj, base_branch, feature_branch, analysis_depth
        )
        analysis_result["impacts"][base_branch] = base_impact

        # Analyze collisions with compare branches
        if compare_branches:
            for compare_branch in compare_branches:
                collision_analysis = detect_branch_collisions(
                    repo_path_obj, feature_branch, compare_branch
                )
                analysis_result["collisions"].append(
                    {"branch": compare_branch, "analysis": collision_analysis}
                )

                # Also analyze impact on compare branch
                compare_impact = analyze_branch_impact(
                    repo_path_obj, compare_branch, feature_branch, analysis_depth
                )
                analysis_result["impacts"][compare_branch] = compare_impact

        # Perform semantic analysis if requested
        if include_semantic_analysis and analysis_depth in ["functions", "full"]:
            semantic_impact = analyze_semantic_changes(
                repo_path_obj, base_branch, feature_branch, file_changes
            )
            analysis_result["semantic_analysis"] = semantic_impact

        # Perform LLM-enhanced analysis if requested
        if intelligence_level in ["smart", "deep"]:
            llm_analysis = perform_llm_enhanced_analysis(
                repo_path_obj,
                base_branch,
                feature_branch,
                compare_branches or [],
                intelligence_level,
                llm_model,
            )
            analysis_result["llm_analysis"] = llm_analysis

            # Merge LLM insights into recommendations
            if "error" not in llm_analysis:
                merge_llm_recommendations(analysis_result, llm_analysis)

        # Generate recommendations
        recommendations = generate_safety_recommendations(analysis_result)
        analysis_result["recommendations"] = recommendations

        # Provide summary
        summary = generate_impact_summary(analysis_result)
        analysis_result["summary"] = summary

        return True, "Git analysis completed successfully", analysis_result

    except Exception as e:
        return False, f"Error during git analysis: {str(e)}", None


def analyze_branch_impact(
    repo_path: Path, target_branch: str, feature_branch: str, depth: str
) -> dict[str, Any]:
    """Analyze how feature branch changes impact a target branch."""
    import subprocess

    def run_git(command: list[str]) -> tuple[bool, str, str]:
        try:
            result = subprocess.run(
                ["git"] + command, cwd=repo_path, capture_output=True, text=True, timeout=30
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except Exception:
            return False, "", ""

    impact: dict[str, Any] = {
        "branch": target_branch,
        "risk_level": "low",
        "affected_areas": [],
        "file_count": 0,
        "line_count": 0,
        "function_changes": {} if depth == "functions" else None,
    }

    # Get file changes
    success, files_output, _ = run_git(
        ["diff", f"{target_branch}...{feature_branch}", "--name-only"]
    )
    if success:
        files = files_output.split("\n") if files_output else []
        impact["file_count"] = len([f for f in files if f.strip()])
        impact["affected_areas"] = classify_file_changes(files)

    # Get line changes
    success, stats_output, _ = run_git(["diff", f"{target_branch}...{feature_branch}", "--stat"])
    if success and stats_output:
        # Parse git stat output for line counts
        for line in stats_output.split("\n"):
            if "|" in line and not line.startswith(" "):
                # Extract insertion/deletion counts
                stats_part = line.split("|")[1].strip()
                import re

                match = re.search(r"(\d+)\s*insertion[^\d]*(\d+)?\s*deletion?", stats_part)
                if match:
                    insertions = int(match.group(1))
                    deletions = int(match.group(2) or 0)
                    impact["line_count"] = insertions + deletions

    # Determine risk level
    if impact["file_count"] > 50 or impact["line_count"] > 1000:
        impact["risk_level"] = "high"
    elif impact["file_count"] > 10 or impact["line_count"] > 200:
        impact["risk_level"] = "medium"

    return impact


def detect_branch_collisions(repo_path: Path, branch1: str, branch2: str) -> dict[str, Any]:
    """Detect potential collisions between two branches."""
    import subprocess

    def run_git(command: list[str]) -> tuple[bool, str, str]:
        try:
            result = subprocess.run(
                ["git"] + command, cwd=repo_path, capture_output=True, text=True, timeout=30
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except Exception:
            return False, "", ""

    collision: dict[str, Any] = {
        "collision_risk": "low",
        "conflicting_files": [],
        "merge_conflicts": [],
        "divergence_point": None,
    }

    # Check for conflicting changes
    success, merge_output, _ = run_git(["merge-tree", f"origin/{branch1}", f"origin/{branch2}"])
    if success and merge_output:
        # Parse for potential conflicts
        if "<<<<<<<" in merge_output:
            collision["collision_risk"] = "high"
            collision["merge_conflicts"] = ["Potential merge conflicts detected"]

    # Get common ancestor
    success, ancestor_output, _ = run_git(["merge-base", f"origin/{branch1}", f"origin/{branch2}"])
    if success:
        collision["divergence_point"] = ancestor_output

    # Check files changed in both branches
    success, files1, _ = run_git(["diff", f"origin/{branch1}...{branch1}", "--name-only"])
    success, files2, _ = run_git(["diff", f"origin/{branch2}...{branch2}", "--name-only"])

    if files1 and files2:
        set1 = set(files1.split("\n"))
        set2 = set(files2.split("\n"))
        common_files = set1.intersection(set2)
        collision["conflicting_files"] = list(common_files)

        if len(common_files) > 5:
            collision["collision_risk"] = "high"
        elif len(common_files) > 0:
            collision["collision_risk"] = "medium"

    return collision


def analyze_semantic_changes(
    repo_path: Path,
    base_branch: str,
    feature_branch: str,
    file_changes: dict[str, str],
) -> dict[str, Any]:
    """Perform semantic analysis of changes to identify deeper impacts."""
    semantic: dict[str, Any] = {
        "api_changes": [],
        "data_model_changes": [],
        "dependency_changes": [],
        "semantic_impact_score": 0.0,
    }

    # This is a simplified semantic analysis - could be enhanced with AST parsing
    for filepath, status in file_changes.items():
        if filepath.endswith((".py", ".js", ".ts", ".java", ".cpp")):
            # Look for function/class definitions that might be APIs
            if status in ["M", "A"]:  # Modified or Added
                semantic["api_changes"].append(f"Potential API change in {filepath}")
                semantic["semantic_impact_score"] += 0.3

        elif filepath.endswith((".json", ".yaml", ".yml")):
            # Configuration or data model changes
            semantic["data_model_changes"].append(f"Data model change in {filepath}")
            semantic["semantic_impact_score"] += 0.2

        elif "requirements" in filepath or "package" in filepath or "Pipfile" in filepath:
            # Dependency changes
            semantic["dependency_changes"].append(f"Dependency change in {filepath}")
            semantic["semantic_impact_score"] += 0.4

    # Normalize score
    semantic["semantic_impact_score"] = min(semantic["semantic_impact_score"], 1.0)

    return semantic


def classify_file_changes(files: list[str]) -> list[str]:
    """Classify types of changes based on file patterns."""
    areas = []

    for file_path in files:
        if file_path.startswith("src/") or file_path.startswith("lib/"):
            areas.append("Core code")
        elif file_path.startswith("test/") or file_path.endswith("_test.py"):
            areas.append("Tests")
        elif file_path.startswith("docs/"):
            areas.append("Documentation")
        elif file_path.endswith((".json", ".yaml", ".yml", ".toml")):
            areas.append("Configuration")
        elif file_path.endswith((".js", ".jsx", ".ts", ".tsx")) and "mobile" in file_path:
            areas.append("Mobile code")
        else:
            areas.append("Other")

    return list(set(areas))


def generate_safety_recommendations(analysis: dict[str, Any]) -> list[str]:
    """Generate safety recommendations based on analysis."""
    recommendations = []

    # Check for high-risk impacts
    for branch, impact in analysis["impacts"].items():
        if impact.get("risk_level") == "high":
            recommendations.append(
                f"⚠️  High risk detected for branch '{branch}'. "
                "Consider breaking down changes or extensive testing."
            )

        if impact.get("file_count", 0) > 20:
            recommendations.append(
                f"📁 Large number of files changed ({impact['file_count']}). "
                "Consider splitting into smaller PRs."
            )

    # Check for collisions
    for collision in analysis["collisions"]:
        if collision["analysis"]["collision_risk"] in ["medium", "high"]:
            recommendations.append(
                f"🔄 Collision risk with branch '{collision['branch']}'. "
                "Coordinate with that team before merging."
            )

    # Semantic analysis recommendations
    if "semantic_analysis" in analysis:
        semantic = analysis["semantic_analysis"]
        if semantic.get("semantic_impact_score", 0) > 0.7:
            recommendations.append(
                "🧠 High semantic impact detected. "
                "Comprehensive testing across all contexts recommended."
            )

        if semantic.get("api_changes"):
            recommendations.append(
                "API changes detected. Ensure backward compatibility and update documentation."
            )

    if not recommendations:
        recommendations.append(
            "✅ Low risk detected. Standard PR review process should be sufficient."
        )

    return recommendations


def generate_impact_summary(analysis: dict[str, Any]) -> str:
    """Generate a human-readable impact summary."""
    summary_parts = []

    feature_branch = analysis["feature_branch"]
    base_branch = analysis["base_branch"]

    # Basic stats
    changed_files = len(analysis.get("changed_files", {}))
    total_lines = sum(impact.get("line_count", 0) for impact in analysis["impacts"].values())

    summary_parts.append(f"📊 Analysis Summary for '{feature_branch}' → '{base_branch}':")
    summary_parts.append(f"   • Files changed: {changed_files}")
    summary_parts.append(f"   • Lines modified: {total_lines}")

    # Risk assessment
    risks = [impact["risk_level"] for impact in analysis["impacts"].values()]
    highest_risk = "high" if "high" in risks else "medium" if "medium" in risks else "low"
    risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}[highest_risk]

    summary_parts.append(f"   • Overall risk: {risk_emoji} {highest_risk.upper()}")

    # Collision risks
    collision_branches = [
        c["branch"] for c in analysis["collisions"] if c["analysis"]["collision_risk"] != "low"
    ]
    if collision_branches:
        summary_parts.append(f"   • Potential collisions: {', '.join(collision_branches)}")
    else:
        summary_parts.append("   • No significant collision risks detected")

    return "\n".join(summary_parts)


def perform_llm_enhanced_analysis(
    repo_path: Path,
    base_branch: str,
    feature_branch: str,
    compare_branches: list[str],
    intelligence_level: str,
    llm_model: str | None,
) -> dict[str, Any]:
    """
    Perform LLM-enhanced analysis for deeper insights.

    Args:
        repo_path: Path to git repository
        base_branch: Base branch name
        feature_branch: Feature branch name
        compare_branches: List of context branches
        intelligence_level: 'smart' or 'deep'
        llm_model: Optional specific model to use

    Returns:
        LLM analysis results
    """
    import subprocess

    try:
        # Import LLM analyzer
        from ..llm_analysis import get_llm_analyzer

        llm_analyzer = get_llm_analyzer(llm_model)
        if not llm_analyzer.is_available():
            return {"error": "LLM not available or not configured"}

        # Get diff content for LLM analysis
        def run_git(command: list[str]) -> tuple[bool, str, str]:
            try:
                result = subprocess.run(
                    ["git"] + command, cwd=repo_path, capture_output=True, text=True, timeout=30
                )
                return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
            except Exception:
                return False, "", ""

        # Get full diff for analysis
        success, diff_content, _ = run_git(
            ["diff", f"{base_branch}...{feature_branch}", "--unified=3"]
        )
        if not success:
            return {"error": "Failed to generate diff for LLM analysis"}

        # Perform basic code analysis for both smart and deep modes
        code_analysis = llm_analyzer.analyze_code_changes(diff_content, compare_branches)

        llm_result: dict[str, Any] = {
            "intelligence_level": intelligence_level,
            "model_used": (
                llm_analyzer.model_config.name
                if hasattr(llm_analyzer, "model_config")
                else llm_model
            ),
            "code_analysis": code_analysis,
        }

        if intelligence_level == "deep":
            # Additional deep analysis

            # Get commit messages for quality analysis
            success, commit_output, _ = run_git(
                ["log", f"{base_branch}..{feature_branch}", "--oneline", "--no-merges"]
            )
            if success:
                commit_messages = commit_output.split("\n") if commit_output else []
                commit_quality = llm_analyzer.analyze_commit_quality(commit_messages)
                llm_result["commit_quality"] = commit_quality

            # Business impact assessment (using project context from repo structure)
            project_context = infer_project_context(repo_path)
            changes_summary = {
                "files": len(code_analysis.get("breaking_changes", [])),
                "complexity": (
                    code_analysis.get("risk_assessment", {}).get("technical_complexity", "unknown")
                ),
            }
            business_impact = llm_analyzer.assess_business_impact(changes_summary, project_context)
            llm_result["business_impact"] = business_impact

            # Coordination planning
            collision_summary = {"branches": compare_branches}
            coordination_plan = llm_analyzer.generate_coordination_plan(
                collision_summary, changes_summary
            )
            llm_result["coordination_plan"] = coordination_plan

        return llm_result

    except Exception as e:
        return {"error": f"LLM analysis failed: {str(e)}"}


def infer_project_context(repo_path: Path) -> str:
    """Infer project context from repository structure and files."""
    import os

    indicators = {
        "payment processing": ["payment", "billing", "stripe", "paypal", "subscription"],
        "user authentication": ["auth", "login", "user", "session", "jwt", "oauth"],
        "e-commerce": ["cart", "product", "inventory", "order", "shop"],
        "data analytics": ["analytics", "dashboard", "metrics", "reporting"],
        "mobile app": ["mobile", "ios", "android", "react-native", "flutter"],
        "api/backend": ["api", "rest", "graphql", "endpoint", "controller"],
        "content management": ["cms", "content", "blog", "article", "media"],
        "devops/infrastructure": ["docker", "k8s", "deploy", "ci/cd", "terraform"],
    }

    try:
        # Look for indicative files and directories
        for root, dirs, files in os.walk(repo_path):
            for item in dirs + files:
                item_lower = item.lower()
                for context, keywords in indicators.items():
                    if any(keyword in item_lower for keyword in keywords):
                        return context
        return "general software development"
    except Exception:
        return "software development"


def merge_llm_recommendations(
    analysis_result: dict[str, Any], llm_analysis: dict[str, Any]
) -> None:
    """Merge LLM-generated recommendations into the main analysis results."""
    if "error" in llm_analysis:
        return

    code_analysis = llm_analysis.get("code_analysis", {})

    # Add breaking change warnings
    breaking_changes = code_analysis.get("breaking_changes", [])
    if breaking_changes:
        for change in breaking_changes:
            severity_emoji = {"high": "🚨", "medium": "⚠️", "low": "📋"}.get(
                change.get("severity", "low"), "📋"
            )
            analysis_result["recommendations"].append(
                f"{severity_emoji} Breaking change detected in {change.get('file', 'unknown')}: "
                f"{change.get('description', 'unknown')}"
            )

    # Add coordination requirements
    if "coordination_plan" in llm_analysis:
        coordination = llm_analysis["coordination_plan"]
        coordination_required = coordination.get("coordination_required", [])
        for item in coordination_required:
            urgency_emoji = {"immediate": "🚨", "before_merge": "⚡", "after_merge": "📋"}.get(
                item.get("urgency", "after_merge"), "📋"
            )
            analysis_result["recommendations"].append(
                f"{urgency_emoji} Coordinate with {item.get('team', 'team')}: "
                f"{item.get('action', 'action needed')}"
            )

    # Add business impact warnings
    if "business_impact" in llm_analysis:
        business = llm_analysis["business_impact"]
        risk_level = business.get("business_risk", "low")
        if risk_level in ["high", "medium"]:
            risk_emoji = {"high": "🚨", "medium": "⚠️"}[risk_level]
            analysis_result["recommendations"].append(
                f"{risk_emoji} Business risk assessed as {risk_level.upper()}: "
                f"{business.get('customer_impact', {}).get('areas', ['unknown'])}"
            )

    # Add risk mitigation suggestions
    if llm_analysis.get("intelligence_level") == "deep":
        risk_mitigation = code_analysis.get("recommendations", [])
        for suggestion in risk_mitigation[:3]:  # Limit to top 3
            analysis_result["recommendations"].append(f"💡 {suggestion}")

    # Remove duplicates while preserving order
    seen = set()
    unique_recommendations = []
    for rec in analysis_result["recommendations"]:
        if rec not in seen:
            seen.add(rec)
            unique_recommendations.append(rec)
    analysis_result["recommendations"] = unique_recommendations
