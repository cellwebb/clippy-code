"""clippy-code - A CLI coding agent."""

from .__version__ import __version__
from .agent import ClippyAgent
from .cli import main
from .permissions import PermissionConfig, PermissionManager

__all__ = ["__version__", "ClippyAgent", "main", "PermissionConfig", "PermissionManager"]
