"""LLM integration for enhanced git and PR analysis."""

import json
import logging
import os
from typing import Any

from .models import get_default_model_config, get_model_config
from .providers import LLMProvider

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """LLM-powered analysis for git and PR insights."""

    def __init__(self, model_name: str | None = None):
        """
        Initialize LLM analyzer with specified model.

        Args:
            model_name: Model to use, defaults to configured default
        """
        self.model_name = model_name
        self.provider: LLMProvider | None = None
        self._init_provider()

    def _init_provider(self) -> bool:
        """Initialize LLM provider from clippy's model configuration."""
        try:
            if self.model_name:
                model_config, provider_config = get_model_config(self.model_name)
            else:
                model_config, provider_config = get_default_model_config()

            if not model_config or not provider_config:
                logger.warning("No LLM model configuration found")
                return False

            # Import here to avoid circular imports
            from .providers import LLMProvider

            api_key = os.getenv(provider_config.api_key_env)
            if not api_key:
                logger.warning(f"API key not found: {provider_config.api_key_env}")
                return False

            self.provider = LLMProvider(api_key=api_key, base_url=provider_config.base_url)
            self.model_config = model_config

            logger.info(f"LLM analyzer initialized with model: {model_config.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            return False

    def is_available(self) -> bool:
        """Check if LLM analyzer is available and configured."""
        return self.provider is not None

    def analyze_code_changes(
        self, diff_content: str, context_branches: list[str]
    ) -> dict[str, Any]:
        """
        Analyze code changes with LLM for deeper insights.

        Args:
            diff_content: Git diff content to analyze
            context_branches: List of context branches for coordination analysis

        Returns:
            LLM analysis results
        """
        if not self.is_available():
            return {"error": "LLM not available"}

        system_prompt = """You are an expert software engineer analyzing git changes for
potential impacts and risks.

Analyze the provided git diff and provide insights on:
1. Breaking changes (API modifications, removed functions, signature changes)
2. Business logic impact (core functionality vs cosmetic changes)
3. Coordination requirements (which teams/contexts need to be notified)
4. Risk assessment (technical complexity and potential for issues)
5. Dependencies affected (both direct and indirect)

Respond in JSON format with these exact keys:
{
  "breaking_changes": [{"file": "path", "description": "what changed",
                        "severity": "high|medium|low"}],
  "business_impact": {"level": "high|medium|low",
                      "description": "impact explanation"},
  "coordination_required": [{"team": "team_name", "reason": "why they need to know",
                             "priority": "high|medium|low"}],
  "risk_assessment": {"overall": "high|medium|low",
                      "technical_complexity": "high|medium|low",
                      "reasoning": "explanation"},
  "dependencies_affected": [{"type": "api|config|database|infrastructure",
                             "details": "what's affected"}],
  "recommendations": ["string recommendations"]
}

Be specific and technical in your analysis."""

        context_info = (
            f"Context branches: {', '.join(context_branches)}"
            if context_branches
            else "No additional context branches"
        )
        user_message = f"""Analyze this git diff:

{context_info}

Diff content:
{diff_content[:8000]}  # Limit to prevent token overflow

Focus on practical impacts and coordination needs."""

        try:
            if not self.provider:
                return {"error": "LLM provider not initialized"}

            response = self.provider.create_message(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                model=self.model_config.model_id,
            )

            # Parse JSON response
            content = response.get("content", "")
            if content:
                # Try to extract JSON from response
                content = content.strip()
                if content.startswith("{") and content.endswith("}"):
                    result = json.loads(content)
                    return (
                        dict[str, Any](result)
                        if isinstance(result, dict)
                        else {"error": "Invalid response format"}
                    )
                else:
                    # Look for JSON in the response
                    import re

                    json_match = re.search(r"\{.*\}", content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        return (
                            dict[str, Any](result)
                            if isinstance(result, dict)
                            else {"error": "Invalid response format"}
                        )

            return {"error": "Failed to parse LLM response"}

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            return {"error": str(e)}

    def analyze_commit_quality(self, commit_messages: list[str]) -> dict[str, Any]:
        """
        Analyze commit message quality and technical context.

        Args:
            commit_messages: List of commit messages to analyze

        Returns:
            Quality analysis results
        """
        if not self.is_available():
            return {"error": "LLM not available"}

        system_prompt = """You are an expert code reviewer evaluating commit message quality.

Analyze these commit messages and evaluate:
1. Clarity and specificity
2. Technical accuracy
3. Impact description
4. Reference to issues/tickets (if applicable)
5. Overall commit hygiene

Respond in JSON format:
{
  "overall_quality": "excellent|good|fair|poor",
  "score": 0.0-10.0,
  "issues": ["specific problems found"],
  "strengths": ["good aspects found"],
  "recommendations": ["improvement suggestions"],
  "technical_context": "assessment of the technical nature of changes"
}

Be constructive and specific in your feedback."""

        commits_text = "\n".join([f"- {msg}" for msg in commit_messages[:10]])
        user_message = f"""Analyze these commit messages:

{commits_text}

Provide honest assessment of their quality and usefulness."""

        try:
            if not self.provider:
                return {"error": "LLM provider not initialized"}

            response = self.provider.create_message(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                model=self.model_config.model_id,
            )

            content = response.get("content", "")
            if content:
                content = content.strip()
                if content.startswith("{") and content.endswith("}"):
                    result = json.loads(content)
                    return (
                        dict[str, Any](result)
                        if isinstance(result, dict)
                        else {"error": "Invalid response format"}
                    )
                else:
                    import re

                    json_match = re.search(r"\{.*\}", content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        return (
                            dict[str, Any](result)
                            if isinstance(result, dict)
                            else {"error": "Invalid response format"}
                        )

            return {"error": "Failed to parse LLM response"}

        except Exception as e:
            logger.error(f"Commit quality analysis failed: {e}")
            return {"error": str(e)}

    def assess_business_impact(
        self, changes_summary: dict[str, Any], project_context: str
    ) -> dict[str, Any]:
        """
        Assess business impact of changes based on project context.

        Args:
            changes_summary: Summary of technical changes
            project_context: Project context (e.g., "payment processing",
                             "user authentication")

        Returns:
            Business impact assessment
        """
        if not self.is_available():
            return {"error": "LLM not available"}

        system_prompt = """You are a technical product manager assessing business impact
of code changes.

Given the technical changes summary and project context, assess:
1. Business risk level
2. Customer impact
3. Revenue impact potential
4. Compliance/regulatory implications
5. Rollback complexity
6. Testing requirements

Respond in JSON format:
{
  "business_risk": "high|medium|low",
  "customer_impact": {"areas": ["affected areas"],
                      "severity": "high|medium|low"},
  "revenue_impact": {"potential": "positive|neutral|negative",
                     "reasoning": "explanation"},
  "compliance_risk": {"level": "high|medium|low",
                      "areas": ["specific concerns"]},
  "rollback_complexity": "high|medium|low",
  "testing_approach": "recommended testing strategy",
  "stakeholder_notifications": [{"role": "role to notify",
                                 "urgency": "immediate|soon|routine",
                                 "reason": "why"}]
}

Consider the business context in your assessment."""

        changes_json = json.dumps(changes_summary, indent=2)
        user_message = f"""Assess business impact for these changes:

Project Context: {project_context}

Technical Changes Summary:
{changes_json}

Focus on practical business implications and stakeholder communication."""

        try:
            if not self.provider:
                return {"error": "LLM provider not initialized"}

            response = self.provider.create_message(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                model=self.model_config.model_id,
            )

            content = response.get("content", "")
            if content:
                content = content.strip()
                if content.startswith("{") and content.endswith("}"):
                    result = json.loads(content)
                    return (
                        dict[str, Any](result)
                        if isinstance(result, dict)
                        else {"error": "Invalid response format"}
                    )
                else:
                    import re

                    json_match = re.search(r"\{.*\}", content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        return (
                            dict[str, Any](result)
                            if isinstance(result, dict)
                            else {"error": "Invalid response format"}
                        )

            return {"error": "Failed to parse LLM response"}

        except Exception as e:
            logger.error(f"Business impact analysis failed: {e}")
            return {"error": str(e)}

    def generate_coordination_plan(
        self, collision_analysis: dict[str, Any], changes_impact: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Generate coordination plan for handling collisions and impacts.

        Args:
            collision_analysis: Results from collision detection
            changes_impact: Analysis of changes impact

        Returns:
            Coordination plan with specific actions
        """
        if not self.is_available():
            return {"error": "LLM not available"}

        system_prompt = """You are a technical project manager creating a coordination
plan for multi-branch development.

Given collision analysis and impact analysis, create a practical coordination plan:
1. Required communications
2. Dependency management
3. Testing coordination
4. Rollback contingencies
5. Timeline considerations

Respond in JSON format:
{
  "coordination_required": [{"team": "team_name",
                             "action": "specific action needed",
                             "urgency": "immediate|before_merge|after_merge",
                             "contact_method": "slack|email|meeting"}],
  "testing_strategy": {"parallel_testing": ["teams that should test in parallel"],
                       "integration_checkpoints": ["key integration points"]},
  "rollback_plan": {"triggers": ["rollback conditions"],
                    "procedure": "step-by-step rollback",
                    "coordination": ["who needs to be involved"]},
  "communication_plan": {"pre_merge": ["communications needed before merge"],
                         "post_merge": ["communications needed after merge"]},
  "timeline_impact": {"estimated_delay": "hours/days",
                      "blocking_factors": ["what might delay the merge"]},
  "risk_mitigation": ["risk mitigation strategies"]
}

Focus on practical, actionable coordination guidance."""

        collision_json = json.dumps(collision_analysis, indent=2)
        impact_json = json.dumps(changes_impact, indent=2)
        user_message = f"""Create coordination plan for:

Collision Analysis:
{collision_json}

Changes Impact:
{impact_json}

Provide specific, actionable coordination steps."""

        try:
            if not self.provider:
                return {"error": "LLM provider not initialized"}

            response = self.provider.create_message(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                model=self.model_config.model_id,
            )

            content = response.get("content", "")
            if content:
                content = content.strip()
                if content.startswith("{") and content.endswith("}"):
                    result = json.loads(content)
                    return (
                        dict[str, Any](result)
                        if isinstance(result, dict)
                        else {"error": "Invalid response format"}
                    )
                else:
                    import re

                    json_match = re.search(r"\{.*\}", content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        return (
                            dict[str, Any](result)
                            if isinstance(result, dict)
                            else {"error": "Invalid response format"}
                        )

            return {"error": "Failed to parse LLM response"}

        except Exception as e:
            logger.error(f"Coordination plan generation failed: {e}")
            return {"error": str(e)}


def get_llm_analyzer(model_name: str | None = None) -> LLMAnalyzer:
    """
    Get LLM analyzer instance with optional model specification.

    Args:
        model_name: Specific model to use, uses default if None

    Returns:
        LLM analyzer instance
    """
    return LLMAnalyzer(model_name)


def is_llm_available(model_name: str | None = None) -> bool:
    """
    Check if LLM analysis is available.

    Args:
        model_name: Specific model to check

    Returns:
        True if LLM is configured and available
    """
    analyzer = get_llm_analyzer(model_name)
    return analyzer.is_available()
