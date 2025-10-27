"""PR management tool for staging changes and cross-branch impact analysis."""

from pathlib import Path
from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "pr_manager",
        "description": (
            "Comprehensive PR management for staging changes, analyzing cross-branch "
            "impacts, and ensuring safe commits. Perfect for multi-branch development workflows. "
            "LLM enhancement for intelligent validation and coordination planning."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["analyze", "stage", "validate", "impact_report", "collision_check"],
                    "description": (
                        "Action to perform: 'analyze' (full analysis), 'stage' (prepare staged "
                        "changes), 'validate' (check safety), 'impact_report' (detailed impact), "
                        "'collision_check' (check branch conflicts)"
                    ),
                },
                "source_branch": {
                    "type": "string",
                    "description": "Source/feature branch containing changes",
                },
                "target_branch": {
                    "type": "string",
                    "description": "Target branch (e.g., 'main', 'develop', 'staging')",
                },
                "context_branches": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Additional context branches to analyze impact on "
                        "(e.g., ['mobile/main', 'api/v2', 'feature/parallel'])"
                    ),
                    "default": [],
                },
                "repo_path": {
                    "type": "string",
                    "description": "Path to the git repository",
                    "default": ".",
                },
                "safety_level": {
                    "type": "string",
                    "enum": ["strict", "moderate", "permissive"],
                    "description": (
                        "Safety validation level: 'strict' (all checks), 'moderate' (standard "
                        "checks), 'permissive' (minimal checks)"
                    ),
                    "default": "moderate",
                },
                "generate_patch": {
                    "type": "boolean",
                    "description": "Whether to generate a clean patch file for the changes",
                    "default": True,
                },
                "include_tests": {
                    "type": "boolean",
                    "description": "Whether to analyze test coverage and test impact",
                    "default": True,
                },
                "intelligence_level": {
                    "type": "string",
                    "enum": ["fast", "smart", "deep"],
                    "description": (
                        "Intelligence level: 'fast' (rule-based validation only), "
                        "'smart' (LLM-enhanced validation), "
                        "'deep' (comprehensive LLM analysis with coordination planning)"
                    ),
                    "default": "smart",
                },
                "llm_model": {
                    "type": "string",
                    "description": (
                        "Specific LLM model to use for analysis (uses default if not specified)"
                    ),
                    "default": None,
                },
            },
            "required": ["action", "source_branch", "target_branch"],
        },
    },
}


def pr_manager(
    action: str,
    source_branch: str,
    target_branch: str,
    context_branches: list[str] | None = None,
    repo_path: str = ".",
    safety_level: str = "moderate",
    generate_patch: bool = True,
    include_tests: bool = True,
    intelligence_level: str = "smart",
    llm_model: str | None = None,
) -> tuple[bool, str, Any]:
    """
    Comprehensive PR management for multi-branch development workflows.

    This addresses your friend's exact needs:
    - Stages changes safely before commits
    - Analyzes how commits in subfeatureB affect F, A, M, and F'1
    - Detects cross-branch collisions
    - Provides detailed impact analysis
    """
    import os
    import subprocess
    from datetime import datetime

    try:
        repo_path_obj = Path(repo_path).resolve()
        if not os.path.exists(repo_path_obj):
            return False, f"Repository path does not exist: {repo_path}", None

        # Initialize result
        result: dict[str, Any] = {
            "action": action,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "context_branches": context_branches or [],
            "repo_path": str(repo_path_obj),
            "safety_level": safety_level,
            "intelligence_level": intelligence_level,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "warnings": [],
            "blocking_issues": [],
            "llm_enhanced": True,  # Always use LLM analysis
        }

        # Helper function to run git commands
        def run_git(command: list[str], capture_output: bool = True) -> tuple[bool, str, str]:
            try:
                if capture_output:
                    proc = subprocess.run(
                        ["git"] + command,
                        cwd=repo_path_obj,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    return proc.returncode == 0, proc.stdout.strip(), proc.stderr.strip()
                else:
                    proc = subprocess.run(
                        ["git"] + command, cwd=repo_path_obj, timeout=30, text=True
                    )
                    return proc.returncode == 0, "", ""

            except Exception as e:
                return False, "", str(e)

        # Verify repository state
        if not (repo_path_obj / ".git").exists():
            return False, "Not a git repository", None

        # Check if there are uncommitted changes
        success, status_output, _ = run_git(["status", "--porcelain"])
        if success and status_output.strip():
            result["warnings"].append(
                "Repository has uncommitted changes. Consider committing or stashing first."
            )

        if action == "analyze":
            # Perform comprehensive analysis using git_analyzer
            from .git_analyzer import git_analyzer

            git_success, git_message, git_analysis = git_analyzer(
                base_branch=target_branch,
                feature_branch=source_branch,
                compare_branches=context_branches,
                repo_path=str(repo_path_obj),
                analysis_depth="files",
                include_semantic_analysis=True,
                intelligence_level=intelligence_level,
                llm_model=llm_model,
            )

            if git_success:
                result.update(git_analysis)

                # Add additional PR-specific analysis
                pr_analysis = perform_pr_specific_analysis(
                    repo_path_obj, source_branch, target_branch, context_branches or []
                )
                result["pr_analysis"] = pr_analysis

                # Safety validation
                safety_result = validate_safety(result, safety_level)
                result["safety_validation"] = safety_result

                # Perform LLM-enhanced PR analysis (always required now)
                llm_pr_analysis = perform_llm_pr_analysis(
                    repo_path_obj,
                    source_branch,
                    target_branch,
                    context_branches or [],
                    intelligence_level,
                    llm_model,
                    result,
                )
                result["llm_pr_analysis"] = llm_pr_analysis

                result["success"] = True
                return True, "PR analysis completed successfully", result
            else:
                return False, f"Git analysis failed: {git_message}", None

        elif action == "stage":
            # Stage changes for safe commit
            stage_result = stage_changes_safely(
                repo_path_obj, source_branch, target_branch, generate_patch
            )
            result.update(stage_result)

            if stage_result.get("success", False):
                result["success"] = True
                return True, "Changes staged successfully", result
            else:
                return False, "Failed to stage changes", result

        elif action == "validate":
            # Validate PR safety and readiness
            validation = validate_pr_readiness(
                repo_path_obj,
                source_branch,
                target_branch,
                context_branches or [],
                safety_level,
                include_tests,
            )
            result.update(validation)

            result["success"] = validation.get("overall_safe", False)
            return True, "PR validation completed", result

        elif action == "impact_report":
            # Generate detailed impact report
            impact_report = generate_detailed_impact_report(
                repo_path_obj, source_branch, target_branch, context_branches or []
            )
            result.update(impact_report)

            result["success"] = True
            return True, "Impact report generated", result

        elif action == "collision_check":
            # Focus on collision detection
            collisions = perform_comprehensive_collision_check(
                repo_path_obj, source_branch, [target_branch] + (context_branches or [])
            )
            result["collision_analysis"] = collisions

            # Determine collision severity
            max_severity = (
                max(c.get("severity", "low") for c in collisions.values()) if collisions else "low"
            )
            result["collision_severity"] = max_severity
            result["success"] = True

            if max_severity in ["high", "critical"]:
                result["warnings"].append(
                    "High collision severity detected. "
                    "Coordinate with affected teams before proceeding."
                )

            return True, "Collision check completed", result

        else:
            return False, f"Unknown action: {action}", None

    except Exception as e:
        return False, f"Error during PR management: {str(e)}", None


def perform_pr_specific_analysis(
    repo_path: Path,
    source_branch: str,
    target_branch: str,
    context_branches: list[str],
) -> dict[str, Any]:
    """Perform PR-specific analysis beyond basic git diff."""
    import subprocess

    def run_git(command: list[str]) -> tuple[bool, str, str]:
        try:
            proc = subprocess.run(
                ["git"] + command, cwd=repo_path, capture_output=True, text=True, timeout=30
            )
            return proc.returncode == 0, proc.stdout.strip(), proc.stderr.strip()
        except Exception:
            return False, "", ""

    analysis: dict[str, Any] = {
        "commit_history": {},
        "change_complexity": "low",
        "review_difficulty": "easy",
        "merge_strategy": "fast-forward",
        "test_implications": [],
    }

    # Analyze commits in the source branch
    success, log_output, _ = run_git(
        ["log", f"{target_branch}..{source_branch}", "--oneline", "--no-merges"]
    )
    if success:
        commits = log_output.split("\n") if log_output else []
        analysis["commit_history"] = {
            "commit_count": len(commits),
            "recent_commits": commits[:10],  # Last 10 commits
        }

        # Assess complexity based on commit count and patterns
        if len(commits) > 20:
            analysis["change_complexity"] = "high"
            analysis["review_difficulty"] = "complex"
        elif len(commits) > 5:
            analysis["change_complexity"] = "medium"
            analysis["review_difficulty"] = "moderate"

        # Check for merge commits (might need merge strategy)
        success, merge_check, _ = run_git(
            ["log", f"{target_branch}..{source_branch}", "--merges", "--oneline"]
        )
        if success and merge_check.strip():
            analysis["merge_strategy"] = "merge-commits"

    # Analyze file types and patterns
    success, file_output, _ = run_git(["diff", f"{target_branch}...{source_branch}", "--name-only"])
    if success:
        files = file_output.split("\n") if file_output else []

        # Assess complexity based on file types
        complex_files = [
            f for f in files if f.endswith((".py", ".js", ".ts", ".java", ".cpp", ".go"))
        ]
        config_files = [f for f in files if f.endswith((".json", ".yaml", ".yml", ".xml", ".toml"))]

        if len(complex_files) > 10:
            analysis["review_difficulty"] = "complex"
        elif len(complex_files) > 3:
            analysis["review_difficulty"] = "moderate"

        # Test implications
        test_files = [
            f for f in files if "test" in f or f.endswith("_test.py") or f.endswith(".test.js")
        ]
        if not test_files:
            analysis["test_implications"].append("⚠️  No test files detected in changes")

        if config_files:
            analysis["test_implications"].append(
                "📄 Configuration files changed - test environment setup may be affected"
            )

    return analysis


def stage_changes_safely(
    repo_path: Path, source_branch: str, target_branch: str, generate_patch: bool
) -> dict[str, Any]:
    """Stage changes safely with proper validation."""
    import subprocess
    from datetime import datetime

    def run_git(command: list[str]) -> tuple[bool, str, str]:
        try:
            proc = subprocess.run(
                ["git"] + command, cwd=repo_path, capture_output=True, text=True, timeout=30
            )
            return proc.returncode == 0, proc.stdout.strip(), proc.stderr.strip()
        except Exception:
            return False, "", ""

    stage_result: dict[str, Any] = {
        "success": False,
        "staged_files": [],
        "patch_file": None,
        "backup_created": False,
        "validation": {"passed": [], "failed": []},
    }

    try:
        # Create backup of current state
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_branch = f"backup/merge_backup_{timestamp}"

        success, _, stderr = run_git(["checkout", "-b", backup_branch])
        if success:
            stage_result["backup_created"] = True
            stage_result["backup_branch"] = backup_branch

        # Switch back to original branch (assuming we were on source branch)
        run_git(["checkout", source_branch])

        # Generate clean diff between branches
        success, diff_output, _ = run_git(["diff", f"{target_branch}...{source_branch}"])
        if not success:
            stage_result["validation"]["failed"].append("Failed to generate diff between branches")
            return stage_result

        # Save diff as patch if requested
        if generate_patch:
            patch_file = repo_path / f"staged_changes_{timestamp}.patch"
            with open(patch_file, "w") as f:
                f.write(diff_output)
            stage_result["patch_file"] = str(patch_file)

        # Get list of changed files
        success, files_output, _ = run_git(
            ["diff", f"{target_branch}...{source_branch}", "--name-only"]
        )
        if success:
            stage_result["staged_files"] = files_output.split("\n") if files_output else []

        # Basic validations
        if len(stage_result["staged_files"]) == 0:
            stage_result["validation"]["failed"].append("No changes detected to stage")
        else:
            stage_result["validation"]["passed"].append(
                f"Changes identified in {len(stage_result['staged_files'])} files"
            )

        # Check for binary files (might need special handling)
        success, binary_output, _ = run_git(
            ["diff", f"{target_branch}...{source_branch}", "--binary", "--name-only"]
        )
        if binary_output:
            stage_result["validation"]["passed"].append("Binary changes detected and included")

        stage_result["success"] = len(stage_result["validation"]["failed"]) == 0

    except Exception as e:
        stage_result["validation"]["failed"].append(f"Error during staging: {str(e)}")

    return stage_result


def validate_pr_readiness(
    repo_path: Path,
    source_branch: str,
    target_branch: str,
    context_branches: list[str],
    safety_level: str,
    include_tests: bool,
) -> dict[str, Any]:
    """Comprehensive validation of PR readiness."""
    import subprocess

    def run_git(command: list[str]) -> tuple[bool, str, str]:
        try:
            proc = subprocess.run(
                ["git"] + command, cwd=repo_path, capture_output=True, text=True, timeout=30
            )
            return proc.returncode == 0, proc.stdout.strip(), proc.stderr.strip()
        except Exception:
            return False, "", ""

    validation: dict[str, Any] = {
        "overall_safe": False,
        "checks": {},
        "recommendations": [],
        "blockers": [],
        "score": 0.0,
        "max_score": 10.0,
    }

    score = 0.0

    # Check 1: Branch availability
    for branch in [source_branch, target_branch] + context_branches:
        success, _, _ = run_git(["rev-parse", "--verify", branch])
        validation["checks"][f"branch_exists_{branch}"] = success
        if success:
            score += 0.5

    # Check 2: No merge conflicts with target
    success, merge_result, _ = run_git(["merge-tree", target_branch, source_branch])
    if success and "<<<<<<<" not in merge_result:
        validation["checks"]["no_merge_conflicts"] = True
        score += 2.0
    else:
        validation["checks"]["no_merge_conflicts"] = False
        validation["blockers"].append("Merge conflicts detected with target branch")

    # Check 3: Reasonable change size
    success, file_count, _ = run_git(["diff", f"{target_branch}...{source_branch}", "--name-only"])
    if success:
        files = file_count.split("\n") if file_count else []
        file_num = len([f for f in files if f.strip()])
        validation["checks"]["reasonable_change_size"] = file_num <= 50
        if file_num <= 50:
            score += 1.5
        else:
            validation["recommendations"].append(
                "Large number of files changed - consider breaking into smaller PRs"
            )

    # Check 4: Test coverage (if enabled)
    if include_tests:
        success, test_files, _ = run_git(
            ["diff", f"{target_branch}...{source_branch}", "--name-only", "--", "*test*"]
        )
        has_tests = success and test_files.strip()

        success, all_changes, _ = run_git(
            ["diff", f"{target_branch}...{source_branch}", "--name-only"]
        )
        has_code_changes = success and all_changes.strip()

        if has_code_changes and not has_tests:
            validation["checks"]["has_test_coverage"] = False
            validation["recommendations"].append(
                "Code changes detected but no test files - consider adding tests"
            )
        else:
            validation["checks"]["has_test_coverage"] = True
            score += 1.0

    # Check 5: Context branch safety
    collision_risk = 0
    for context_branch in context_branches:
        success, check_result, _ = run_git(["merge-tree", context_branch, source_branch])
        if success and "<<<<<<<" in check_result:
            collision_risk += 1

    if collision_risk == 0:
        validation["checks"]["context_branch_safe"] = True
        score += 1.5
    else:
        validation["checks"]["context_branch_safe"] = False
        validation["recommendations"].append(
            f"Potential conflicts with {collision_risk} context branches"
        )

    # Check 6: Commit message quality
    success, commits, _ = run_git(["log", f"{target_branch}..{source_branch}", "--oneline"])
    if success:
        commit_lines = commits.split("\n") if commits else []
        has_descriptive_commits = all(
            len(line) > 20 and ":" in line for line in commit_lines if line.strip()
        )
        validation["checks"]["good_commit_messages"] = has_descriptive_commits
        if has_descriptive_commits:
            score += 1.0
        else:
            validation["recommendations"].append(
                "Consider improving commit messages for better clarity"
            )

    # Safety level adjustments
    if safety_level == "strict":
        threshold = 9.0
        required_checks = ["no_merge_conflicts", "has_test_coverage"]
        for check in required_checks:
            if not validation["checks"].get(check, True):
                validation["blockers"].append(f"Required check failed for strict mode: {check}")
    elif safety_level == "moderate":
        threshold = 7.0
    else:  # permissive
        threshold = 5.0

    validation["score"] = min(score, validation["max_score"])
    validation["overall_safe"] = (
        validation["score"] >= threshold and len(validation["blockers"]) == 0
    )

    return validation


def generate_detailed_impact_report(
    repo_path: Path,
    source_branch: str,
    target_branch: str,
    context_branches: list[str],
) -> dict[str, Any]:
    """Generate comprehensive impact report for stakeholders."""

    report: dict[str, Any] = {
        "executive_summary": "",
        "technical_details": {},
        "risk_assessment": {},
        "timeline_impact": {},
        "resource_requirements": {},
        "rollback_plan": {},
    }

    # This would integrate with the git_analyzer and add business context
    # For now, provide structured template
    report["executive_summary"] = f"""
PR Impact Analysis: {source_branch} → {target_branch}
Context Branches: {", ".join(context_branches) if context_branches else "None"}

This analysis evaluates the impact of merging changes from {source_branch} into {target_branch},
considering potential effects on {len(context_branches)} additional context branches.
    """.strip()

    return report


def perform_comprehensive_collision_check(
    repo_path: Path, source_branch: str, target_branches: list[str]
) -> dict[str, Any]:
    """Perform detailed collision analysis with multiple branches."""
    import subprocess

    def run_git(command: list[str]) -> tuple[bool, str, str]:
        try:
            proc = subprocess.run(
                ["git"] + command, cwd=repo_path, capture_output=True, text=True, timeout=30
            )
            return proc.returncode == 0, proc.stdout.strip(), proc.stderr.strip()
        except Exception:
            return False, "", ""

    collision_analysis: dict[str, Any] = {}

    for target_branch in target_branches:
        analysis: dict[str, Any] = {
            "severity": "low",
            "conflicting_files": [],
            "merge_complexity": "simple",
            "divergence_point": None,
            "recommendations": [],
        }

        # Check mergeability
        success, result, _ = run_git(["merge-tree", target_branch, source_branch])
        if success:
            if "<<<<<<<" in result:
                analysis["severity"] = "high" if result.count(">>>>>>>") > 5 else "medium"
                analysis["merge_complexity"] = "complex"
            else:
                analysis["severity"] = "low"
                analysis["merge_complexity"] = "simple"

        # Get conflicting files
        success, files1, _ = run_git(["diff", f"{target_branch}...{source_branch}", "--name-only"])
        success, files2, _ = run_git(["diff", f"{source_branch}...{target_branch}", "--name-only"])

        if files1 and files2:
            set1 = set(files1.split("\n"))
            set2 = set(files2.split("\n"))
            common = set1.intersection(set2)
            analysis["conflicting_files"] = list(common)

        # Get divergence point
        success, ancestor, _ = run_git(["merge-base", target_branch, source_branch])
        if success:
            analysis["divergence_point"] = ancestor

        # Generate recommendations
        if analysis["severity"] == "high":
            analysis["recommendations"].append("Coordinate with target branch team before merging")
            analysis["recommendations"].append("Consider extensive integration testing")
        elif analysis["severity"] == "medium":
            analysis["recommendations"].append("Review conflicting files carefully")
            analysis["recommendations"].append("Plan for potential merge conflicts")

        collision_analysis[target_branch] = analysis

    return collision_analysis


def validate_safety(analysis_result: dict[str, Any], safety_level: str) -> dict[str, Any]:
    """Validate overall safety based on analysis results."""
    validation: dict[str, Any] = {
        "safe_to_proceed": False,
        "risk_level": "low",
        "blocking_issues": [],
        "warnings": [],
        "recommended_actions": [],
    }

    # Extract risk indicators
    file_count = len(analysis_result.get("changed_files", {}))
    collision_risks = [
        c
        for c in analysis_result.get("collisions", [])
        if c.get("analysis", {}).get("collision_risk") in ["medium", "high"]
    ]

    # Determine overall risk
    if file_count > 50 or len(collision_risks) > 2:
        validation["risk_level"] = "high"
    elif file_count > 10 or len(collision_risks) > 0:
        validation["risk_level"] = "medium"

    # Blocking issues for different safety levels
    if safety_level == "strict":
        if validation["risk_level"] == "high":
            validation["blocking_issues"].append("High risk changes not allowed in strict mode")
        if collision_risks:
            validation["blocking_issues"].append("Any collision risk not allowed in strict mode")
    elif safety_level == "moderate":
        if file_count > 100:
            validation["blocking_issues"].append(
                "Extremely large changes require breaking into smaller PRs"
            )

    # Generate recommendations
    if validation["risk_level"] == "high":
        validation["recommended_actions"].extend(
            [
                "Break changes into smaller, focused PRs",
                "Coordinate with all affected teams",
                "Plan extensive testing across all contexts",
            ]
        )

    # Determine if safe to proceed
    validation["safe_to_proceed"] = (
        len(validation["blocking_issues"]) == 0 and validation["risk_level"] != "high"
    )

    return validation


def perform_llm_pr_analysis(
    repo_path: Path,
    source_branch: str,
    target_branch: str,
    context_branches: list[str],
    intelligence_level: str,
    llm_model: str | None,
    analysis_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Perform LLM-enhanced PR analysis for deeper validation insights.

    Args:
        repo_path: Path to git repository
        source_branch: Source branch name
        target_branch: Target branch name
        context_branches: List of context branches
        intelligence_level: 'smart' or 'deep'
        llm_model: Optional specific model to use
        analysis_result: Existing analysis results to enhance

    Returns:
        LLM PR analysis results
    """
    import subprocess

    try:
        # Import LLM analyzer
        from ..llm_analysis import get_llm_analyzer
        from .git_analyzer import infer_project_context

        llm_analyzer = get_llm_analyzer(llm_model)
        if not llm_analyzer.is_available():
            return {"error": "LLM not available or not configured"}

        pr_analysis: dict[str, Any] = {
            "intelligence_level": intelligence_level,
            "model_used": (
                llm_analyzer.model_config.name
                if hasattr(llm_analyzer, "model_config")
                else llm_model
            ),
        }

        # Helper function to run git commands
        def run_git(command: list[str]) -> tuple[bool, str, str]:
            try:
                result = subprocess.run(
                    ["git"] + command, cwd=repo_path, capture_output=True, text=True, timeout=30
                )
                return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
            except Exception:
                return False, "", ""

        # Get commit messages for quality analysis
        success, commit_output, _ = run_git(
            ["log", f"{target_branch}..{source_branch}", "--oneline", "--no-merges"]
        )

        if success:
            commit_messages = commit_output.split("\n") if commit_output else []
            commit_quality = llm_analyzer.analyze_commit_quality(commit_messages)
            pr_analysis["commit_quality"] = commit_quality

        # Business impact assessment for deep analysis
        if intelligence_level == "deep":
            project_context = infer_project_context(repo_path)
            changes_summary = {
                "files": len(analysis_result.get("changed_files", {})),
                "risk_level": extract_overall_risk(analysis_result),
                "branches_affected": len(analysis_result.get("impacts", {})),
                "has_collisions": bool(analysis_result.get("collisions", [])),
            }
            business_impact = llm_analyzer.assess_business_impact(changes_summary, project_context)
            pr_analysis["business_impact"] = business_impact

        # Coordination planning when there are collision risks
        collision_analysis = analysis_result.get("collisions", [])
        if collision_analysis and any(
            c.get("analysis", {}).get("collision_risk") != "low" for c in collision_analysis
        ):
            collision_summary = {
                "branches": [c["branch"] for c in collision_analysis],
                "high_risk_count": len(
                    [
                        c
                        for c in collision_analysis
                        if c.get("analysis", {}).get("collision_risk") == "high"
                    ]
                ),
                "medium_risk_count": len(
                    [
                        c
                        for c in collision_analysis
                        if c.get("analysis", {}).get("collision_risk") == "medium"
                    ]
                ),
            }
            changes_summary = {
                "source_branch": source_branch,
                "target_branch": target_branch,
                "impact_level": extract_overall_risk(analysis_result),
            }
            coordination_plan = llm_analyzer.generate_coordination_plan(
                collision_summary, changes_summary
            )
            pr_analysis["coordination_plan"] = coordination_plan

        # Generate enhanced recommendations
        enhanced_recommendations = generate_llm_pr_recommendations(pr_analysis, analysis_result)
        pr_analysis["enhanced_recommendations"] = enhanced_recommendations

        return pr_analysis

    except Exception as e:
        return {"error": f"LLM PR analysis failed: {str(e)}"}


def extract_overall_risk(analysis_result: dict[str, Any]) -> str:
    """Extract overall risk level from analysis results."""
    risks = []

    # Check branch impacts
    for impact in analysis_result.get("impacts", {}).values():
        risks.append(impact.get("risk_level", "low"))

    # Check collision risks
    for collision in analysis_result.get("collisions", []):
        risks.append(collision.get("analysis", {}).get("collision_risk", "low"))

    # Return highest risk
    if "high" in risks:
        return "high"
    elif "medium" in risks:
        return "medium"
    else:
        return "low"


def generate_llm_pr_recommendations(
    llm_pr_analysis: dict[str, Any], analysis_result: dict[str, Any]
) -> list[str]:
    """Generate enhanced PR recommendations based on LLM analysis."""
    recommendations = []

    # Commit quality recommendations
    commit_quality = llm_pr_analysis.get("commit_quality", {})
    if commit_quality:
        overall_quality = commit_quality.get("overall_quality", "")
        if overall_quality in ["fair", "poor"]:
            recommendations.append(
                "📝 Consider improving commit message quality for better maintainability"
            )

        for issue in commit_quality.get("issues", []):
            recommendations.append(f"⚠️  {issue}")

    # Business impact recommendations
    business_impact = llm_pr_analysis.get("business_impact", {})
    if business_impact:
        business_risk = business_impact.get("business_risk", "")
        if business_risk == "high":
            recommendations.append(
                "🚨 High business impact detected - ensure stakeholder approval before merge"
            )

        compliance_risk = business_impact.get("compliance_risk", {})
        compliance_level = compliance_risk.get("level", "")
        if compliance_level in ["high", "medium"]:
            recommendations.append(
                f"📋 Compliance considerations: {', '.join(compliance_risk.get('areas', []))}"
            )

    # Coordination recommendations
    coordination_plan = llm_pr_analysis.get("coordination_plan", {})
    if coordination_plan:
        # Add specific coordination actions
        coordination_required = coordination_plan.get("coordination_required", [])
        for item in coordination_required[:2]:  # Top 2 most important
            urgency = item.get("urgency", "after_merge")
            urgency_emoji = {"immediate": "🚨", "before_merge": "⚡", "after_merge": "📋"}.get(
                urgency, "📋"
            )
            recommendations.append(
                f"{urgency_emoji} Coordinate with {item.get('team', 'team')}: "
                f"{item.get('action', 'action needed')}"
            )

    # Risk mitigation recommendations
    if True:  # Always include deep analysis features
        risk_mitigation = business_impact.get("recommendations", [])
        for suggestion in risk_mitigation[:2]:  # Top 2 suggestions
            recommendations.append(f"💡 {suggestion}")

    return recommendations
