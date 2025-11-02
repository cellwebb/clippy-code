"""Project analysis tool implementation."""

import ast
import json
import re
from pathlib import Path
from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "analyze_project",
        "description": (
            "Comprehensive project analysis including security vulnerability scanning, "
            "dependency analysis, code quality metrics, license detection, and TODO tracking. "
            "Supports multiple programming languages and package managers. "
            "Identifies potential issues and provides actionable insights."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to the project directory to analyze",
                },
                "include_tests": {
                    "type": "boolean",
                    "description": "Include test files in analysis",
                    "default": True,
                },
                "deep_scan": {
                    "type": "boolean",
                    "description": "Perform deep analysis (slower but more comprehensive)",
                    "default": False,
                },
                "security_focus": {
                    "type": "boolean",
                    "description": "Focus on security vulnerabilities and best practices",
                    "default": True,
                },
                "max_file_size": {
                    "type": "integer",
                    "description": "Maximum file size to analyze in bytes",
                    "default": 1048576,  # 1MB
                },
            },
            "required": ["project_path"],
        },
    },
}


def analyze_project(
    project_path: str,
    include_tests: bool = True,
    deep_scan: bool = False,
    security_focus: bool = True,
    max_file_size: int = 1048576,
) -> tuple[bool, str, Any]:
    """
    Perform comprehensive project analysis.

    Args:
        project_path: Path to project directory
        include_tests: Include test files in analysis
        deep_scan: Perform detailed analysis
        security_focus: Focus on security aspects
        max_file_size: Maximum file size to process

    Returns:
        Tuple of (success: bool, message: str, result: Any)
    """
    try:
        path = Path(project_path)

        if not path.exists():
            return False, f"Project path does not exist: {project_path}", None

        if not path.is_dir():
            return False, f"Project path must be a directory: {project_path}", None

        analysis = ProjectAnalyzer(path, include_tests, deep_scan, security_focus, max_file_size)
        results: dict[str, Any] = analysis.analyze()

        summary = generate_analysis_summary(results)
        message = (
            f"Project analysis complete. Found {summary['issues_count']} potential issues "
            f"and {summary['recommendations_count']} recommendations."
        )

        return True, message, results

    except Exception as e:
        return False, f"Error during project analysis: {str(e)}", None


class ProjectAnalyzer:
    """Comprehensive project analyzer."""

    def __init__(
        self,
        project_path: Path,
        include_tests: bool,
        deep_scan: bool,
        security_focus: bool,
        max_file_size: int,
    ):
        self.project_path = project_path
        self.include_tests = include_tests
        self.deep_scan = deep_scan
        self.security_focus = security_focus
        self.max_file_size = max_file_size

        # Analysis results
        self.results: dict[str, Any] = {
            "project_info": {},
            "dependencies": {},
            "security_issues": [],
            "code_quality": {},
            "licenses": [],
            "todos": [],
            "recommendations": [],
        }

    def analyze(self) -> dict[str, Any]:
        """Perform complete project analysis."""
        self._analyze_project_info()
        self._analyze_dependencies()
        self._analyze_security()
        self._analyze_code_quality()
        self._analyze_licenses()
        self._find_todos()
        self._generate_recommendations()

        return self.results

    def _analyze_project_info(self) -> None:
        """Analyze basic project information."""
        info: dict[str, Any] = {
            "path": str(self.project_path.absolute()),
            "name": self.project_path.name,
            "total_files": 0,
            "total_lines": 0,
            "programming_languages": {},
            "file_extensions": set(),
            "has_git": (self.project_path / ".git").exists(),
            "has_readme": False,
            "has_tests": False,
        }

        # Scan project structure
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file() and file_path.stat().st_size <= self.max_file_size:
                info["total_files"] += 1

                # Check for README
                if file_path.name.lower().startswith("readme"):
                    info["has_readme"] = True

                # Check for test files
                if not info["has_tests"] and (
                    "test" in file_path.name.lower()
                    or file_path.parent.name.lower() == "tests"
                    or file_path.parent.name.lower() == "test"
                ):
                    info["has_tests"] = True

                # Analyze file extensions for language detection
                if "." in file_path.name:
                    ext = file_path.suffix.lower()
                    info["file_extensions"].add(ext)

                    # Language detection
                    language_map = {
                        ".py": "Python",
                        ".js": "JavaScript",
                        ".ts": "TypeScript",
                        ".java": "Java",
                        ".cpp": "C++",
                        ".c": "C",
                        ".go": "Go",
                        ".rs": "Rust",
                        ".rb": "Ruby",
                        ".php": "PHP",
                        ".cs": "C#",
                        ".swift": "Swift",
                    }

                    if ext in language_map:
                        lang = language_map[ext]
                        info["programming_languages"][lang] = (
                            info["programming_languages"].get(lang, 0) + 1
                        )

                # Count lines (simplified)
                try:
                    if ext in [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs"]:
                        with open(file_path, encoding="utf-8") as f:
                            lines = len(f.readlines())
                            info["total_lines"] += lines
                except Exception:
                    pass

        info["file_extensions"] = list(info["file_extensions"])
        self.results["project_info"] = info

    def _analyze_dependencies(self) -> None:
        """Analyze project dependencies."""
        deps: dict[str, Any] = {
            "package_managers": [],
            "dependencies": {},
            "dev_dependencies": {},
            "security_issues": [],
        }

        # Check for different package managers
        package_files = {
            "requirements.txt": "pip",
            "pyproject.toml": "poetry/uv",
            "setup.py": "setuptools",
            "package.json": "npm",
            "yarn.lock": "yarn",
            "Cargo.toml": "cargo",
            "go.mod": "go",
            "composer.json": "composer",
            "Pipfile": "pipenv",
        }

        for file_name, manager in package_files.items():
            file_path = self.project_path / file_name
            if file_path.exists():
                deps["package_managers"].append(manager)
                self._parse_dependency_file(file_path, manager, deps)

        # Check for known vulnerable dependencies
        if self.security_focus:
            self._check_vulnerable_dependencies(deps)

        self.results["dependencies"] = deps

    def _parse_dependency_file(self, file_path: Path, manager: str, deps: dict[str, Any]) -> None:
        """Parse dependency files based on package manager."""
        try:
            if manager == "pip" and file_path.name == "requirements.txt":
                self._parse_requirements_txt(file_path, deps)
            elif manager == "npm" and file_path.name == "package.json":
                self._parse_package_json(file_path, deps)
            elif manager in ["poetry/uv"] and file_path.name == "pyproject.toml":
                self._parse_pyproject_toml(file_path, deps)
            elif manager == "cargo" and file_path.name == "Cargo.toml":
                self._parse_cargo_toml(file_path, deps)

        except Exception as e:
            deps["security_issues"].append(f"Error parsing {file_path}: {str(e)}")

    def _parse_requirements_txt(self, file_path: Path, deps: dict[str, Any]) -> None:
        """Parse requirements.txt file."""
        try:
            with open(file_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Extract package name (before version specifiers)
                        package = re.split(r"[<>=!]", line)[0].strip()
                        if package:
                            deps["dependencies"][package] = line
        except Exception as e:
            deps["security_issues"].append(f"Error reading requirements.txt: {str(e)}")

    def _parse_package_json(self, file_path: Path, deps: dict[str, Any]) -> None:
        """Parse package.json file."""
        try:
            with open(file_path) as f:
                data = json.load(f)

                deps["dependencies"] = data.get("dependencies", {})
                deps["dev_dependencies"] = data.get("devDependencies", {})

        except json.JSONDecodeError:
            deps["security_issues"].append(f"Invalid JSON in {file_path}")
        except Exception as e:
            deps["security_issues"].append(f"Error reading package.json: {str(e)}")

    def _parse_pyproject_toml(self, file_path: Path, deps: dict[str, Any]) -> None:
        """Parse pyproject.toml file."""
        try:
            with open(file_path) as f:
                content = f.read()

            # Simple TOML parsing (basic)
            dependencies_match = re.search(r"dependencies\s*=\s*\[(.*?)\]", content, re.DOTALL)
            if dependencies_match:
                deps_str = dependencies_match.group(1)
                for line in deps_str.split("\n"):
                    line = line.strip().strip('"').strip("'")
                    if line and not line.startswith("#"):
                        package = re.split(r"[<>=!]", line)[0].strip()
                        if package:
                            deps["dependencies"][package] = line

        except Exception as e:
            deps["security_issues"].append(f"Error parsing TOML in {file_path}: {str(e)}")

    def _parse_cargo_toml(self, file_path: Path, deps: dict[str, Any]) -> None:
        """Parse Cargo.toml file."""
        try:
            with open(file_path) as f:
                content = f.read()

            # Simple TOML parsing for Cargo
            dependencies_section = re.search(r"\[dependencies\](.*?)(?:\[|\Z)", content, re.DOTALL)
            if dependencies_section:
                deps_content = dependencies_section.group(1)
                for line in deps_content.split("\n"):
                    if "=" in line and not line.strip().startswith("#"):
                        package_part = line.split("=")[0].strip()
                        package = package_part.strip('"').strip("'")
                        if package:
                            deps["dependencies"][package] = line.strip()

        except Exception as e:
            deps["security_issues"].append(f"Error parsing Cargo.toml: {str(e)}")

    def _analyze_security(self) -> None:
        """Analyze security vulnerabilities."""
        if not self.security_focus:
            return

        security_issues: list[dict[str, Any]] = []

        # Common security patterns to check for
        security_patterns = {
            r"password\s*=\s*[\"'].+?[\"']": "Hardcoded password detected",
            r"api[_-]?key\s*=\s*[\"'].+?[\"']": "Hardcoded API key detected",
            r"secret[_-]?key\s*=\s*[\"'].+?[\"']": "Hardcoded secret key detected",
            r"token\s*=\s*[\"'].+?[\"']": "Hardcoded token detected",
            r"eval\s*\(": "Use of eval() function detected",
            r"exec\s*\(": "Use of exec() function detected",
            r"shell\s*=True": "shell=True detected (potential command injection)",
            r"debug\s*=\s*True": "Debug mode enabled in production",
            r"allow_all_origins\s*=\s*True": "CORS allows all origins",
            r"import\s+pickle": "Pickle import detected (potential security risk)",
            r"subprocess\.call.*shell=True": "subprocess with shell=True detected",
        }

        # Scan for security issues
        for file_path in self.project_path.rglob("*"):
            if file_path.is_file() and file_path.stat().st_size <= self.max_file_size:
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()

                    for pattern, description in security_patterns.items():
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[: match.start()].count("\n") + 1
                            security_issues.append(
                                {
                                    "file": str(file_path.relative_to(self.project_path)),
                                    "line": line_num,
                                    "issue": description,
                                    "snippet": (
                                        match.group()[:50] + "..."
                                        if len(match.group()) > 50
                                        else match.group()
                                    ),
                                }
                            )

                except UnicodeDecodeError:
                    continue
                except Exception:
                    continue

        self.results["security_issues"] = security_issues

    def _analyze_code_quality(self) -> None:
        """Analyze code quality metrics."""
        quality: dict[str, Any] = {
            "python_issues": [],
            "javascript_issues": [],
            "general_issues": [],
            "complexity_indicators": {},
        }

        # Analyze Python files
        for file_path in self.project_path.rglob("*.py"):
            if file_path.is_file() and file_path.stat().st_size <= self.max_file_size:
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read()

                    # Parse Python AST for quality analysis
                    try:
                        tree = ast.parse(content)
                        self._analyze_python_ast(tree, file_path, quality)
                    except SyntaxError as e:
                        quality["python_issues"].append(
                            {
                                "file": str(file_path.relative_to(self.project_path)),
                                "issue": f"Syntax error: {str(e)}",
                                "severity": "error",
                            }
                        )

                    # Check for common Python issues
                    self._check_python_patterns(content, file_path, quality)

                except Exception:
                    continue

        self.results["code_quality"] = quality

    def _analyze_python_ast(self, tree: ast.AST, file_path: Path, quality: dict[str, Any]) -> None:
        """Analyze Python AST for quality issues."""
        issues: list[dict[str, Any]] = []

        # Check function complexity
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count statements in function
                statements = len(list(ast.walk(node)))
                if statements > 50:
                    issues.append(
                        {
                            "file": str(file_path.relative_to(self.project_path)),
                            "function": node.name,
                            "issue": (
                                f"Function '{node.name}' is too complex ({statements} statements)"
                            ),
                            "type": "complexity",
                            "severity": "warning",
                        }
                    )

                # Check function length
                if hasattr(node, "end_lineno") and node.lineno and node.end_lineno:
                    lines = node.end_lineno - node.lineno + 1
                    if lines > 30:
                        issues.append(
                            {
                                "file": str(file_path.relative_to(self.project_path)),
                                "function": node.name,
                                "issue": f"Function '{node.name}' is too long ({lines} lines)",
                                "type": "length",
                                "severity": "warning",
                            }
                        )

        quality["python_issues"].extend(issues)

    def _check_python_patterns(
        self, content: str, file_path: Path, quality: dict[str, Any]
    ) -> None:
        """Check for common Python code patterns."""
        patterns = {
            r"# TODO": "TODO comment found",
            r"# FIXME": "FIXME comment found",
            r"# HACK": "HACK comment found",
            r"import \*": "Wildcard import detected",
            r"except:$": "Bare except clause detected",
            r"assert\s+.*\s*in\s*production": "Assert in potential production code",
        }

        for pattern, description in patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1
                quality["python_issues"].append(
                    {
                        "file": str(file_path.relative_to(self.project_path)),
                        "line": line_num,
                        "issue": description,
                        "severity": "info",
                    }
                )

    def _analyze_licenses(self) -> None:
        """Analyze project licenses."""
        licenses: list[dict[str, Any]] = []

        # Look for license files
        license_files = ["LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING"]

        for license_file in license_files:
            file_path = self.project_path / license_file
            if file_path.exists():
                try:
                    with open(file_path, encoding="utf-8") as f:
                        content = f.read().lower()

                    # Detect license type
                    license_patterns = {
                        "mit": "MIT License",
                        "apache": "Apache License",
                        "gpl": "GPL License",
                        "bsd": "BSD License",
                        "isc": "ISC License",
                    }

                    for pattern, license_name in license_patterns.items():
                        if pattern in content:
                            licenses.append(
                                {
                                    "file": license_file,
                                    "license": license_name,
                                    "detected_from": "file_content",
                                }
                            )
                            break

                except Exception:
                    continue

        # Check package.json for license
        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    if "license" in data:
                        licenses.append(
                            {
                                "file": "package.json",
                                "license": data["license"],
                                "detected_from": "package_metadata",
                            }
                        )
            except Exception:
                pass

        self.results["licenses"] = licenses

    def _find_todos(self) -> None:
        """Find TODO, FIXME, and similar comments."""
        todos: list[dict[str, Any]] = []

        todo_patterns = [
            r"# TODO:?\s*(.+)",
            r"# FIXME:?\s*(.+)",
            r"# HACK:?\s*(.+)",
            r"# NOTE:?\s*(.+)",
            r"// TODO:?\s*(.+)",
            r"// FIXME:?\s*(.+)",
            r"// HACK:?\s*(.+)",
            r"// NOTE:?\s*(.+)",
        ]

        for file_path in self.project_path.rglob("*"):
            if file_path.is_file() and file_path.stat().st_size <= self.max_file_size:
                try:
                    with open(file_path, encoding="utf-8") as f:
                        lines = f.readlines()

                    for line_num, line in enumerate(lines, 1):
                        for pattern in todo_patterns:
                            match = re.search(pattern, line, re.IGNORECASE)
                            if match:
                                todos.append(
                                    {
                                        "file": str(file_path.relative_to(self.project_path)),
                                        "line": line_num,
                                        "type": (
                                            match.group()
                                            .split(":")[0]
                                            .replace("#", "")
                                            .replace("//", "")
                                            .strip()
                                        ),
                                        "text": (
                                            match.group(1).strip()
                                            if len(match.groups()) > 0
                                            else ""
                                        ),
                                        "line_text": line.strip(),
                                    }
                                )
                                break

                except UnicodeDecodeError:
                    continue
                except Exception:
                    continue

        self.results["todos"] = todos

    def _generate_recommendations(self) -> None:
        """Generate actionable recommendations."""
        recommendations: list[dict[str, Any]] = []

        # Security recommendations
        if list(self.results["security_issues"]):
            recommendations.append(
                {
                    "category": "security",
                    "priority": "high",
                    "title": "Address security vulnerabilities",
                    "description": (
                        f"Found {len(self.results['security_issues'])} potential security issues"
                    ),
                    "action": (
                        "Review and fix hardcoded secrets, use environment variables, "
                        "and validate inputs"
                    ),
                }
            )

        # Dependency recommendations
        deps = dict(self.results["dependencies"])
        if list(deps.get("security_issues", [])):
            recommendations.append(
                {
                    "category": "dependencies",
                    "priority": "medium",
                    "title": "Fix dependency parsing issues",
                    "description": "Some dependency files could not be parsed",
                    "action": "Check syntax in dependency files and ensure they are valid",
                }
            )

        if len(list(deps["dependencies"])) > 50:
            recommendations.append(
                {
                    "category": "dependencies",
                    "priority": "low",
                    "title": "Consider reducing dependencies",
                    "description": f"Project has {len(deps['dependencies'])} dependencies",
                    "action": "Review dependencies and remove unused or redundant packages",
                }
            )

        # Code quality recommendations
        code_quality = dict(self.results["code_quality"])
        python_issues = list(code_quality.get("python_issues", []))
        error_count = sum(1 for issue in python_issues if issue.get("severity") == "error")
        warning_count = sum(1 for issue in python_issues if issue.get("severity") == "warning")

        if error_count > 0:
            recommendations.append(
                {
                    "category": "code_quality",
                    "priority": "high",
                    "title": "Fix syntax errors",
                    "description": f"Found {error_count} syntax errors",
                    "action": "Fix syntax errors before proceeding with development",
                }
            )

        if warning_count > 5:
            recommendations.append(
                {
                    "category": "code_quality",
                    "priority": "medium",
                    "title": "Improve code quality",
                    "description": f"Found {warning_count} quality warnings",
                    "action": "Refactor complex functions and reduce code duplication",
                }
            )

        # TODO recommendations
        if self.results["todos"]:
            recommendations.append(
                {
                    "category": "maintenance",
                    "priority": "low",
                    "title": "Address TODO items",
                    "description": f"Found {len(self.results['todos'])} TODO/FIXME items",
                    "action": "Review and complete outstanding TODO items",
                }
            )

        # Documentation recommendations
        project_info = self.results["project_info"]
        if not project_info.get("has_readme"):
            recommendations.append(
                {
                    "category": "documentation",
                    "priority": "medium",
                    "title": "Add README documentation",
                    "description": "No README file found",
                    "action": (
                        "Create a comprehensive README with project description, setup, and usage"
                    ),
                }
            )

        if not project_info.get("has_tests"):
            recommendations.append(
                {
                    "category": "testing",
                    "priority": "medium",
                    "title": "Add test coverage",
                    "description": "No test files detected",
                    "action": "Implement unit tests and integration tests",
                }
            )

        self.results["recommendations"] = recommendations

    def _check_vulnerable_dependencies(self, deps: dict[str, Any]) -> None:
        """Check for known vulnerable dependencies (basic implementation)."""
        # This is a simplified version - in practice, you would use a vulnerability database
        vulnerable_packages = ["requests<2.20.0", "urllib3<1.24.2", "pillow<6.2.0", "pyyaml<5.1"]

        for vuln_spec in vulnerable_packages:
            package_name = vuln_spec.split("<")[0]
            if package_name in deps["dependencies"]:
                deps["security_issues"].append(
                    f"Vulnerable dependency detected: {package_name}. "
                    "Please update to a secure version."
                )


def generate_analysis_summary(results: dict[str, Any]) -> dict[str, Any]:
    """Generate a summary of analysis results."""
    return {
        "issues_count": len(results.get("security_issues", []))
        + len(results.get("code_quality", {}).get("python_issues", [])),
        "recommendations_count": len(results.get("recommendations", [])),
        "todos_count": len(list(results.get("todos", []))),
        "dependencies_count": len(
            list(results.get("dependencies", {}).get("dependencies", {}).keys())
        ),
        "files_analyzed": int(results.get("project_info", {}).get("total_files", 0)),
        "license_detected": bool(list(results.get("licenses", []))),
        "high_priority_issues": len(
            [r for r in results.get("recommendations", []) if r.get("priority") == "high"]
        ),
    }
