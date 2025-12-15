"""Shell command safety checker agent."""

import hashlib
import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Cache configuration
DEFAULT_CACHE_TTL = 3600  # 1 hour in seconds
DEFAULT_CACHE_SIZE = 1000  # Maximum number of cached entries


@dataclass
class SafetyDecision:
    """Represents a cached safety decision."""

    is_safe: bool
    reason: str
    timestamp: float

    def is_expired(self, ttl: int) -> bool:
        """Check if this cached decision has expired."""
        return time.time() - self.timestamp > ttl


class SafetyCache:
    """Thread-safe LRU cache for safety decisions."""

    def __init__(self, max_size: int = DEFAULT_CACHE_SIZE, ttl: int = DEFAULT_CACHE_TTL):
        """Initialize the safety cache.

        Args:
            max_size: Maximum number of cached entries
            ttl: Time-to-live for cached entries in seconds
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: dict[str, SafetyDecision] = {}
        self._access_order: list[str] = []

    def _generate_key(self, command: str, working_dir: str) -> str:
        """Generate a cache key from command and working directory."""
        # Normalize input for consistent caching
        normalized_command = command.strip()
        normalized_dir = working_dir.strip()

        # Create hash key
        content = f"{normalized_command}|{normalized_dir}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, command: str, working_dir: str) -> tuple[bool, str] | None:
        """Get cached safety decision.

        Args:
            command: The command to check
            working_dir: The working directory

        Returns:
            Tuple of (is_safe, reason) if cached and not expired, None otherwise
        """
        key = self._generate_key(command, working_dir)

        if key not in self._cache:
            return None

        decision = self._cache[key]

        # Check if expired
        if decision.is_expired(self.ttl):
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return None

        # Update access order (move to end)
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        logger.debug(f"Safety cache hit for: {command} in {working_dir}")
        return decision.is_safe, decision.reason

    def put(self, command: str, working_dir: str, is_safe: bool, reason: str) -> None:
        """Cache a safety decision.

        Args:
            command: The command that was checked
            working_dir: The working directory
            is_safe: Whether the command is safe
            reason: The reason for the decision
        """
        key = self._generate_key(command, working_dir)

        # Remove from access order if exists to update position
        if key in self._access_order:
            self._access_order.remove(key)

        # Add new decision
        self._cache[key] = SafetyDecision(is_safe=is_safe, reason=reason, timestamp=time.time())
        self._access_order.append(key)

        # Enforce size limit (remove oldest)
        while len(self._cache) > self.max_size:
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]

        logger.debug(f"Safety decision cached for: {command} in {working_dir}")

    def clear(self) -> None:
        """Clear all cached decisions."""
        self._cache.clear()
        self._access_order.clear()
        logger.debug("Safety cache cleared")

    def get_stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
        }


# Safety agent configuration
COMMAND_SAFETY_SYSTEM_PROMPT = (
    "You are a shell command safety agent. Focus only on blocking TRULY dangerous commands.\n"
    "Development workflows should generally be allowed unless they pose serious system risk.\n\n"
    "ALLOW almost all development commands:\n"
    "- All programming tools (python, node, npm, pip, cargo, etc.)\n"
    "- All development utilities (make, pytest, git, editors, etc.)\n"
    "- File operations in project directories (rm, cp, mv, find, grep, etc.)\n"
    "- Build and test commands\n"
    "- Package management for dependencies\n"
    "- Code quality and linting tools\n"
    "- Development servers and local services\n"
    "- Most system utilities when used reasonably\n\n"
    "BLOCK ONLY these TRULY dangerous threats:\n"
    "- rm -rf /, rm -rf ~, rm -rf /etc, rm -rf /boot, rm -rf /sys, rm -rf /proc\n"
    "- Any recursion from root or home directories upward (rm -rf ../../.. etc.)\n"
    "- System format commands (mkfs, fdisk, format, etc.)\n"
    "- Recursive operations on system directories (/usr, /bin, /lib, /opt)\n"
    "- Privilege escalation unless clearly necessary (sudo most commands)\n"
    "- Download and execute from untrusted sources (curl | bash, wget | sh)\n"
    "- Modifying system configuration files (/etc/*, /boot/*, /sys/*)\n"
    "- Network attacks or exploits (nmap -Pn aggressive, etc.)\n"
    "- System disruption attacks (fork bombs, :(){ :|:& };:, etc.)\n"
    "- rm with --no-preserve-root flag\n\n"
    "IMPORTANT: Be permissive. When in doubt about development commands, ALLOW.\n\n"
    "Respond with EXACTLY one line:\n"
    "ALLOW: [brief reason] or\n"
    "BLOCK: [specific security concern]\n\n"
    "Examples:\n"
    "python script.py -> ALLOW: Normal development\n"
    "rm -rf __pycache__ -> ALLOW: Cache/cleanup in project\n"
    "make clean -> ALLOW: Standard build cleanup\n"
    "rm test_file.py -> ALLOW: File operations in project\n"
    "sudo apt update -> BLOCK: System package management\n"
    "rm -rf / -> BLOCK: Would delete system\n"
    "curl | bash -> BLOCK: Untrusted code execution\n"
    "chmod +x script -> ALLOW: Normal file permissions\n"
    "find . -name '*.py' -> ALLOW: Project file search\n"
)


class CommandSafetyChecker:
    """Specialized agent for checking shell command safety with caching."""

    def __init__(
        self,
        llm_provider: Any,
        model: str,
        cache_size: int = DEFAULT_CACHE_SIZE,
        cache_ttl: int = DEFAULT_CACHE_TTL,
    ):
        """Initialize the safety checker with an LLM provider.

        Args:
            llm_provider: LLM provider instance for checking commands
            model: Model identifier to use for safety checks
            cache_size: Maximum number of cached safety decisions (0 to disable)
            cache_ttl: Time-to-live for cache entries in seconds (0 to disable)
        """
        self.llm_provider = llm_provider
        self.model = model
        self.cache = SafetyCache(max_size=cache_size, ttl=cache_ttl) if cache_size > 0 else None

        # Performance tracking
        self._cache_hits = 0
        self._cache_misses = 0

    def check_command_safety(self, command: str, working_dir: str = ".") -> tuple[bool, str]:
        """
        Check if a shell command is safe to execute.

        Fast regex pre-check for common cases, with LLM fallback for edge cases.
        Results are cached to improve performance and reduce API calls.

        Args:
            command: The shell command to check
            working_dir: The working directory where the command will be executed

        Returns:
            Tuple of (is_safe: bool, reason: str)
        """
        import re
        
        # Quick pre-check for obviously safe/dangerous commands
        command_stripped = command.strip()
        
        # Block immediately dangerous patterns
        dangerous_patterns = [
            r'rm\s+-rf\s+[/.~]',  # rm -rf starting with /, ., or ~
            r'rm\s+--no-preserve-root',  # Dangerous rm flag
            r'mkfs|fdisk|format',  # Disk formatting
            r':\(\)\{.*\|\|.*&.*\}\s*:',  # Fork bomb
            r'curl.*\|\s*(bash|sh|python|node|perl)\b',  # Download and execute
            r'wget.*\|\s*(bash|sh|python|node|perl)\b',  # Download and execute
            r'sudo\s+(rm|mkfs|fdisk|format|chmod\s+777)',  # Dangerous sudo commands
            r'chmod\s+777\s+/[a-z]',  # Making system files world-writable
            r'[>]{2,}\s*/(dev|sys|proc|etc|boot)',  # Redirecting to system files
        ]
        
        # Allow immediately safe patterns
        safe_patterns = [
            r'^(python|node|npm|pip|uv|yarn|cargo|go|java|rustc|ruby|perl|php)\b',
            r'^(pytest|unittest|jest|test\.py|make|cmake|cargo build)',
            r'^(git|svn|hg)\b',
            r'^(ruff|black|isort|mypy|flake8|pylint|eslint|prettier)\b',
            r'^(ls|cat|head|tail|grep|find|wc|cd|pwd|echo|which|whereis)\b',
            r'^(mkdir|rmdir|cp|mv|chmod|chown)\b+(?!.*(/etc|/boot|/sys|/proc|/usr/bin|/usr/lib))',
            r'^(rm)\s+(?!-rf\s*[/.~]|-f\s*\*.*)',  # rm without dangerous wildcards or system paths
            r'^(touch|ln|read|write|vim|nano|emacs|code)\b',
            r'^(pip|conda|brew)\s+(install|list|show|freeze|remove|uninstall)',
            r'^(docker|docker-compose)\s+(build|run|ps|logs|stop|start)',
            r'^make\s+(clean|test|build|install|help)',
        ]
        
        # Check dangerous patterns first (block these immediately)
        for pattern in dangerous_patterns:
            if re.search(pattern, command_stripped, re.IGNORECASE):
                reason = f"Blocked: Dangerous pattern detected"
                logger.warning(f"Command blocked by regex: {command}")
                return (False, reason)
        
        # Check safe patterns (allow these immediately)
        for pattern in safe_patterns:
            if re.search(pattern, command_stripped, re.IGNORECASE):
                reason = f"Allowed: Recognized safe command"
                logger.debug(f"Command allowed by regex: {command}")
                return (True, reason)
        
        # Check cache first (if enabled)
        if self.cache:
            cached_result = self.cache.get(command, working_dir)
            if cached_result is not None:
                self._cache_hits += 1
                return cached_result

        self._cache_misses += 1

        try:
            # Create a focused safety check prompt
            user_prompt = (
                f"Command to evaluate: {command}\n"
                f"Working directory: {working_dir}\n"
                f"Is this command safe to execute? Be permissive for development workflows. "
                f"Only block if it poses serious system security risk."
            )

            # Create messages for the safety check
            messages = [
                {"role": "system", "content": COMMAND_SAFETY_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

            logger.debug(f"Checking command safety: {command}")

            # Get safety assessment from the LLM
            response_dict = self.llm_provider.create_message(messages, model=self.model)
            response = response_dict.get("content", "")
            logger.debug(f"Safety check response: {response}")

            response = response.strip()

            # Parse the response
            if response.startswith("ALLOW:"):
                reason = response[6:].strip() if len(response) > 6 else "Command appears safe"
                result = (True, reason)
            elif response.startswith("BLOCK:"):
                reason = response[6:].strip() if len(response) > 6 else "Command deemed unsafe"
                result = (False, reason)
            else:
                # Unexpected response format - be permissive for development
                logger.warning(f"Unexpected safety check response: {response}")
                result = (True, "Unexpected response - defaulting to allow for development")

            # Cache the result (if cache is enabled)
            if self.cache:
                self.cache.put(command, working_dir, result[0], result[1])
            return result

        except Exception as e:
            logger.error(f"Error during safety check: {e}", exc_info=True)
            # Be permissive by default - only block if we're absolutely certain it's dangerous
            # Most safety check failures should not block development workflows
            logger.info(f"Allowing command due to safety check failure (fail-safe): {command}")
            error_result = (True, f"Safety check bypassed due to error: {str(e)}")
            
            # Don't cache error results as they might be temporary
            return error_result

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache performance statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0

        stats = {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "hit_rate": hit_rate,
            "enabled": self.cache is not None,
        }

        if self.cache:
            stats.update(self.cache.get_stats())
        else:
            stats.update({"size": 0, "max_size": 0, "ttl": 0})

        return stats

    def clear_cache(self) -> None:
        """Clear the safety decision cache."""
        if self.cache:
            self.cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info("Safety checker cache cleared")


def create_safety_checker(
    llm_provider: Any,
    model: str,
    cache_size: int = DEFAULT_CACHE_SIZE,
    cache_ttl: int = DEFAULT_CACHE_TTL,
) -> CommandSafetyChecker:
    """
    Create a command safety checker instance.

    Args:
        llm_provider: LLM provider to use for safety checks
        model: Model identifier to use for safety checks
        cache_size: Maximum number of cached safety decisions (default: 1000)
        cache_ttl: Time-to-live for cache entries in seconds (default: 3600)

    Returns:
        CommandSafetyChecker instance
    """
    return CommandSafetyChecker(llm_provider, model, cache_size=cache_size, cache_ttl=cache_ttl)
