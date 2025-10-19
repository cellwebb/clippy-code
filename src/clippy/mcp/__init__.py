"""MCP (Model Context Protocol) integration for code-with-clippy."""

from .config import Config, load_config
from .manager import Manager

__all__ = ["Manager", "Config", "load_config"]
