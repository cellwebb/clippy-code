# PR Analysis and Cross-Branch Impact Assessment

This document describes the new PR-level analysis features added to clippy, designed specifically for multi-branch development workflows and preventing cross-branch conflicts.

## 🎯 Problem Statement

Your friend described a common and critical challenge in modern software development:

```
main M (monolith)
 -> primary feature F
   -> subfeatureA
   -> subfeatureB

mobile (react native)
  -> primary feature F'1
```

The core question: **How do we analyze commits in B as they might affect:**
- F (parent feature)
- A (sibling subfeature)  
- M (main monolith)
- F'1 (mobile feature)

## 📎 Solution: Two New Tools

### 1. `git_analyzer` - Advanced Git Analysis

Deep analysis of git changes across multiple branches with semantic understanding.

#### Key Features:
- **Cross-branch impact analysis**: See how changes in one branch affect others
- **Collision detection**: Identify files that conflict between branches  
- **Semantic analysis**: Understand API changes, data model changes, dependency updates
- **Risk assessment**: Automatic risk scoring (low/medium/high)
- **Smart recommendations**: Context-aware safety recommendations

#### Usage Example:
```python
git_analyzer(
    base_branch="main",           # M - base monolith
    feature_branch="feature/subfeatureB",  # B - source of changes
    compare_branches=[            # Context branches
        "feature/subfeatureA",    # A - sibling
        "feature/primaryFeatureF", # F - parent
        "mobile/primaryFeatureF1"  # F'1 - mobile
    ],
    analysis_depth="files",        # or "commits", "functions", "full"
    include_semantic_analysis=True
)
```

#### Result Structure:
```json
{
  "impacts": {
    "main": {
      "risk_level": "medium",
      "file_count": 12,
      "line_count": 234,
      "affected_areas": ["Core code", "Configuration"]
    },
    "feature/subfeatureA": {
      "risk_level": "low",
      "collision_risk": "medium"
    }
  },
  "collisions": [
    {
      "branch": "feature/subfeatureA",
      "analysis": {
        "collision_risk": "medium",
        "conflicting_files": ["src/utils/helpers.py"]
      }
    }
  ],
  "semantic_analysis": {
    "api_changes": ["Potential API change in src/api/controllers.py"],
    "semantic_impact_score": 0.7
  },
  "recommendations": [
    "🔄 Collision risk with branch 'feature/subfeatureA'. Coordinate with that team before merging.",
    "API changes detected. Ensure backward compatibility and update documentation."
  ]
}
```

### 2. `pr_manager` - Comprehensive PR Management

Complete PR workflow management with staging, validation, and impact reporting.

#### Actions:
- **`analyze`**: Full PR analysis using git_analyzer plus PR-specific insights
- **`validate`**: Safety validation with configurable strictness levels
- **`stage`**: Create clean change patches and backup branches
- **`impact_report`**: Generate stakeholder-friendly impact reports
- **`collision_check`**: Focused collision detection with detailed analysis

#### Safety Levels:
- **`strict`**: All checks must pass, no collision risks allowed
- **`moderate`**: Standard safety checks, medium collision risks allowed
- **`permissive`**: Basic checks only, minimal safety requirements

#### Validation Criteria:
- Branch existence verification
- Merge conflict detection
- Change size assessment
- Test coverage analysis
- Context branch safety
- Commit message quality
- Safety level enforcement

## 🚀 Quick Start

### 1. Basic Impact Analysis
```python
from clippy.tools import git_analyzer

# Analyze how subfeatureB affects other branches
success, message, result = git_analyzer(
    base_branch="main",
    feature_branch="feature/subfeatureB", 
    compare_branches=["feature/subfeatureA", "mobile/F1"],
    analysis_depth="files"
)

if success:
    print("Impact Summary:")
    print(result["summary"])
    
    for branch, impact in result["impacts"].items():
        print(f"{branch}: {impact['risk_level']} risk")
```

### 2. PR Validation
```python
from clippy.tools import pr_manager

# Validate PR safety before merging
success, message, result = pr_manager(
    action="validate",
    source_branch="feature/subfeatureB",
    target_branch="main",
    context_branches=["feature/subfeatureA", "mobile/F1"],
    safety_level="moderate"
)

if result["overall_safe"]:
    print("✅ PR is safe to merge")
    print(f"Score: {result['score']}/{result['max_score']}")
else:
    print("⚠️  PR requires attention")
    for blocker in result["blocking_issues"]:
        print(f"- {blocker}")
```

### 3. Comprehensive PR Analysis
```python
# Full PR analysis with all checks
success, message, result = pr_manager(
    action="analyze",
    source_branch="feature/subfeatureB",
    target_branch="main", 
    context_branches=["feature/subfeatureA", "feature/F", "mobile/F1"],
    safety_level="strict",
    include_tests=True,
    generate_patch=True
)

# Generate detailed report
print(result["pr_analysis"]["change_complexity"])
print(result["safety_validation"]["safe_to_proceed"])
```

## 📊 Example Workflow

### Scenario: Analyzing subfeatureB before merge

```bash
# Run the demo script
python examples/pr_analysis_demo.py

# Or interactive mode
python examples/pr_analysis_demo.py interactive
```

### Expected Output:
```
📎 Clippy PR Analysis Demo!
=============================================================
Scenario: Analyzing subfeatureB changes for cross-branch impacts

🔍 Analyzing cross-branch impacts...
Source: feature/subfeatureB
Target: main
Context branches: feature/subfeatureA, feature/primaryFeatureF, mobile/primaryFeatureF1

========================================
1. GIT ANALYSIS
========================================
✅ Git analysis completed!

📊 IMPACT SUMMARY:
📊 Analysis Summary for 'feature/subfeatureB' → 'main':
   • Files changed: 8
   • Lines modified: 156
   • Overall risk: 🟡 MEDIUM
   • Potential collisions: feature/subfeatureA

🎯 BRANCH IMPACTS:
  main: 🟡 MEDIUM
    Files affected: 8
    Lines modified: 156
    Areas impacted: Core code, Configuration

  feature/subfeatureA: 🟡 MEDIUM
    Files affected: 0  
    Lines modified: 0
    Areas impacted: []

⚠️  COLLISION RISKS:
  feature/subfeatureA: 🟡 MEDIUM
    Conflicting files: 2
    Divergence point: a1b2c3d4...

💡 RECOMMENDATIONS:
  🔄 Collision risk with branch 'feature/subfeatureA'. Coordinate with that team before merging.
  📁 Large number of files changed (8). Consider splitting into smaller PRs.

========================================
2. PR MANAGEMENT VALIDATION  
========================================
✅ PR validation completed!

✅ OVERALL SAFETY: REQUIRES ATTENTION
   Score: 7.5/10.0

🔍 SAFETY CHECKS:
  ✅ branch_exists_feature/subfeatureB
  ✅ branch_exists_main
  ✅ branch_exists_feature/subfeatureA
  ✅ branch_exists_feature/primaryFeatureF
  ✅ branch_exists_mobile/primaryFeatureF1
  ✅ no_merge_conflicts
  ✅ reasonable_change_size
  ✅ has_test_coverage
  ❌ context_branch_safe

💡 RECOMMENDATIONS:
  • Potential conflicts with 1 context branches

========================================
3. DETAILED COLLISION ANALYSIS
========================================
✅ Collision analysis completed!

🟢 OVERALL COLLISION SEVERITY: LOW

  feature/subfeatureA: 🟡 MEDIUM
    Merge complexity: complex
    Conflicting files: 2
    Conflicting file list:
      - src/utils/helpers.py
      - tests/test_helpers.py
    Recommendations:
      • Review conflicting files carefully
      • Plan for potential merge conflicts

=============================================================
📎 Analysis complete! 📎
Use this information to make informed decisions about
whether to proceed with merging subfeatureB changes.
=============================================================
```

## 🔧 Integration with Existing Workflow

### In Interactive Mode:
Use the `/analyze` command to trigger PR analysis:
```
You: /analyze pr --source feature/subfeatureB --target main --context feature/subfeatureA,mobile/F1

Clippy: 📎 I'll analyze the PR impact for you! Let me check how subfeatureB changes affect main and the context branches...

[Analysis results displayed]
```

### In Document Mode:
Use the PR Analysis panel to visualize cross-branch impacts and collision risks.

### In Automated CI/CD:
```bash
# Pre-merge hook analysis
python -m clippy --oneshot "Use git_analyzer to analyze changes in $SOURCE_BRANCH against $TARGET_BRANCH with context branches $CONTEXT_BRANCHES"
```

## 🎯 Advanced Use Cases

### 1. Multi-Team Coordination
```python
# Analyze impact across multiple team branches
git_analyzer(
    base_branch="main",
    feature_branch="team-backend/new-api",
    compare_branches=[
        "team-frontend/api-consumers", 
        "team-mobile/native-app",
        "team-qa/test-suite"
    ]
)
```

### 2. Release Safety Validation
```python
# Strict validation before release
pr_manager(
    action="validate",
    source_branch="release/v2.1.0",
    target_branch="main",
    context_branches=["production/hotfixes"],
    safety_level="strict"
)
```

### 3. Feature Branch Dependencies
```python
# Check dependent feature branches
git_analyzer(
    base_branch="feature/auth-system",
    feature_branch="feature/user-profiles",
    compare_branches=["feature/social-integration"]
)
```

## 🧠 Semantic Analysis Features

The semantic analysis goes beyond line-by-line diffs:

### API Change Detection
- Identifies function/method signature changes
- Detects new endpoints or removed APIs
- Flags breaking changes

### Data Model Impact
- Recognizes database schema changes
- Identifies configuration file modifications
- Detects dependency version changes

### Cross-Language Understanding
- Works with Python, JavaScript, TypeScript, Java, C++, Go
- Language-agnostic pattern matching
- Framework-agnostic change analysis

## 📋 Best Practices

### 1. Set Safety Levels Appropriately
- **Production releases**: Use `strict` mode
- **Feature development**: Use `moderate` mode  
- **Experimental features**: Use `permissive` mode

### 2. Include All Context Branches
- Always include sibling feature branches
- Include platform-specific branches (mobile, web)
- Include integration/testing branches

### 3. Review Semantic Analysis
- Pay attention to API change warnings
- Check dependency impact scores
- Review semantic impact scoring

### 4. Use Staging for Critical Changes
- Always stage changes that affect multiple contexts
- Generate patches for backup and review
- Create backup branches before risky operations

## 🔍 Troubleshooting

### Common Issues:
1. **Branch not found**: Ensure all branches exist locally or track remote branches
2. **No git repository**: Run from within a git repository
3. **Timeout**: Large repositories may need longer analysis time
4. **Merge conflicts**: Address conflicts before analysis for best results

### Performance Tips:
- Use `analysis_depth="commits"` for quick checks
- Use `analysis_depth="full"` only when needed
- Limit `compare_branches` to essential branches
- Consider repository size when planning analysis

## 📎 Happy Analyzing!

These tools give your friend exactly what they need - comprehensive PR-level analysis that prevents breaking other contexts when making commits. The system analyzes not just the immediate changes, but their broader impact across the entire development ecosystem.

Remember: In complex multi-branch development, it's not about preventing commits - it's about making *informed* commits! 📎✨